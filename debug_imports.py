
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'thesis_site.settings')
django.setup()

print("Importing main.views...")
try:
    import main.views.public
    print("Done importing public")
    import main.views.portal
    print("Done importing portal")
    import main.views.admin
    print("Done importing admin")
    import main.views.records
    print("Done importing records")
    import main.views.auth
    print("Done importing auth")
    import main.views.secure
    print("Done importing secure")
    import main.views.api
    print("Done importing api")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
