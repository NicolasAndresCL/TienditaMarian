from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import get_object_or_404
from django.db import transaction

from carrito.models import Carrito, ItemCarrito
from productos.models import Producto
from carrito.serializers import CarritoSerializer, ItemCarritoSerializer
from orden.serializers import OrdenSerializer, ItemOrdenSerializer
from orden.models import Orden, ItemOrden

from drf_spectacular.utils import (
    extend_schema, extend_schema_view,
    OpenApiExample, OpenApiResponse
)


@extend_schema_view(
    list=extend_schema(tags=["Carrito"]),
)
class CarritoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CarritoSerializer

    @extend_schema(
        summary="Obtener el carrito actual",
        responses={200: CarritoSerializer},
        description="Devuelve el carrito de compras del usuario autenticado."
    )
    def list(self, request):
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        serializer = CarritoSerializer(carrito)
        return Response(serializer.data)

    @extend_schema(
        tags=["Carrito"],
        summary="Agregar producto al carrito",
        request=ItemCarritoSerializer,
        responses={200: OpenApiResponse(description="Producto agregado al carrito.")},
        examples=[OpenApiExample("Agregar", value={"producto_id": 1, "cantidad": 2}, request_only=True)]
    )
    def add(self, request):
        producto_id = request.data.get('producto_id')
        cantidad = int(request.data.get('cantidad', 1))
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        producto = get_object_or_404(Producto, id=producto_id)
        item, created = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto)
        item.cantidad = item.cantidad + cantidad if not created else cantidad
        item.save()
        return Response({'detail': 'Producto agregado al carrito.'}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Carrito"],
        summary="Eliminar producto del carrito",
        request=ItemCarritoSerializer,
        responses={
            200: OpenApiResponse(description="Producto eliminado del carrito."),
            404: OpenApiResponse(description="Producto no encontrado en el carrito.")
        }
    )
    def remove(self, request):
        producto_id = request.data.get('producto_id')
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        item = ItemCarrito.objects.filter(carrito=carrito, producto_id=producto_id).first()
        if item:
            item.delete()
            return Response({'detail': 'Producto eliminado del carrito.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Producto no encontrado en el carrito.'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Carrito"],
        summary="Vaciar el carrito",
        responses={200: OpenApiResponse(description="Carrito vaciado.")}
    )
    def clear(self, request):
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        carrito.items.all().delete()
        return Response({'detail': 'Carrito vaciado.'}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Carrito"],
    summary="Actualizar cantidad de un producto en el carrito",
    request=ItemCarritoSerializer,
    responses={
        200: OpenApiResponse(description="Cantidad actualizada correctamente."),
        404: OpenApiResponse(description="Producto no encontrado en el carrito.")
    }
)
class UpdateCantidadCarritoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        producto_id = request.data.get('producto_id')
        cantidad = int(request.data.get('cantidad', 1))
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        item = ItemCarrito.objects.filter(carrito=carrito, producto_id=producto_id).first()
        if item:
            item.cantidad = cantidad
            item.save()
            return Response({'detail': 'Cantidad actualizada correctamente.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Producto no encontrado en el carrito.'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=["Carrito"],
    summary="Checkout: crear orden desde el carrito",
    responses={
        201: OpenApiResponse(response=OrdenSerializer, description="Orden creada con éxito."),
        400: OpenApiResponse(description="El carrito está vacío.")
    }
)
class CheckoutViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrdenSerializer

    @transaction.atomic
    def create(self, request):
        carrito = get_object_or_404(Carrito, usuario=request.user)
        if not carrito.items.exists():
            return Response({'detail': 'El carrito está vacío.'}, status=status.HTTP_400_BAD_REQUEST)

        total = sum(item.producto.precio * item.cantidad for item in carrito.items.all())
        orden = Orden.objects.create(usuario=request.user, total=total)

        for item in carrito.items.all():
            ItemOrden.objects.create(
                orden=orden,
                producto=item.producto,
                cantidad=item.cantidad,
                precio=item.producto.precio
            )

        carrito.items.all().delete()
        serializer = OrdenSerializer(orden)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
