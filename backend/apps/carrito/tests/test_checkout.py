"""Tests del checkout — el corazón del negocio.

El checkout anterior creaba la orden y **nunca tocaba el inventario**: se podía
vender indefinidamente algo agotado. Tampoco bloqueaba nada, así que dos clientas
podían comprar la misma última unidad. Estos tests fijan las dos reglas.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core import mail

from apps.carrito.models import Carrito, ItemCarrito
from apps.carrito.services import CarritoService, CheckoutService
from apps.descuentos.models import Descuento
from apps.envios.models import Envio
from apps.orden.models import Orden
from apps.productos.models import Producto
from core.events import Despachador
from core.exceptions import (
    CantidadInvalidaError,
    CarritoVacioError,
    ProductoNoEncontradoError,
    StockInsuficienteError,
)


@pytest.fixture
def despachador_mudo() -> Despachador:
    """Despachador vacío: prueba la regla de negocio sin correos ni notificaciones."""
    return Despachador()


@pytest.fixture
def carrito_con_items(db, usuario, producto) -> Carrito:
    carrito = Carrito.objects.create(usuario=usuario)
    ItemCarrito.objects.create(carrito=carrito, producto=producto, cantidad=2)
    return carrito


# ------------------------------------------------------------------ el stock


@pytest.mark.django_db
def test_el_checkout_descuenta_el_stock(usuario, producto, carrito_con_items, despachador_mudo):
    """La regla que faltaba: comprar 2 unidades baja el stock de 10 a 8."""
    assert producto.stock == 10

    CheckoutService(usuario, despachador=despachador_mudo).ejecutar()

    producto.refresh_from_db()
    assert producto.stock == 8


@pytest.mark.django_db
def test_el_stock_baja_exactamente_una_vez(usuario, producto, carrito_con_items, despachador_mudo):
    CheckoutService(usuario, despachador=despachador_mudo).ejecutar()

    producto.refresh_from_db()
    assert producto.stock == 8, "un doble descuento dejaría 6"


@pytest.mark.django_db
def test_no_se_puede_comprar_mas_de_lo_que_hay(usuario, despachador_mudo):
    producto = Producto.objects.create(
        nombre="Última muñeca", descripcion="x", precio=Decimal("5000"), stock=2
    )
    carrito = Carrito.objects.create(usuario=usuario)
    # Se fuerza el ítem en la base para simular un carrito armado cuando sí había
    # stock, y que la bodega se vació entremedio.
    ItemCarrito.objects.create(carrito=carrito, producto=producto, cantidad=3)

    with pytest.raises(StockInsuficienteError) as info:
        CheckoutService(usuario, despachador=despachador_mudo).ejecutar()

    assert info.value.solicitado == 3
    assert info.value.disponible == 2


@pytest.mark.django_db
def test_si_falta_stock_no_queda_ninguna_orden(usuario, despachador_mudo):
    """Todo o nada: la transacción se revierte entera."""
    producto = Producto.objects.create(
        nombre="Pelota", descripcion="x", precio=Decimal("1000"), stock=1
    )
    carrito = Carrito.objects.create(usuario=usuario)
    ItemCarrito.objects.create(carrito=carrito, producto=producto, cantidad=5)

    with pytest.raises(StockInsuficienteError):
        CheckoutService(usuario, despachador=despachador_mudo).ejecutar()

    assert not Orden.objects.exists()
    producto.refresh_from_db()
    assert producto.stock == 1, "el stock no puede haberse tocado"


@pytest.mark.django_db
def test_comprar_todo_el_stock_lo_deja_en_cero(usuario, despachador_mudo):
    producto = Producto.objects.create(
        nombre="Último", descripcion="x", precio=Decimal("1000"), stock=3
    )
    carrito = Carrito.objects.create(usuario=usuario)
    ItemCarrito.objects.create(carrito=carrito, producto=producto, cantidad=3)

    CheckoutService(usuario, despachador=despachador_mudo).ejecutar()

    producto.refresh_from_db()
    assert producto.stock == 0


# ------------------------------------------------------------------ la orden


@pytest.mark.django_db
def test_el_carrito_vacio_no_genera_orden(usuario, despachador_mudo):
    Carrito.objects.create(usuario=usuario)

    with pytest.raises(CarritoVacioError):
        CheckoutService(usuario, despachador=despachador_mudo).ejecutar()

    assert not Orden.objects.exists()


@pytest.mark.django_db
def test_la_orden_guarda_el_total_correcto(usuario, producto, carrito_con_items, despachador_mudo):
    orden = CheckoutService(usuario, despachador=despachador_mudo).ejecutar()

    assert orden.total == Decimal("6000.00")  # 2 x 3000
    assert orden.items.count() == 1


@pytest.mark.django_db
def test_el_precio_se_congela_en_la_orden(usuario, producto, carrito_con_items, despachador_mudo):
    """Si mañana sube el precio, la orden conserva el que se pagó."""
    orden = CheckoutService(usuario, despachador=despachador_mudo).ejecutar()

    producto.precio = Decimal("9999.00")
    producto.save()

    item = orden.items.first()
    assert item.precio == Decimal("3000.00")


@pytest.mark.django_db
def test_el_carrito_queda_vacio_tras_comprar(usuario, carrito_con_items, despachador_mudo):
    CheckoutService(usuario, despachador=despachador_mudo).ejecutar()

    assert not ItemCarrito.objects.filter(carrito__usuario=usuario).exists()


# ------------------------------------------------------------------ descuentos


@pytest.mark.django_db
def test_el_cupon_de_porcentaje_rebaja_el_total(
    usuario, producto, carrito_con_items, despachador_mudo
):
    Descuento.objects.create(
        nombre="VERANO",
        tipo="porcentaje",
        valor=Decimal("10.00"),
        activo=True,
        fecha_inicio=date.today() - timedelta(days=1),
        fecha_fin=date.today() + timedelta(days=30),
    )

    orden = CheckoutService(usuario, despachador=despachador_mudo).ejecutar(cupon="VERANO")

    assert orden.total == Decimal("5400.00")  # 6000 - 10%


@pytest.mark.django_db
def test_un_cupon_vencido_no_se_aplica(usuario, carrito_con_items, despachador_mudo):
    from core.exceptions import DescuentoInvalidoError

    Descuento.objects.create(
        nombre="NAVIDAD",
        tipo="porcentaje",
        valor=Decimal("50.00"),
        activo=True,
        fecha_inicio=date.today() - timedelta(days=60),
        fecha_fin=date.today() - timedelta(days=30),
    )

    with pytest.raises(DescuentoInvalidoError) as info:
        CheckoutService(usuario, despachador=despachador_mudo).ejecutar(cupon="NAVIDAD")

    assert "vencido" in info.value.motivo
    assert not Orden.objects.exists()


@pytest.mark.django_db
def test_un_cupon_gigante_no_deja_el_total_negativo(usuario, carrito_con_items, despachador_mudo):
    """La tienda no le paga al cliente por comprar."""
    Descuento.objects.create(
        nombre="EXAGERADO",
        tipo="fijo",
        valor=Decimal("999999.00"),
        activo=True,
        fecha_inicio=date.today() - timedelta(days=1),
        fecha_fin=date.today() + timedelta(days=30),
    )

    orden = CheckoutService(usuario, despachador=despachador_mudo).ejecutar(cupon="EXAGERADO")

    assert orden.total == Decimal("0.00")


# ------------------------------------------------------------------ los efectos


@pytest.mark.django_db(transaction=True)
def test_comprar_manda_un_solo_correo(usuario, carrito_con_items):
    """Antes salían DOS correos idénticos: uno de Orden.save() y otro de la señal.

    Este test reemplaza al de caracterización que congelaba ese bug.
    """
    mail.outbox.clear()

    CheckoutService(usuario).ejecutar()

    assert len(mail.outbox) == 1
    assert "Gracias por tu compra" in mail.outbox[0].subject


@pytest.mark.django_db(transaction=True)
def test_comprar_deja_el_envio_pendiente(usuario, carrito_con_items):
    """El checkout no creaba ningún envío: la app `envios` quedaba desconectada."""
    orden = CheckoutService(usuario).ejecutar()

    envio = Envio.objects.filter(orden=orden).first()
    assert envio is not None
    assert envio.estado == "pendiente"


@pytest.mark.django_db(transaction=True)
def test_si_el_correo_falla_la_venta_igual_queda_registrada(usuario, carrito_con_items, monkeypatch):
    """Skill §2.2: un servicio externo caído no puede tumbar la operación."""
    from apps.orden import subscribers

    def correo_caido(_orden):
        raise ConnectionError("servidor SMTP inalcanzable")

    monkeypatch.setattr(subscribers, "enviar_correo_confirmacion", correo_caido)

    orden = CheckoutService(usuario).ejecutar()

    assert Orden.objects.filter(pk=orden.pk).exists(), "la venta ya ocurrió: debe persistir"


# ------------------------------------------------------------------ el carrito


@pytest.mark.django_db
def test_agregar_valida_el_stock(usuario, producto):
    servicio = CarritoService(usuario)

    with pytest.raises(StockInsuficienteError):
        servicio.agregar(producto.id, 11)  # hay 10


@pytest.mark.django_db
def test_agregar_acumula_y_valida_contra_el_total(usuario):
    """Pedir "1 unidad" tres veces de algo con stock 2 debe fallar en el tercer intento."""
    producto = Producto.objects.create(
        nombre="Escaso", descripcion="x", precio=Decimal("100"), stock=2
    )
    servicio = CarritoService(usuario)

    servicio.agregar(producto.id, 1)
    servicio.agregar(producto.id, 1)

    with pytest.raises(StockInsuficienteError):
        servicio.agregar(producto.id, 1)


@pytest.mark.django_db
@pytest.mark.parametrize("cantidad", ["abc", 0, -3, "", 2.5])
def test_una_cantidad_invalida_es_un_error_de_negocio_no_un_500(usuario, producto, cantidad):
    """`int(request.data.get('cantidad'))` devolvía HTTP 500 ante "abc"."""
    with pytest.raises(CantidadInvalidaError):
        CarritoService(usuario).agregar(producto.id, cantidad)


@pytest.mark.django_db
def test_agregar_sin_producto_id_no_revienta(usuario):
    """`data['producto_id']` lanzaba KeyError → 500."""
    with pytest.raises(ProductoNoEncontradoError):
        CarritoService(usuario).agregar(None, 1)


@pytest.mark.django_db
def test_agregar_un_producto_inexistente(usuario):
    with pytest.raises(ProductoNoEncontradoError):
        CarritoService(usuario).agregar(99999, 1)
