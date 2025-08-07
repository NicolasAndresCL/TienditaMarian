from rest_framework import status, mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView
from django.shortcuts import get_object_or_404
from django.db import transaction

from carrito.models import Carrito, ItemCarrito
from productos.models import Producto
from orden.models import Orden, ItemOrden

from carrito.serializers import CarritoSerializer, ItemCarritoSerializer
from orden.serializers import OrdenSerializer

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiExample, OpenApiResponse

# 📦 Utils
def get_or_create_carrito(usuario):
    return Carrito.objects.get_or_create(usuario=usuario)[0]

# 🛒 Listar carrito
@extend_schema_view(
    get=extend_schema(
        operation_id="carrito.list",
        tags=["Carrito"],
        summary="Obtener carrito actual",
        description="Devuelve el carrito de compras del usuario autenticado.",
        responses={200: CarritoSerializer}
    )
)
class CarritoDetailView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CarritoSerializer

    def get(self, request):
        carrito = get_or_create_carrito(request.user)
        serializer = self.get_serializer(carrito)
        return Response(serializer.data)


# ➕ Agregar producto
@extend_schema_view(
    post=extend_schema(
        operation_id="carrito.add",
        tags=["Carrito"],
        summary="Agregar producto al carrito",
        request=ItemCarritoSerializer,
        responses={200: OpenApiResponse(description="Producto agregado.")},
        examples=[
            OpenApiExample("Agregar", value={"producto_id": 1, "cantidad": 2})
        ]
    )
)
class AddItemCarritoView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ItemCarritoSerializer

    def post(self, request):
        data = request.data
        carrito = get_or_create_carrito(request.user)
        producto = get_object_or_404(Producto, id=data['producto_id'])
        item, created = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto)
        item.cantidad = item.cantidad + data.get('cantidad', 1) if not created else data.get('cantidad', 1)
        item.save()
        return Response({'detail': 'Producto agregado.'}, status=status.HTTP_200_OK)


# ➖ Eliminar producto
@extend_schema_view(
    delete=extend_schema(
        operation_id="carrito.remove",
        tags=["Carrito"],
        summary="Eliminar producto del carrito",
        request=ItemCarritoSerializer,
        responses={
            200: OpenApiResponse(description="Eliminado."),
            404: OpenApiResponse(description="No encontrado.")
        }
    )
)
class RemoveItemCarritoView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ItemCarritoSerializer

    def delete(self, request):
        producto_id = request.data.get('producto_id')
        carrito = get_or_create_carrito(request.user)
        item = ItemCarrito.objects.filter(carrito=carrito, producto_id=producto_id).first()
        if item:
            item.delete()
            return Response({'detail': 'Producto eliminado.'})
        return Response({'detail': 'Producto no encontrado.'}, status=status.HTTP_404_NOT_FOUND)


# 🔄 Actualizar cantidad
@extend_schema_view(
    patch=extend_schema(
        operation_id="carrito.updateCantidad",
        tags=["Carrito"],
        summary="Actualizar cantidad",
        request=ItemCarritoSerializer,
        responses={
            200: OpenApiResponse(description="Cantidad actualizada."),
            404: OpenApiResponse(description="Producto no encontrado.")
        }
    )
)
class UpdateCantidadCarritoView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ItemCarritoSerializer

    def patch(self, request):
        producto_id = request.data.get('producto_id')
        cantidad = int(request.data.get('cantidad', 1))
        carrito = get_or_create_carrito(request.user)
        item = ItemCarrito.objects.filter(carrito=carrito, producto_id=producto_id).first()
        if item:
            item.cantidad = cantidad
            item.save()
            return Response({'detail': 'Cantidad actualizada.'})
        return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)


# 🧼 Vaciar carrito
@extend_schema_view(
    delete=extend_schema(
        operation_id="carrito.clear",
        tags=["Carrito"],
        summary="Vaciar carrito",
        responses={200: OpenApiResponse(description="Carrito vaciado.")}
    )
)
class ClearCarritoView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        carrito = get_or_create_carrito(request.user)
        carrito.items.all().delete()
        return Response({'detail': 'Carrito vaciado.'})


# 📦 Checkout
@extend_schema_view(
    post=extend_schema(
        operation_id="carrito.checkout",
        tags=["Carrito"],
        summary="Checkout y creación de orden",
        responses={
            201: OpenApiResponse(response=OrdenSerializer, description="Orden creada."),
            400: OpenApiResponse(description="Carrito vacío.")
        }
    )
)
class CheckoutView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrdenSerializer

    @transaction.atomic
    def post(self, request):
        carrito = get_object_or_404(Carrito, usuario=request.user)
        if not carrito.items.exists():
            return Response({'detail': 'Carrito vacío.'}, status=status.HTTP_400_BAD_REQUEST)

        orden = Orden.objects.create(
            usuario=request.user,
            total=sum(item.producto.precio * item.cantidad for item in carrito.items.all())
        )

        for item in carrito.items.all():
            ItemOrden.objects.create(
                orden=orden,
                producto=item.producto,
                cantidad=item.cantidad,
                precio=item.producto.precio
            )
        carrito.items.all().delete()
        serializer = self.get_serializer(orden)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
