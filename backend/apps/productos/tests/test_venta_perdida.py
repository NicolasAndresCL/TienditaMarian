"""El aviso de venta perdida: `STOCK_AGOTADO` deja de emitirse al vacío.

Estos tests cubren las dos mitades de un mismo problema:

1. que el suscriptor haga lo que dice (crear el aviso para el staff), y
2. que su trabajo **sobreviva**, que es donde estaba el defecto de verdad.

El evento se emitía dentro de la transacción del checkout, una línea antes del
`raise` que la revierte. El suscriptor corría sin dar error y no persistía nada:
un aviso que se pisaba a sí mismo. Sin el test 2, suscribir el efecto habría
parecido funcionar.
"""

import pytest
from django.contrib.auth import get_user_model

from apps.carrito.models import Carrito, ItemCarrito
from apps.carrito.services import CheckoutService
from apps.notificaciones.models import Notificacion
from apps.productos.subscribers import avisar_venta_perdida
from core.exceptions import StockInsuficienteError

User = get_user_model()


@pytest.fixture
def staff(db):
    return User.objects.create_user(
        username="marian_tienda", email="tienda@tiendita.cl",
        password="clave-segura-123", is_staff=True,
    )


def _carrito_que_no_alcanza(usuario, producto, pedidos=5, quedan=1):
    producto.stock = quedan
    producto.save(update_fields=["stock"])
    carrito, _ = Carrito.objects.get_or_create(usuario=usuario)
    ItemCarrito.objects.create(carrito=carrito, producto=producto, cantidad=pedidos)


@pytest.mark.django_db
def test_el_aviso_nombra_el_producto_y_lo_que_queda(staff, producto):
    avisar_venta_perdida(producto)

    aviso = Notificacion.objects.get(usuario=staff)
    assert producto.nombre in aviso.mensaje
    assert str(producto.stock) in aviso.mensaje


@pytest.mark.django_db
def test_sin_staff_no_falla_ni_crea_nada(producto):
    """Una base recién creada no tiene destinatarios; eso no es un error."""
    avisar_venta_perdida(producto)

    assert Notificacion.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_el_aviso_sobrevive_al_rollback_del_checkout(usuario, staff, producto):
    """El corazón del arreglo: emitir fuera de la transacción revertida.

    Con la emisión donde estaba —dentro del `atomic`, antes del `raise`— este
    test ve 0 notificaciones: el rollback se lleva el aviso junto con la orden
    que nunca existió.
    """
    _carrito_que_no_alcanza(usuario, producto)

    with pytest.raises(StockInsuficienteError):
        CheckoutService(usuario).ejecutar()

    assert Notificacion.objects.filter(usuario=staff).count() == 1

    # Y el rollback sí hizo lo suyo con lo que le tocaba: ninguna orden.
    from apps.orden.models import Orden

    assert Orden.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_un_checkout_que_sale_bien_no_avisa_de_nada(usuario, staff, producto):
    """El aviso es de venta perdida, no de venta."""
    _carrito_que_no_alcanza(usuario, producto, pedidos=2, quedan=10)

    CheckoutService(usuario).ejecutar()

    assert Notificacion.objects.filter(asunto__icontains="stock").count() == 0
