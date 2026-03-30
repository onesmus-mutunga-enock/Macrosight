import os
import sys
import django

# 1️⃣ Add project root to Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# 2️⃣ Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "macrosight.settings")

# 3️⃣ Setup Django
django.setup()

# 3️⃣ Now safe to import anything Django/DRF
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.viewsets import ViewSet
import importlib

def fix_views():
    for app in settings.LOCAL_APPS:
        try:
            views_module_name = f"{app}.views"
            views_module = importlib.import_module(views_module_name)
        except ModuleNotFoundError:
            continue  # skip apps with no views.py

        for attr_name in dir(views_module):
            view_class = getattr(views_module, attr_name)
            if isinstance(view_class, type) and issubclass(view_class, APIView):
                if issubclass(view_class, (GenericAPIView, ViewSet)):
                    continue

                # Patch inheritance
                view_class.__bases__ = (GenericAPIView,) + tuple(
                    b for b in view_class.__bases__ if b is not APIView
                )
                print(f"[PATCHED] {app}.{attr_name} → now inherits GenericAPIView")

                # Check if serializer_class exists
                if not (hasattr(view_class, "serializer_class") or hasattr(view_class, "get_serializer_class")):
                    print(f"[WARNING] {app}.{attr_name} missing serializer_class or get_serializer_class. Define it manually.")

if __name__ == "__main__":
    fix_views()
    print("✅ Production-ready APIViews patched.")