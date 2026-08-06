"""Vistas del carrito y del checkout.

Las vistas ya no contienen reglas de negocio: parsean la petición, delegan en
`CarritoService` / `CheckoutService` y serializan la respuesta. Los errores de
negocio se lanzan como excepciones de dominio y `core.api.exception_handler` los
traduce a HTTP, así que aquí no queda ni un `Response({'detail': ...}, 400)`
armado a mano.

Con eso desaparecen los 500 que producían `data['producto_id']` (KeyError si el
campo no venía) e `int(request.data.get('cantidad'))` (ValueError si venía
"abc").
"""

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.carrito.serializers import CarritoSerializer, ItemCarritoSerializer
from apps.carrito.services import CarritoService, CheckoutService
from apps.orden.serializers import OrdenSerializer


class AgregarItemSerializer(serializers.Serializer):
    """Documenta y valida la forma del cuerpo de la petición."""

    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(required=False, default=1, min_value=1)


class QuitarItemSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()


class CheckoutSerializer(serializers.Serializer):
    cupon = serializers.CharField(required=False, allow_blank=True)


class CarritoBaseView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @property
    def servicio(self) -> CarritoService:
        return CarritoService(self.request.user)


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
        return Response(self.get_serializer(self.servicio.carrito).data)


@extend_schema_view(
    post=extend_schema(
        operation_id="carrito.add",
        tags=["Carrito"],
        summary="Agregar producto al carrito",
        request=AgregarItemSerializer,
        responses={
            200: ItemCarritoSerializer,
            404: OpenApiResponse(description="El producto no existe."),
            409: OpenApiResponse(description="Stock insuficiente."),
        },
        examples=[OpenApiExample("Agregar", value={"producto_id": 1, "cantidad": 2})],
    )
)
class AddItemCarritoView(CarritoBaseView):
    serializer_class = AgregarItemSerializer

    def post(self, request: Request) -> Response:
        item = self.servicio.agregar(
            request.data.get("producto_id"), request.data.get("cantidad", 1)
        )
        return Response(ItemCarritoSerializer(item).data, status=status.HTTP_200_OK)


@extend_schema_view(
    delete=extend_schema(
        operation_id="carrito.remove",
        tags=["Carrito"],
        summary="Quitar producto del carrito",
        request=QuitarItemSerializer,
        responses={
            204: OpenApiResponse(description="Producto eliminado."),
            404: OpenApiResponse(description="No está en tu carrito."),
        },
    )
)
class RemoveItemCarritoView(CarritoBaseView):
    serializer_class = QuitarItemSerializer

    def delete(self, request: Request) -> Response:
        self.servicio.quitar(request.data.get("producto_id"))
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    patch=extend_schema(
        operation_id="carrito.updateCantidad",
        tags=["Carrito"],
        summary="Actualizar la cantidad de un producto",
        request=AgregarItemSerializer,
        responses={
            200: ItemCarritoSerializer,
            400: OpenApiResponse(description="Cantidad inválida."),
            409: OpenApiResponse(description="Stock insuficiente."),
        },
    )
)
class UpdateCantidadCarritoView(CarritoBaseView):
    serializer_class = AgregarItemSerializer

    def patch(self, request: Request) -> Response:
        item = self.servicio.actualizar_cantidad(
            request.data.get("producto_id"), request.data.get("cantidad")
        )
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
    serializer_class = OrdenSerializer

    def post(self, request: Request) -> Response:
        cupon = request.data.get("cupon") or None
        orden = CheckoutService(request.user).ejecutar(cupon=cupon)

        return Response(self.get_serializer(orden).data, status=status.HTTP_201_CREATED)
