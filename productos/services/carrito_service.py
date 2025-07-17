# Aquí puedes poner la lógica de negocio del carrito, por ejemplo:

def calcular_total_carrito(carrito):
    return sum(item.producto.precio * item.cantidad for item in carrito.items.all())
