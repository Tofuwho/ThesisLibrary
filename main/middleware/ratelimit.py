from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.general_limit = getattr(settings, 'RATELIMIT_GENERAL_LIMIT', 100)
        self.general_period = getattr(settings, 'RATELIMIT_GENERAL_PERIOD', 60)
        self.login_limit = getattr(settings, 'RATELIMIT_LOGIN_LIMIT', 5)
        self.login_period = getattr(settings, 'RATELIMIT_LOGIN_PERIOD', 900)  # 15 minutes

    def __call__(self, request):
        ip = self.get_client_ip(request)
        
        # 1. General Rate Limit for ALL endpoints
        if not self.is_allowed(f"rl:gen:{ip}", self.general_limit, self.general_period):
            logger.warning(f"General rate limit exceeded by IP: {ip}")
            return HttpResponse("Too many requests. Please slow down.", status=429)

        # 2. Login specific rate limit (POST to /auth/login/ or /admin/login/)
        # Normalize path by removing trailing slash for comparison
        normalized_path = request.path.rstrip('/')
        if (normalized_path == '/auth/login' or normalized_path == '/admin/login') and request.method == 'POST':
            if not self.is_allowed(f"rl:login:{ip}", self.login_limit, self.login_period):
                logger.warning(f"Login rate limit exceeded by IP: {ip}")
                if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                    return JsonResponse({
                        'success': False, 
                        'error': f'Too many login attempts. Please try again in {self.login_period // 60} minutes.'
                    }, status=429)
                return HttpResponse("Too many login attempts. Please try again later.", status=429)

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_allowed(self, key, limit, period):
        try:
            # Use cache.add to initialize the key if it doesn't exist
            # This is more atomic than get/set
            if cache.add(key, 1, period):
                return True
            
            # If key already exists, increment it
            # Note: incr might fail if key expired between add and incr
            try:
                new_count = cache.incr(key)
            except ValueError:
                # Key expired, re-add
                cache.set(key, 1, period)
                return True

            if new_count > limit:
                return False
            return True
        except Exception as e:
            # Fallback to allow request if cache is down
            logger.error(f"Rate limiting cache error: {e}")
            return True
