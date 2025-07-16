from productos.models import Producto

def corregir_rutas_imagenes():
    for producto in Producto.objects.all():
        if producto.image and not producto.image.name.startswith('productos/images/'):
            nombre_archivo = producto.image.name.split('/')[-1]
            producto.image.name = f'productos/images/{nombre_archivo}'
            producto.save()
    print('Rutas de imágenes corregidas.')

# Uso: Ejecuta este script con shell de Django:
# python manage.py shell < productos/scripts/corregir_rutas_imagenes.py
