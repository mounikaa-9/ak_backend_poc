import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ak_backend_poc.settings')

# Import ASGI application
from src.ak_backend_poc.asgi import application

# Vercel handler
app = application