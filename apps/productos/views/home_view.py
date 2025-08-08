from django.shortcuts import render, redirect
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from apps.productos.models import Producto

def home(request):
    productos = Producto.objects.order_by('-creado')[:200]
    context = {
        'productos': productos,
        'nombre_tienda': 'Tiendita Marian',
        'descripcion_tienda': 'La mejor tienda de productos de Marian',
    }
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        print(f"DEBUG: Formulario recibido - Nombre: {name}, Email: {email}, Mensaje: {message}")
        if name and email and message:
            subject = f'Mensaje de contacto de tu Tiendita - {name}'
            email_message = f'Nombre: {name}\n' \
                            f'Email: {email}\n\n' \
                            f'Mensaje:\n{message}'
            try:
                send_mail(subject, email_message, settings.EMAIL_HOST_USER, ['admin@tienditademarian.com'])
                messages.success(request, '¡Tu mensaje ha sido enviado con éxito!')
            except Exception as e:
                messages.error(request, f'Error al enviar el mensaje: {e}')
    return render(request, 'productos/index.html', context)
