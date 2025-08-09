import os
from pathlib import Path
from datetime import timedelta
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = '.env.test' if os.getenv('ENV') == 'test' else '.env'
ENV_PATH = os.path.join(BASE_DIR, ENV_FILE)
print(f" Cargando configuracion desde: {ENV_PATH}")

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'apps.pagos',
    'apps.envios',
    'apps.notificaciones',
    'apps.descuentos',
    'apps.reviews',
    'apps.analytics',
    'apps.productos',
    'apps.carrito',
    'apps.orden',
    'apps.auth_api',
    'apps.auditlog',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'config.wsgi.application'




DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'tiendita_marian',
        'USER': env('DATABASES_USER'),
        'PASSWORD': env('DATABASES_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}




AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]




LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True




STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR,'static')
]



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Tiendita de Marian API',
    'DESCRIPTION': (
        'Documentación interactiva y bilingüe de la API REST para la gestión integral de productos, '
        'ventas, usuarios y auditoría de eventos en la Tiendita de Marian. Incluye endpoints para '
        'operaciones CRUD, autenticación segura, trazabilidad automática de acciones y visualización '
        'estructurada de datos. Compatible con herramientas externas mediante OpenAPI 3.0, con '
        'serialización desacoplada y pruebas automatizadas en CI/CD.'
    ),
    'VERSION': '1.0.0',
    'CONTACT': {
        'name': 'Soporte de la Tiendita',
        'email': 'nicolas.cano.leal@gmail.com',
    },
    'LICENSE': {
        'name': 'Licencia MIT',
        'url': 'https://opensource.org/licenses/MIT',
    },


    'SECURITY': [
        {'BearerAuth': []},
    ],
    'COMPONENTS': {
        'securitySchemes': {
            'BearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },

    'SERVERS': [
        {
            'url': 'http://127.0.0.1:8000/api/',
            'description': 'Servidor de Desarrollo Local',
        },
    ],

    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_SPLIT_PATCH': True,

    'SERVE_INCLUDE_SCHEMA': False, 
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,          
        'displayRequestDuration': True, 
        'filter': True,               
        'persistAuthorization': True, 
        'syntaxHighlight.theme': 'obsidian', 
        'displayOperationId': True,   
    },
    'SWAGGER_UI_STYLES': {
        'primaryColor': "#db34bf",
        'secondaryColor': '#2ecc71',
        'backgroundColor': '#f9f9f9',
        'textColor': '#333333',
    },
    'TEMPLATE_DIR': 'templates/drf_spectacular_sidecar',
    'STATIC_DIR': 'static/drf_spectacular_sidecar',
    'REDOC_UI_SETTINGS': {
        'pathInMiddlePanel': True,   
        'theme': {
            'typography': {
                'fontFamily': '"Inter", sans-serif',
            },
            'colors': {
                'primary': {
                    'main': '#0ea5e9'
                }
            }
        }
    },
    'SWAGGER_UI_DIST': 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@latest',
    'REDOC_DIST': 'https://cdn.jsdelivr.net/npm/redoc@latest',

    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums',
    ],

    'RENDERER_WHITELIST': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'AUTHENTICATION_WHITELIST': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],

    'SORT_OPERATIONS': True,
    'ENFORCE_NON_BLANK_FIELDS': True, 
    'CAMELIZE_NAMES': True, 

}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}


CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')

EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''