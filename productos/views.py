from rest_framework import viewsets
from .models import Producto
from .serializers import ProductoSerializer
from django.contrib import messages
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.mail import send_mail
from rest_framework import permissions # Asegúrate de importar las clases de permisos necesarias

class ProductoViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny] # Permite acceso a todos los usuarios
    queryset = Producto.objects.all().order_by('-creado')
    serializer_class = ProductoSerializer

    def get_serializer_context(self):
        return {"request": self.request}

def home(request):
    productos = Producto.objects.order_by('-creado')[:200] # Limit to 200 products

    context = {
        'productos': productos,
        'nombre_tienda': 'Tiendita Marian',
        'descripcion_tienda': 'La mejor tienda de productos de Marian',
    }

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        print(f"DEBUG: Formulario recibido - Nombre: {name}, Email: {email}, Mensaje: {message}") # Para depuración

        if name and email and message: # Verifica que los campos no estén vacíos
            subject = f'Mensaje de contacto de tu Tiendita - {name}'
            email_message = f'Nombre: {name}\n' \
                            f'Email: {email}\n\n' \
                            f'Mensaje:\n{message}'
            
            try:
                send_mail(
                    subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    ['canolealn@gmail.com'], # ¡CAMBIA ESTO por tu correo personal!
                    fail_silently=False,
                )
                messages.success(request, '¡Tu mensaje ha sido enviado con éxito!')
                print("DEBUG: Correo enviado con éxito.") # Para depuración
                return redirect('home') # Redirige a la página principal por su nombre de URL (cambiado de 'index' a 'home')
            except Exception as e:
                print(f"Error al enviar el correo: {e}")
                context['error_message'] = "Hubo un error al enviar tu mensaje. Inténtalo de nuevo más tarde."
        else:
            print("DEBUG: Faltan campos obligatorios en el formulario.")
            context['error_message'] = "Por favor, completa todos los campos del formulario."

    return render(request, 'productos/index.html', context)
