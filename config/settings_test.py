from .settings import *

# ✅ Base de datos en memoria para tests rápidos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# ✅ Desactiva validadores de contraseña
AUTH_PASSWORD_VALIDATORS = []

# ✅ Acelera hashing de contraseñas
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ✅ Email backend en memoria
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# ✅ Hosts seguros para entorno CI
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# ✅ CORS para pruebas locales
CORS_ALLOWED_ORIGINS = ['http://127.0.0.1:8000']

# ✅ Debug desactivado
DEBUG = False
