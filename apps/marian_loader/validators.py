import os
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError

from apps.marian_loader.constants import ALLOWED_EXTENSIONS, EXPECTED_COLUMNS
from apps.productos.models import Producto


def validar_extension(filename: str) -> None:
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extensión '{ext}' no permitida. Solo {ALLOWED_EXTENSIONS}.")


def validar_columnas_presentes(columns: set) -> None:
    faltantes = EXPECTED_COLUMNS - columns
    if faltantes:
        raise ValueError(f"Columnas faltantes en CSV: {faltantes}")


def validar_precio(value) -> None:
    try:
        precio = float(value)
    except (TypeError, ValueError):
        raise ValueError("Precio no es un número válido.")
    if precio <= 0:
        raise ValueError("Precio debe ser mayor que cero.")


def validar_stock(value) -> None:
    try:
        stock = int(value)
    except (TypeError, ValueError):
        raise ValueError("Stock no es un entero válido.")
    if stock < 0:
        raise ValueError("Stock no puede ser negativo.")


def validar_imagen(value) -> None:
    """
    Valida que sea una URL o ruta local con extensión de imagen válida.
    """
    validator = URLValidator()
    try:
        validator(value)
    except DjangoValidationError:
        ext = os.path.splitext(value.lower())[1]
        if ext not in {'.jpg', '.jpeg', '.png', '.gif'}:
            raise ValueError(f"Formato de imagen '{ext}' no soportado.")


def crear_producto_desde_datos(datos: dict) -> Producto:
    """
    Crea una instancia de Producto con los datos validados.
    """
    producto = Producto.objects.create(
        nombre=datos['nombre'],
        descripcion=datos['descripcion'],
        image=datos['image'],
        precio=float(datos['precio']),
        stock=int(datos['stock']),
    )
    return producto
