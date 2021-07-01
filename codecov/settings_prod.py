from .settings_base import *
import os
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


DEBUG = False
THIS_POD_IP = os.environ.get("THIS_POD_IP")
ALLOWED_HOSTS = get_config(
    "setup", "api_allowed_hosts", default=["codecov.io-shadow", ".codecov.io"]
)
if THIS_POD_IP:
    ALLOWED_HOSTS.append(THIS_POD_IP)

INSTALLED_APPS += ["ddtrace.contrib.django"]

WEBHOOK_URL = get_config("setup", "webhook_url", default="https://codecov.io")


STRIPE_API_KEY = os.environ.get("SERVICES__STRIPE__API_KEY", None)
STRIPE_ENDPOINT_SECRET = os.environ.get("SERVICES__STRIPE__ENDPOINT_SECRET", None)
STRIPE_PLAN_IDS = {
    "users-pr-inappm": "price_1Gv2B8GlVGuVgOrkFnLunCgc",
    "users-pr-inappy": "price_1Gv2COGlVGuVgOrkuOYVLIj7",
}


sentry_sdk.init(
    dsn=os.environ.get("SERVICES__SENTRY__SERVER_DSN", None),
    integrations=[DjangoIntegration()],
    environment="PRODUCTION",
)

CORS_ALLOW_CREDENTIALS = True
CODECOV_URL = get_config("setup", "codecov_url", default="https://codecov.io")
CODECOV_DASHBOARD_URL = get_config(
    "setup", "codecov_dashboard_url", default="https://app.codecov.io"
)
CORS_ALLOWED_ORIGINS = [
    CODECOV_URL,
    CODECOV_DASHBOARD_URL,
    "https://gazebo.netlify.app",  # to access unreleased URL of gazebo
]

DATA_UPLOAD_MAX_MEMORY_SIZE = 15000000
SILENCED_SYSTEM_CHECKS = ['urls.W002']