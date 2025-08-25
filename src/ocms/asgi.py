import os
import sys
from pathlib import Path

from django.core.asgi import get_asgi_application

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "src"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ocms.settings")
application = get_asgi_application()
