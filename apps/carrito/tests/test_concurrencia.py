"""¿Qué pasa si dos clientas compran la última unidad al mismo tiempo?

El checkout original leía el stock, creaba la orden y no bloqueaba nada (y de
hecho ni siquiera descontaba el inventario). Dos peticiones simultáneas leían
ambas "queda 1" y ambas vendían esa única unidad: se vendía dos veces lo que
había una sola vez.

`select_for_update(of=("producto",))` cierra la carrera: la segunda transacción
espera a que la primera confirme y entonces ve el stock ya descontado.

El test necesita hilos y transacciones reales, así que va con
`django_db(transaction=True)` y sobre una base en disco: SQLite en memoria no
comparte estado entre conexiones.
"""

import threading
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, connections, transaction
from django.db.models import F

from apps.carrito.models import Carrito, ItemCarrito
from apps.carrito.services import CheckoutService
from apps.orden.models import Orden
from apps.productos.models import Producto
from core.events import Despachador
from core.exceptions import StockInsuficienteError

User = get_user_model()

# SQLite NO implementa SELECT ... FOR UPDATE: Django lo ignora en silencio (su
# feature `has_select_for_update` es False). El test igual pasaría, pero por el
# lock global de escritura de SQLite y no por nuestro bloqueo — un verde que no
# prueba nada. Se ejecuta contra PostgreSQL, que es lo que corre en producción
# (el CI levanta un servicio postgres justamente para esto).
requiere_bloqueo_real = pytest.mark.skipif(
    not connection.features.has_select_for_update,
    reason=(
        "El backend actual no soporta select_for_update, así que este test no "
        "probaría el bloqueo. Correr con DATABASE_URL apuntando a PostgreSQL."
    ),
)


@requiere_bloqueo_real
@pytest.mark.django_db(transaction=True)
def test_dos_compras_simultaneas_de_la_ultima_unidad(django_db_setup):
    producto = Producto.objects.create(
        nombre="La última muñeca", descripcion="queda una", precio=Decimal("9990"), stock=1
    )

    compradoras = []
    for nombre in ("ana", "bea"):
        usuaria = User.objects.create_user(username=nombre, password="clave-segura-123")
        carrito = Carrito.objects.create(usuario=usuaria)
        ItemCarrito.objects.create(carrito=carrito, producto=producto, cantidad=1)
        compradoras.append(usuaria)

    resultados: list[str] = []
    barrera = threading.Barrier(len(compradoras))
    despachador_mudo = Despachador()

    def comprar(usuaria):
        try:
            # Las dos llegan al checkout exactamente a la vez.
            barrera.wait(timeout=5)
            CheckoutService(usuaria, despachador=despachador_mudo).ejecutar()
            resultados.append("vendida")
        except StockInsuficienteError:
            resultados.append("sin stock")
        finally:
            # Cada hilo abre su propia conexión: hay que cerrarla a mano.
            connections.close_all()

    hilos = [threading.Thread(target=comprar, args=(u,)) for u in compradoras]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=10)

    producto.refresh_from_db()

    assert sorted(resultados) == ["sin stock", "vendida"], (
        f"exactamente una compra debe prosperar, resultados={resultados}"
    )
    assert producto.stock == 0, "no se puede vender dos veces la misma unidad"
    assert Orden.objects.count() == 1


@pytest.mark.django_db
def test_la_base_de_datos_rechaza_el_stock_negativo(producto):
    """Última línea de defensa, y la única que ningún código puede saltarse.

    El bloqueo vive en la aplicación; este `CheckConstraint` vive en el motor. Si
    mañana alguien escribe un `update()` crudo que se salta el servicio, o si el
    bloqueo falla, la base se niega igual: es imposible dejar el inventario en
    negativo. A diferencia de `select_for_update`, esto sí funciona en SQLite.
    """
    with pytest.raises(IntegrityError), transaction.atomic():
        Producto.objects.filter(pk=producto.pk).update(stock=F("stock") - 999)
