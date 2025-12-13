import os
from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# --- SECURITY AND SECRET SETTINGS ---

# Read SECRET_KEY, DEBUG, and ALLOWED_HOSTS from the .env file
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Define ALLOWED_HOSTS for security
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())


# --- APPLICATION DEFINITION ---

# Add all your installed apps here, including third-party and custom apps.
INSTALLED_APPS = [
    # Django Core Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-Party Apps
    'django_otp',
    'two_factor',  # For staff 2FA login
    
    # Local Apps
    'accounts',
    'scheduling',
    'compliance',
    'inventory',
]

# Middleware provides hooks into Django’s request/response processing.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Two-factor authentication middleware (must come after auth)
    'django_otp.middleware.OTPMiddleware',
]

ROOT_URLCONF = 'fd_intranet.urls'

# Configuration for how Django finds and renders HTML templates.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Global templates directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'fd_intranet.wsgi.application'


# --- DATABASE CONFIGURATION ---

# We are using the default SQLite database for simplicity.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- AUTHENTICATION AND AUTHORIZATION ---

# Custom user model is not needed, but we require 2FA for staff/superuser.
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# Set the URL where Django redirects users after successful login.
LOGIN_URL = 'two_factor:login'  # Direct users to the 2FA login page
LOGIN_REDIRECT_URL = '/'        # Redirect to the root (dashboard) after login
LOGOUT_REDIRECT_URL = '/'       # Redirect to root after logout


# --- INTERNATIONALIZATION ---

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York' # Use your local time zone
USE_I18N = True
USE_TZ = True


# --- STATIC FILES (CSS, JavaScript, Images) ---

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' # Location for 'collectstatic' in production


# --- MEDIA FILES (User Uploads like Certifications) ---

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media' # Location for user-uploaded files


# --- TWO-FACTOR AUTHENTICATION SETTINGS ---

# Mandatory for enforcing 2FA on staff and superusers
TWO_FACTOR_FORMS = {
    # Custom form to require 2FA for staff/superusers only
    'login': 'two_factor.forms.TwoFactorAuthenticationForm', 
}


# --- EMAIL CONFIGURATION (For 2FA, Shift Notifications, and Mass Messages) ---

# Read email configuration from .env file
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER')
SERVER_EMAIL = config('EMAIL_HOST_USER') # Used for sending error messages


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
