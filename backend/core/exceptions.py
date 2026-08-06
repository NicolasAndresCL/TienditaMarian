"""Excepciones de dominio de la Tiendita.

Las reglas de negocio comunican sus fallos **lanzando**, no devolviendo un
`Response` a mano. Así la lógica queda testeable sin HTTP: un servicio puede
probarse con `pytest.raises(StockInsuficienteError)` sin levantar el framework.

`core/api/exception_handler.py` traduce cada una a su respuesta HTTP. El atributo
`codigo` viaja en el cuerpo para que el frontend reaccione a un identificador
estable y no a un texto en español que puede cambiar mañana.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework import status


class TienditaError(Exception):
    """Raíz de todos los errores de negocio.

    Capturar `TienditaError` significa "algo del negocio salió mal". Cualquier
    otra excepción es un bug y debe salir como 500, ruidosamente.
    """

    codigo: str = "error_tienda"
    http_status: int = status.HTTP_400_BAD_REQUEST
    mensaje: str = "No se pudo completar la operación."

    def __init__(self, mensaje: str | None = None) -> None:
        self.mensaje = mensaje or self.mensaje
        super().__init__(self.mensaje)

    def detalle(self) -> dict[str, Any]:
        """Datos extra para el cuerpo de la respuesta. Las subclases lo amplían."""
        return {}


class CarritoVacioError(TienditaError):
    codigo = "carrito_vacio"
    mensaje = "Tu carrito está vacío."


class CantidadInvalidaError(TienditaError):
    codigo = "cantidad_invalida"

    def __init__(self, cantidad: Any) -> None:
        self.cantidad = cantidad
        super().__init__(f"La cantidad debe ser un número entero mayor que cero (recibido: {cantidad!r}).")

    def detalle(self) -> dict[str, Any]:
        return {"cantidad": str(self.cantidad)}


class ProductoNoEncontradoError(TienditaError):
    codigo = "producto_no_encontrado"
    http_status = status.HTTP_404_NOT_FOUND
    mensaje = "El producto no existe."


class StockInsuficienteError(TienditaError):
    """El pedido supera lo que hay en bodega.

    Es 409 y no 400: la petición está bien formada, pero choca con el estado
    actual del inventario. El frontend puede distinguir "te equivocaste al pedir"
    de "alguien se te adelantó".
    """

    codigo = "stock_insuficiente"
    http_status = status.HTTP_409_CONFLICT

    def __init__(self, producto: str, solicitado: int, disponible: int) -> None:
        self.producto = producto
        self.solicitado = solicitado
        self.disponible = disponible
        super().__init__(
            f"No alcanza el stock de «{producto}»: pediste {solicitado} y quedan {disponible}."
        )

    def detalle(self) -> dict[str, Any]:
        return {
            "producto": self.producto,
            "solicitado": self.solicitado,
            "disponible": self.disponible,
        }


class DescuentoInvalidoError(TienditaError):
    codigo = "descuento_invalido"

    def __init__(self, cupon: str, motivo: str) -> None:
        self.cupon = cupon
        self.motivo = motivo
        super().__init__(f"El cupón «{cupon}» no se puede aplicar: {motivo}.")

    def detalle(self) -> dict[str, Any]:
        return {"cupon": self.cupon, "motivo": self.motivo}


class OrdenYaPagadaError(TienditaError):
    codigo = "orden_ya_pagada"
    http_status = status.HTTP_409_CONFLICT
    mensaje = "Esta orden ya fue pagada."


class PagoRechazadoError(TienditaError):
    codigo = "pago_rechazado"
    http_status = status.HTTP_402_PAYMENT_REQUIRED

    def __init__(self, motivo: str, monto: Decimal | None = None) -> None:
        self.motivo = motivo
        self.monto = monto
        super().__init__(f"El pago fue rechazado: {motivo}.")

    def detalle(self) -> dict[str, Any]:
        return {"motivo": self.motivo}
