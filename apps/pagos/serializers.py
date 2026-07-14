from rest_framework import serializers

from apps.orden.models import Orden
from apps.pagos.models import Pago


class PagoSerializer(serializers.ModelSerializer):
    """Serializer de pagos.

    `estado` y `transaccion_id` son de solo lectura: los escribe la pasarela al
    confirmar el cobro, nunca el cliente. Con `fields = '__all__'` se podía
    mandar `{"estado": "pagado"}` y darse una orden por saldada sin pagar nada.
    """

    class Meta:
        model = Pago
        fields = ["id", "orden", "monto", "metodo", "estado", "transaccion_id", "fecha_pago"]
        read_only_fields = ["id", "estado", "transaccion_id", "fecha_pago"]

    def validate_orden(self, orden: Orden) -> Orden:
        """No se puede pagar (ni fingir que se paga) la orden de otra persona."""
        peticion = self.context.get("request")
        if peticion and not peticion.user.is_staff and orden.usuario_id != peticion.user.id:
            raise serializers.ValidationError("Esa orden no es tuya.")
        return orden
