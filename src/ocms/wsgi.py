import os
import sys
from django.core.wsgi import get_wsgi_application
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR / "src"))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocms.settings')
application = get_wsgi_application()
