from rest_framework.pagination import PageNumberPagination
from productos.carrito_models import Carrito, ItemCarrito, Orden, ItemOrden
from productos.serializers.carrito_serializers import CarritoSerializer, ItemCarritoSerializer, OrdenSerializer
from productos.models import Producto
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse, OpenApiExample


@extend_schema_view(
    get=extend_schema(
        summary="Historial de órdenes del usuario (paginado)",
        responses={200: OrdenSerializer(many=True)},
        description="Devuelve las órdenes del usuario autenticado, paginadas. Usa ?page=1 para navegar."
    )
)
class OrdenListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    def get(self, request):
        ordenes = Orden.objects.filter(usuario=request.user)
        # Filtros opcionales
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        pagado = request.query_params.get('pagado')
        if fecha_inicio:
            ordenes = ordenes.filter(creado__gte=fecha_inicio)
        if fecha_fin:
            ordenes = ordenes.filter(creado__lte=fecha_fin)
        if pagado is not None:
            if pagado.lower() in ['true', '1']:
                ordenes = ordenes.filter(pagado=True)
            elif pagado.lower() in ['false', '0']:
                ordenes = ordenes.filter(pagado=False)
        ordenes = ordenes.order_by('-creado')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(ordenes, request)
        serializer = OrdenSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

@extend_schema_view(
    get=extend_schema(
        summary="Detalle de una orden",
        responses={200: OrdenSerializer},
        description="Devuelve el detalle de una orden específica del usuario."
    )
)
class OrdenDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        orden = get_object_or_404(Orden, pk=pk, usuario=request.user)
        serializer = OrdenSerializer(orden)
        return Response(serializer.data)

@extend_schema(
    summary="Actualizar cantidad de un producto en el carrito",
    request=ItemCarritoSerializer,
    responses={
        200: OpenApiResponse(
            description="Cantidad actualizada correctamente.",
            examples=[
                OpenApiExample(
                    'Cantidad actualizada',
                    value={"detail": "Cantidad actualizada correctamente."},
                    response_only=True
                )
            ]
        ),
        404: OpenApiResponse(
            description="Producto no encontrado en el carrito.",
            examples=[
                OpenApiExample(
                    'Producto no encontrado',
                    value={"detail": "Producto no encontrado en el carrito."},
                    response_only=True
                )
            ]
        )
    },
    description="Actualiza la cantidad de un producto en el carrito del usuario.",
    examples=[
        OpenApiExample(
            'Actualizar cantidad',
            value={"producto_id": 1, "cantidad": 5},
            request_only=True
        )
    ]
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

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from productos.carrito_models import Carrito, ItemCarrito, Orden, ItemOrden
from productos.serializers.carrito_serializers import CarritoSerializer, ItemCarritoSerializer, OrdenSerializer
from productos.models import Producto
from django.shortcuts import get_object_or_404
from django.db import transaction

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, extend_schema_view


class CarritoViewSet(viewsets.ViewSet):
    """
    Endpoints para gestionar el carrito de compras del usuario autenticado.
    """
    serializer_class = CarritoSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Obtener el carrito actual",
        responses={200: CarritoSerializer},
        description="Devuelve el carrito de compras del usuario autenticado."
    )
    def list(self, request):
        """Devuelve el carrito de compras del usuario autenticado."""
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        serializer = CarritoSerializer(carrito)
        return Response(serializer.data)

    @extend_schema(
        summary="Agregar producto al carrito",
        request=ItemCarritoSerializer,
        responses={
            200: OpenApiResponse(
                description="Producto agregado al carrito.",
                examples=[
                    OpenApiExample(
                        'Producto agregado',
                        value={"detail": "Producto agregado al carrito."},
                        response_only=True
                    )
                ]
            )
        },
        description="Agrega un producto y cantidad al carrito del usuario. Si ya existe, suma la cantidad.",
        examples=[
            OpenApiExample(
                'Agregar producto',
                value={"producto_id": 1, "cantidad": 2},
                request_only=True
            )
        ]
    )
    def add(self, request):
        """Agrega un producto y cantidad al carrito del usuario."""
        producto_id = request.data.get('producto_id')
        cantidad = int(request.data.get('cantidad', 1))
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        producto = get_object_or_404(Producto, id=producto_id)
        item, created = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto)
        if not created:
            item.cantidad += cantidad
        else:
            item.cantidad = cantidad
        item.save()
        return Response({'detail': 'Producto agregado al carrito.'}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Eliminar producto del carrito",
        request=ItemCarritoSerializer,
        responses={
            200: OpenApiResponse(
                description="Producto eliminado del carrito.",
                examples=[
                    OpenApiExample(
                        'Producto eliminado',
                        value={"detail": "Producto eliminado del carrito."},
                        response_only=True
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Producto no encontrado en el carrito.",
                examples=[
                    OpenApiExample(
                        'Producto no encontrado',
                        value={"detail": "Producto no encontrado en el carrito."},
                        response_only=True
                    )
                ]
            )
        },
        description="Elimina un producto específico del carrito del usuario.",
        examples=[
            OpenApiExample(
                'Eliminar producto',
                value={"producto_id": 1},
                request_only=True
            )
        ]
    )
    def remove(self, request):
        """Elimina un producto específico del carrito del usuario."""
        producto_id = request.data.get('producto_id')
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        item = ItemCarrito.objects.filter(carrito=carrito, producto_id=producto_id).first()
        if item:
            item.delete()
            return Response({'detail': 'Producto eliminado del carrito.'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Producto no encontrado en el carrito.'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Vaciar el carrito",
        responses={
            200: OpenApiResponse(
                description="Carrito vaciado.",
                examples=[
                    OpenApiExample(
                        'Carrito vaciado',
                        value={"detail": "Carrito vaciado."},
                        response_only=True
                    )
                ]
            )
        },
        description="Elimina todos los productos del carrito del usuario."
    )
    def clear(self, request):
        """Elimina todos los productos del carrito del usuario."""
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        carrito.items.all().delete()
        return Response({'detail': 'Carrito vaciado.'}, status=status.HTTP_200_OK)


class CheckoutViewSet(viewsets.ViewSet):
    """
    Endpoint para realizar el checkout del carrito y crear una orden.
    """
    serializer_class = OrdenSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Checkout: crear orden desde el carrito",
        responses={
            201: OpenApiResponse(
                response=OrdenSerializer,
                description="Orden creada con éxito.",
                examples=[
                    OpenApiExample(
                        'Orden creada',
                        value={
                            "id": 1,
                            "usuario": 2,
                            "creado": "2025-07-16T12:00:00Z",
                            "total": "150.00",
                            "pagado": False,
                            "items": [
                                {"id": 1, "producto": {"id": 1, "nombre": "Muñeca Trapo", "precio": "50.00"}, "cantidad": 2, "precio": "50.00"},
                                {"id": 2, "producto": {"id": 2, "nombre": "Carrito Didáctico", "precio": "25.00"}, "cantidad": 2, "precio": "25.00"}
                            ]
                        },
                        response_only=True
                    )
                ]
            ),
            400: OpenApiResponse(
                description="El carrito está vacío.",
                examples=[
                    OpenApiExample(
                        'Carrito vacío',
                        value={"detail": "El carrito está vacío."},
                        response_only=True
                    )
                ]
            )
        },
        description="Crea una orden a partir del carrito del usuario autenticado y vacía el carrito."
    )
    @transaction.atomic
    def create(self, request):
        """Crea una orden a partir del carrito y vacía el carrito."""
        carrito = get_object_or_404(Carrito, usuario=request.user)
        if not carrito.items.exists():
            return Response({'detail': 'El carrito está vacío.'}, status=status.HTTP_400_BAD_REQUEST)
        total = 0
        for item in carrito.items.all():
            total += item.producto.precio * item.cantidad
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
