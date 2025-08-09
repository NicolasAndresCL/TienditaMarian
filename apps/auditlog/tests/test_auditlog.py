from django.test import TestCase
from apps.productos.models import Producto
from apps.auditlog.models import AuditLog

class AuditLogTest(TestCase):
    def test_create_audit_entry(self):
        producto = Producto.objects.create(
            nombre="Test", 
            precio=100, 
            stock=10,
            descripcion="Test"
        )
        producto.full_clean()
        producto.save()
        log = AuditLog.objects.filter(model_name="Producto", object_id=producto.id).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.action, "create")
