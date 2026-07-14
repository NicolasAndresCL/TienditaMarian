"""Vitrina HTML de la tienda con su formulario de contacto.

No es parte de la API: es la página que se sirve en `/`. El frontend React
consume los endpoints REST y no pasa por aquí.
"""

import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.productos.models import Producto

logger = logging.getLogger(__name__)

MAX_PRODUCTOS_VITRINA = 200


def home(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        _procesar_formulario_contacto(request)

    context = {
        'productos': Producto.objects.order_by('-creado')[:MAX_PRODUCTOS_VITRINA],
        'nombre_tienda': 'Tiendita Marian',
        'descripcion_tienda': 'La mejor tienda de productos de Marian',
    }
    return render(request, 'productos/index.html', context)


def _procesar_formulario_contacto(request: HttpRequest) -> None:
    nombre = (request.POST.get('name') or '').strip()
    email = (request.POST.get('email') or '').strip()
    mensaje = (request.POST.get('message') or '').strip()

    if not (nombre and email and mensaje):
        messages.error(request, 'Completa tu nombre, tu correo y el mensaje.')
        return

    try:
        send_mail(
            subject=f'Mensaje de contacto de tu Tiendita - {nombre}',
            message=f'Nombre: {nombre}\nEmail: {email}\n\nMensaje:\n{mensaje}',
            # Antes iba `EMAIL_HOST_USER`, que está vacío: el correo salía sin remitente.
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACTO_EMAIL],
        )
    except Exception:
        # El detalle técnico va al log, no a la pantalla del visitante: el
        # mensaje anterior le mostraba la excepción cruda.
        logger.exception('Falló el envío del formulario de contacto')
        messages.error(request, 'No pudimos enviar tu mensaje. Inténtalo de nuevo en un momento.')
        return

    logger.info('Formulario de contacto enviado por %s', email)
    messages.success(request, '¡Tu mensaje ha sido enviado con éxito!')
