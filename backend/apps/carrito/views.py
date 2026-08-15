"""Vistas del carrito y del checkout.

Las vistas ya no contienen reglas de negocio: parsean la petición, delegan en
`CarritoService` / `CheckoutService` y serializan la respuesta. Los errores de
negocio se lanzan como excepciones de dominio y `core.api.exception_handler` los
traduce a HTTP, así que aquí no queda ni un `Response({'detail': ...}, 400)`
armado a mano.

Con eso desaparecen los 500 que producían `data['producto_id']` (KeyError si el
campo no venía) e `int(request.data.get('cantidad'))` (ValueError si venía
"abc").

La validación del cuerpo la hace el serializer declarado, no la vista leyendo
`request.data.get(...)`: hasta ahora el `serializer_class` estaba puesto pero
nunca se invocaba, así que solo decoraba el esquema de OpenAPI mientras el
servicio reparseaba a mano lo mismo que el serializer ya declaraba.
"""

from typing import Any

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.carrito.serializers import (
    ActualizarCantidadSerializer,
    AgregarItemSerializer,
    CarritoSerializer,
    CheckoutSerializer,
    ItemCarritoSerializer,
    QuitarItemSerializer,
)
from apps.carrito.services import CarritoService, CheckoutService
from apps.orden.serializers import OrdenSerializer


class CarritoBaseView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @property
    def servicio(self) -> CarritoService:
        return CarritoService(self.request.user)

    def datos_validados(self) -> dict[str, Any]:
        """Valida el cuerpo con el serializer de la vista y lo devuelve limpio.

        `raise_exception=True` deja que el ValidationError llegue a
        `core.api.exception_handler`, que ya lo envuelve en el mismo formato
        `{error: {codigo, mensaje, detalle}}` que los errores de dominio: el
        frontend no necesita distinguir de dónde viene el fallo.
        """
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data


@extend_schema_view(
    get=extend_schema(
        operation_id="carrito.detail",
        tags=["Carrito"],
        summary="Obtener mi carrito",
        responses={200: CarritoSerializer},
    )
)
class CarritoDetailView(CarritoBaseView):
    serializer_class = CarritoSerializer

    def get(self, request: Request) -> Response:
        # `carrito_para_mostrar()` y no `carrito`: trae ítems y productos en el
        # mismo viaje, que es lo que evita el N+1 al serializar.
        return Response(self.get_serializer(self.servicio.carrito_para_mostrar()).data)


@extend_schema_view(
    post=extend_schema(
        operation_id="carrito.add",
        tags=["Carrito"],
        summary="Agregar producto al carrito",
        request=AgregarItemSerializer,
        responses={
            200: ItemCarritoSerializer,
            400: OpenApiResponse(description="Cuerpo inválido: falta `producto_id` o la cantidad no es un entero ≥ 1."),
            404: OpenApiResponse(description="El producto no existe."),
            409: OpenApiResponse(description="Stock insuficiente."),
        },
        examples=[OpenApiExample("Agregar", value={"producto_id": 1, "cantidad": 2})],
    )
)
class AddItemCarritoView(CarritoBaseView):
    serializer_class = AgregarItemSerializer

    def post(self, request: Request) -> Response:
        datos = self.datos_validados()
        item = self.servicio.agregar(datos["producto_id"], datos["cantidad"])
        return Response(ItemCarritoSerializer(item).data, status=status.HTTP_200_OK)


@extend_schema_view(
    delete=extend_schema(
        operation_id="carrito.remove",
        tags=["Carrito"],
        summary="Quitar producto del carrito",
        request=QuitarItemSerializer,
        responses={
            204: OpenApiResponse(description="Producto eliminado."),
            400: OpenApiResponse(description="Falta `producto_id` o no es un entero."),
            404: OpenApiResponse(description="No está en tu carrito."),
        },
    )
)
class RemoveItemCarritoView(CarritoBaseView):
    serializer_class = QuitarItemSerializer

    def delete(self, request: Request) -> Response:
        self.servicio.quitar(self.datos_validados()["producto_id"])
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    patch=extend_schema(
        operation_id="carrito.updateCantidad",
        tags=["Carrito"],
        summary="Actualizar la cantidad de un producto",
        request=ActualizarCantidadSerializer,
        responses={
            200: ItemCarritoSerializer,
            400: OpenApiResponse(description="Falta `producto_id` o `cantidad`, o la cantidad no es un entero ≥ 1."),
            404: OpenApiResponse(description="Ese producto no está en tu carrito."),
            409: OpenApiResponse(description="Stock insuficiente."),
        },
    )
)
class UpdateCantidadCarritoView(CarritoBaseView):
    # Serializer propio, no el de agregar: aquí `cantidad` es obligatoria. Con el
    # `default=1` del otro, un PATCH sin cantidad dejaba el ítem en 1 unidad en
    # silencio en vez de rechazar la petición.
    serializer_class = ActualizarCantidadSerializer

    def patch(self, request: Request) -> Response:
        datos = self.datos_validados()
        item = self.servicio.actualizar_cantidad(datos["producto_id"], datos["cantidad"])
        return Response(ItemCarritoSerializer(item).data)


@extend_schema_view(
    delete=extend_schema(
        operation_id="carrito.clear",
        tags=["Carrito"],
        summary="Vaciar el carrito",
        responses={204: OpenApiResponse(description="Carrito vaciado.")},
    )
)
class ClearCarritoView(CarritoBaseView):
    serializer_class = None

    def delete(self, request: Request) -> Response:
        self.servicio.vaciar()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    post=extend_schema(
        operation_id="carrito.checkout",
        tags=["Carrito"],
        summary="Confirmar la compra",
        description=(
            "Valida el stock, lo descuenta, aplica el cupón si viene, crea la orden y "
            "deja el envío pendiente. Todo dentro de una única transacción."
        ),
        request=CheckoutSerializer,
        responses={
            201: OrdenSerializer,
            400: OpenApiResponse(description="Carrito vacío o cupón inválido."),
            409: OpenApiResponse(description="Stock insuficiente."),
        },
    )
)
class CheckoutView(CarritoBaseView):
    # `serializer_class` describe la RESPUESTA (la orden creada), así que aquí el
    # cuerpo se valida con `CheckoutSerializer` explícitamente en vez de con
    # `datos_validados()`, que usaría el de la respuesta.
    serializer_class = OrdenSerializer

    def post(self, request: Request) -> Response:
        entrada = CheckoutSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        # Un cupón vacío es "sin cupón", no un cupón llamado "".
        cupon = entrada.validated_data.get("cupon") or None
        orden = CheckoutService(request.user).ejecutar(cupon=cupon)

        return Response(self.get_serializer(orden).data, status=status.HTTP_201_CREATED)
