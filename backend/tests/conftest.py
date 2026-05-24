import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-32chars")
os.environ.setdefault("AUTH_HTTPONLY_REFRESH", "false")
os.environ.setdefault("ENVIRONMENT", "development")