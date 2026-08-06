"""Reglas de negocio del carrito y del checkout.

Esta capa no existía: la lógica vivía dentro de las vistas, que además hacían
`data['producto_id']` e `int(request.data.get('cantidad'))` sobre datos crudos
del cliente — un `KeyError` o un `ValueError` y la respuesta era un 500.

Lo que arregla el checkout:

- **descontaba el stock: no lo hacía**. La orden se creaba y el inventario
  quedaba intacto, así que se podía vender indefinidamente algo agotado;
- **no había bloqueo**: dos clientas comprando la última unidad al mismo tiempo
  se llevaban las dos. `select_for_update()` cierra esa carrera;
- **recorría `carrito.items.all()` tres veces** y accedía a `item.producto` en
  cada vuelta: N+1 consultas;
- **ignoraba los descuentos y no creaba el envío**, pese a que ambas apps existen.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.db.models import F

from apps.carrito.models import Carrito, ItemCarrito
from apps.orden.models import ItemOrden, Orden
from apps.productos.models import Producto
from core.events import Evento
from core.events import despachador as despachador_global
from core.exceptions import (
    CantidadInvalidaError,
    CarritoVacioError,
    ProductoNoEncontradoError,
    StockInsuficienteError,
)

logger = logging.getLogger(__name__)

CERO = Decimal("0.00")


def parsear_cantidad(valor: object, *, por_defecto: int = 1) -> int:
    """Convierte lo que llegue del cliente en una cantidad válida.

    Antes esto era `int(request.data.get('cantidad', 1))` dentro de la vista: si
    llegaba `"abc"` o `None`, el ValueError salía como HTTP 500. Ahora es un error
    de negocio con su código, y el cliente recibe un 400 que puede entender.
    """
    if valor is None:
        return por_defecto

    # `int(2.5)` devuelve 2 sin protestar: la clienta pediría 2,5 unidades y se
    # le cobrarían 2 en silencio. Y `bool` es subclase de `int`, así que `True`
    # se colaría como cantidad 1.
    if isinstance(valor, bool) or (isinstance(valor, float) and not valor.is_integer()):
        raise CantidadInvalidaError(valor)

    try:
        cantidad = int(valor)
    except (TypeError, ValueError) as exc:
        raise CantidadInvalidaError(valor) from exc

    if cantidad <= 0:
        # `PositiveIntegerField` no valida en `save()`, así que una cantidad de 0
        # o negativa se colaba hasta la base de datos.
        raise CantidadInvalidaError(cantidad)

    return cantidad


class CarritoService:
    """Operaciones sobre el carrito de una usuaria."""

    def __init__(self, usuario: AbstractBaseUser) -> None:
        self.usuario = usuario

    @property
    def carrito(self) -> Carrito:
        carrito, _ = Carrito.objects.get_or_create(usuario=self.usuario)
        return carrito

    def _buscar_producto(self, producto_id: object) -> Producto:
        if producto_id is None:
            # `data['producto_id']` lanzaba KeyError → 500. Ahora es un 404 claro.
            raise ProductoNoEncontradoError("Falta indicar el producto.")

        producto = Producto.objects.filter(pk=producto_id).first()
        if producto is None:
            raise ProductoNoEncontradoError()

        return producto

    def agregar(self, producto_id: object, cantidad: object = 1) -> ItemCarrito:
        """Suma unidades al carrito, validando el stock disponible."""
        producto = self._buscar_producto(producto_id)
        cantidad = parsear_cantidad(cantidad)

        item, creado = ItemCarrito.objects.get_or_create(
            carrito=self.carrito, producto=producto, defaults={"cantidad": 0}
        )
        cantidad_final = item.cantidad + cantidad

        # Se valida contra el total que quedaría en el carrito, no contra lo que
        # se agrega ahora: pedir 3 veces "1 unidad" de algo con stock 2 tiene que
        # fallar en el tercer intento.
        if cantidad_final > producto.stock:
            raise StockInsuficienteError(producto.nombre, cantidad_final, producto.stock)

        item.cantidad = cantidad_final
        item.save(update_fields=["cantidad"])

        logger.info(
            "Carrito: usuario=%s producto=%s cantidad=%s (%s)",
            self.usuario.pk,
            producto.pk,
            cantidad_final,
            "nuevo" if creado else "actualizado",
        )
        return item

    def actualizar_cantidad(self, producto_id: object, cantidad: object) -> ItemCarrito:
        producto = self._buscar_producto(producto_id)
        cantidad = parsear_cantidad(cantidad)

        item = ItemCarrito.objects.filter(carrito=self.carrito, producto=producto).first()
        if item is None:
            raise ProductoNoEncontradoError("Ese producto no está en tu carrito.")

        if cantidad > producto.stock:
            raise StockInsuficienteError(producto.nombre, cantidad, producto.stock)

        item.cantidad = cantidad
        item.save(update_fields=["cantidad"])
        return item

    def quitar(self, producto_id: object) -> None:
        producto = self._buscar_producto(producto_id)
        borrados, _ = ItemCarrito.objects.filter(
            carrito=self.carrito, producto=producto
        ).delete()

        if not borrados:
            raise ProductoNoEncontradoError("Ese producto no está en tu carrito.")

    def vaciar(self) -> None:
        self.carrito.items.all().delete()

    def subtotal(self) -> Decimal:
        items = self.carrito.items.select_related("producto")
        return sum((i.producto.precio * i.cantidad for i in items), CERO)


class CheckoutService:
    """Convierte un carrito en una orden: valida, cobra el stock y registra.

    Todo el trabajo ocurre dentro de una única transacción: si algo falla a mitad
    de camino, no queda una orden sin stock descontado ni un stock descontado sin
    orden.

    Los efectos posteriores (correo, notificación, envío) NO van dentro de la
    regla de negocio: se anuncian por el despachador de eventos. Así el servicio
    no sabe quién escucha, se puede probar aislado, y un fallo del servidor de
    correo no tumba una venta que ya ocurrió (skill §2.2 y §2.3).
    """

    def __init__(self, usuario: AbstractBaseUser, despachador=None) -> None:
        self.usuario = usuario
        # Despachador inyectable: en los tests se pasa uno vacío para probar la
        # regla de negocio sin disparar correos ni notificaciones.
        self.despachador = despachador or despachador_global

    @transaction.atomic
    def ejecutar(self, cupon: str | None = None) -> Orden:
        items = self._items_bloqueados()

        if not items:
            raise CarritoVacioError()

        self._validar_stock(items)
        orden = self._crear_orden(items, cupon)
        self._descontar_stock(items)
        self._vaciar_carrito()

        # Se emite al confirmarse la transacción, no antes: si el commit falla,
        # no se manda un correo de "gracias por tu compra" por una orden que no
        # llegó a existir.
        transaction.on_commit(lambda: self.despachador.emitir(Evento.ORDEN_CREADA, orden))

        logger.info(
            "Checkout completado: usuario=%s orden=%s total=%s items=%s",
            self.usuario.pk,
            orden.pk,
            orden.total,
            len(items),
        )
        return orden

    def _items_bloqueados(self) -> list[ItemCarrito]:
        """Lee el carrito bloqueando las filas de producto hasta el commit.

        `select_for_update` sobre el producto es lo que impide que dos checkouts
        simultáneos lean ambos "queda 1" y ambos vendan esa única unidad. El
        segundo espera a que el primero termine y ve el stock ya descontado.
        """
        return list(
            ItemCarrito.objects.filter(carrito__usuario=self.usuario)
            .select_related("producto")
            .select_for_update(of=("producto",))
        )

    def _validar_stock(self, items: list[ItemCarrito]) -> None:
        faltantes = [item for item in items if item.cantidad > item.producto.stock]

        if faltantes:
            item = faltantes[0]
            self.despachador.emitir(Evento.STOCK_AGOTADO, item.producto)
            raise StockInsuficienteError(
                item.producto.nombre, item.cantidad, item.producto.stock
            )

    def _crear_orden(self, items: list[ItemCarrito], cupon: str | None) -> Orden:
        from apps.descuentos.services import DescuentoService

        subtotal = sum((i.producto.precio * i.cantidad for i in items), CERO)
        total, _descuento = DescuentoService.aplicar(subtotal, cupon)

        orden = Orden.objects.create(usuario=self.usuario, total=total)

        # `bulk_create` en vez de un `create()` por vuelta: una consulta en lugar
        # de N. El precio se congela en el ítem: si mañana sube, esta orden
        # conserva el precio al que se compró.
        ItemOrden.objects.bulk_create(
            [
                ItemOrden(
                    orden=orden,
                    producto=item.producto,
                    cantidad=item.cantidad,
                    precio=item.producto.precio,
                )
                for item in items
            ]
        )
        return orden

    def _descontar_stock(self, items: list[ItemCarrito]) -> None:
        """Descuenta el inventario. Esto simplemente no se hacía.

        Se usa `F()` para que la resta la calcule la base de datos sobre el valor
        real de la fila, y no sobre el que leyó Python hace unos milisegundos.
        """
        for item in items:
            Producto.objects.filter(pk=item.producto_id).update(
                stock=F("stock") - item.cantidad
            )

    def _vaciar_carrito(self) -> None:
        ItemCarrito.objects.filter(carrito__usuario=self.usuario).delete()
