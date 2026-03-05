from django.contrib.auth import get_user_model
User = get_user_model()
for u in User.objects.all():
    print(f"{u.username}:{u.is_staff}:{u.is_superuser}")
