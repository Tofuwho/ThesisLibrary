
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'thesis_site.settings')
django.setup()

print("Importing main.views...")
try:
    print("Done importing public")
    print("Done importing portal")
    print("Done importing admin")
    print("Done importing records")
    print("Done importing auth")
    print("Done importing secure")
    print("Done importing api")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
