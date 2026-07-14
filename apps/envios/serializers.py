from rest_framework import serializers

from apps.envios.models import Envio
from apps.orden.models import Orden


class EnvioSerializer(serializers.ModelSerializer):
    """Serializer de envíos.

    Antes usaba `fields = '__all__'`, así que `usuario` y `estado` llegaban desde
    el cuerpo de la petición: se podía registrar un envío a nombre de otra persona
    o declarar el propio pedido como "entregado".

    Ahora `usuario` lo fija la vista desde `request.user`, y `estado` y
    `tracking_id` son de la tienda: un cliente no decide que su paquete ya llegó.
    """

    class Meta:
        model = Envio
        fields = [
            "id",
            "orden",
            "direccion",
            "ciudad",
            "codigo_postal",
            "estado",
            "tracking_id",
            "fecha_envio",
        ]
        read_only_fields = ["id", "fecha_envio"]

    def get_fields(self):
        campos = super().get_fields()
        peticion = self.context.get("request")

        # El estado y el seguimiento los administra la tienda: para el cliente son
        # de solo lectura; para el staff, editables.
        if not (peticion and peticion.user.is_staff):
            campos["estado"].read_only = True
            campos["tracking_id"].read_only = True

        return campos

    def validate_orden(self, orden: Orden) -> Orden:
        """No se puede colgar un envío de la orden de otra persona."""
        peticion = self.context.get("request")
        if peticion and not peticion.user.is_staff and orden.usuario_id != peticion.user.id:
            raise serializers.ValidationError("Esa orden no es tuya.")
        return orden
