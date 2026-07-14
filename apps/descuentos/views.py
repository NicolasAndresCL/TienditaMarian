"""Vistas de descuentos.

Los cupones los emite la tienda. Antes bastaba `IsAuthenticated`, así que
cualquier cliente podía crearse un descuento del 99% y aplicárselo. Las
escrituras pasan a ser exclusivas del staff; la lectura queda para usuarios
autenticados, que es lo que el frontend necesita para mostrar las promociones
vigentes.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import IsAuthenticated

from apps.descuentos.models import Descuento
from apps.descuentos.serializers import DescuentoSerializer
from core.api.base_views import BaseListCreateView, BaseRetrieveUpdateDestroyView
from core.api.permissions import EsAdminOSoloLectura


@extend_schema_view(
    get=extend_schema(
        summary="Listar descuentos",
        description="Descuentos registrados.",
        tags=["Descuentos"],
        operation_id="listarDescuentos",
    ),
    post=extend_schema(
        summary="Crear descuento",
        description="Solo la administración de la tienda emite cupones.",
        tags=["Descuentos"],
        operation_id="crearDescuento",
    ),
)
class DescuentoListCreateView(BaseListCreateView):
    queryset = Descuento.objects.all()
    serializer_class = DescuentoSerializer
    permission_classes = [IsAuthenticated, EsAdminOSoloLectura]


@extend_schema_view(
    get=extend_schema(
        summary="Obtener descuento", tags=["Descuentos"], operation_id="obtenerDescuento"
    ),
    put=extend_schema(
        summary="Actualizar descuento", tags=["Descuentos"], operation_id="actualizarDescuento"
    ),
    patch=extend_schema(
        summary="Actualizar descuento parcialmente",
        tags=["Descuentos"],
        operation_id="actualizarDescuentoParcial",
    ),
    delete=extend_schema(
        summary="Eliminar descuento", tags=["Descuentos"], operation_id="eliminarDescuento"
    ),
)
class DescuentoDetailView(BaseRetrieveUpdateDestroyView):
    queryset = Descuento.objects.all()
    serializer_class = DescuentoSerializer
    permission_classes = [IsAuthenticated, EsAdminOSoloLectura]
