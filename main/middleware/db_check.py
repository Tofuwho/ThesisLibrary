"""
db_check.py — Database availability middleware.

Catches OperationalError exceptions raised anywhere in the request/response
cycle and returns a user-friendly 503 page instead of Django's yellow crash
screen or an indefinite load spinner.
"""

from django.db import OperationalError
from django.db.utils import OperationalError as DBOperationalError
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist


_DB_ERROR_CODES = {
    2002,   # Can't connect to server (MySQL not running)
    2003,   # Can't connect to MySQL server
    2006,   # MySQL server has gone away
    2013,   # Lost connection during query
    1040,   # Too many connections
}


def _is_db_down_error(exc: Exception) -> bool:
    """Return True if the exception indicates the database is unreachable."""
    if not isinstance(exc, (OperationalError, DBOperationalError)):
        return False
    args = getattr(exc, 'args', ())
    if args:
        code = args[0] if isinstance(args[0], int) else None
        if code in _DB_ERROR_CODES:
            return True
        # Also catch generic "Can't connect" messages (sqlite, etc.)
        msg = str(args[0]).lower()
        if any(k in msg for k in ("can't connect", "connection refused",
                                   "server has gone away", "no such table",
                                   "unable to open database")):
            return True
    return True  # Any unrecognised OperationalError is still surfaced as DB issue


class DatabaseAvailabilityMiddleware:
    """
    Intercepts database OperationalErrors and returns a 503 maintenance page
    with clear instructions on how to start MySQL via XAMPP.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except (OperationalError, DBOperationalError) as exc:
            if _is_db_down_error(exc):
                return self._render_db_down(request, exc)
            raise
        return response

    def process_exception(self, request, exception):
        """Also catches exceptions thrown inside views."""
        if isinstance(exception, (OperationalError, DBOperationalError)):
            if _is_db_down_error(exception):
                return self._render_db_down(request, exception)
        return None

    @staticmethod
    def _render_db_down(request, exc):
        try:
            html = render_to_string('main/db_down.html', {
                'error_detail': str(exc),
                'request': request,
            }, request=request)
        except TemplateDoesNotExist:
            # Absolute fallback — plain HTML, zero dependencies
            html = (
                "<h1 style='font-family:sans-serif;text-align:center;margin-top:10vh'>"
                "Database Unavailable</h1>"
                "<p style='text-align:center;color:#555'>"
                "Please start MySQL in XAMPP Control Panel and refresh.</p>"
            )
        return HttpResponse(html, status=503, content_type='text/html')
