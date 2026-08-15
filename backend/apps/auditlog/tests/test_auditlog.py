"""Tests de la bitácora de auditoría.

Este módulo existía pero **nunca llegó a ejecutarse**: la carpeta `tests/` no
tenía `__init__.py` y, además, `apps.auditlog` no estaba en el INSTALLED_APPS de
la configuración de tests. Al arreglar ambas cosas afloraron dos bugs reales,
que estos tests fijan para que no vuelvan.
"""

from datetime import date
from decimal import Decimal

import pytest

from apps.auditlog.models import AuditLog
from apps.auditlog.utils import serializar_instancia
from apps.descuentos.models import Descuento


@pytest.mark.django_db
def test_crear_producto_deja_entrada_de_auditoria(producto):
    log = AuditLog.objects.filter(model_name="Producto", object_id=str(producto.pk)).first()

    assert log is not None
    assert log.action == "create"


@pytest.mark.django_db
def test_modelo_con_datefield_se_audita_sin_reventar():
    """Regresión: `serialize_value` no manejaba `date` y lanzaba TypeError.

    `Descuento` tiene dos DateField, así que crearlo tumbaba la petición con un
    500 en cuanto la auditoría estaba activa.
    """
    descuento = Descuento.objects.create(
        nombre="Lanzamiento",
        tipo="porcentaje",
        valor=Decimal("15.00"),
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
    )

    log = AuditLog.objects.filter(model_name="Descuento", object_id=str(descuento.pk)).first()
    assert log is not None
    assert log.changes["fecha_inicio"] == "2026-01-01"


@pytest.mark.django_db
def test_el_usuario_nunca_se_audita(usuario):
    """El `post_save` global auditaba hasta el User; ahora solo va la lista blanca."""
    assert not AuditLog.objects.filter(model_name="User").exists()


@pytest.mark.django_db
def test_la_serializacion_descarta_campos_sensibles(usuario):
    """Aunque a alguien se le ocurra auditar el User, el hash no puede filtrarse."""
    datos = serializar_instancia(usuario)

    assert "password" not in datos
    assert usuario.password not in datos.values()


@pytest.mark.django_db
def test_eliminar_producto_deja_entrada_delete(producto):
    pk = producto.pk
    producto.delete()

    assert AuditLog.objects.filter(
        model_name="Producto", object_id=str(pk), action="delete"
    ).exists()


@pytest.mark.django_db
def test_la_orden_se_audita_con_el_detalle_de_lo_vendido(usuario, producto):
    """Auditar una orden es registrar QUÉ se vendió, no solo cuánto se cobró.

    `model_to_dict` solo trae los campos propios de la fila, así que la orden
    quedaba como un total suelto. `ItemOrden` estaba en la lista blanca para
    cubrir ese hueco, pero el checkout los crea con `bulk_create`, que no dispara
    señales: no se auditaba ni uno.
    """
    from apps.orden.models import ItemOrden, Orden

    orden = Orden.objects.create(usuario=usuario, total=Decimal("6000.00"))
    ItemOrden.objects.bulk_create(
        [ItemOrden(orden=orden, producto=producto, cantidad=2, precio=producto.precio)]
    )

    # Un cambio posterior (aquí, marcarla pagada) es cuando el detalle importa.
    orden.pagado = True
    orden.save(update_fields=["pagado"])

    log = (
        AuditLog.objects.filter(model_name="Orden", object_id=str(orden.pk), action="update")
        .order_by("-id")
        .first()
    )

    assert log is not None
    assert log.changes["items"] == [
        {"producto": str(producto), "cantidad": 2, "precio": str(producto.precio)}
    ]


@pytest.mark.django_db
def test_los_items_de_orden_ya_no_prometen_auditoria(usuario, producto):
    """`bulk_create` no dispara señales: tenerlos en la lista blanca mentía.

    No se pierde trazabilidad porque un ItemOrden es inmutable —nace con su
    precio congelado y no se toca nunca más—, así que la tabla es su propio
    registro histórico.
    """
    from apps.auditlog.signals import MODELOS_AUDITADOS

    assert "orden.ItemOrden" not in MODELOS_AUDITADOS


@pytest.mark.django_db
def test_una_auditoria_caida_no_tumba_la_operacion(monkeypatch, producto):
    """La capa de auditoría nunca lanza: no puede hacer caer una venta (skill §2.2)."""
    from apps.auditlog import utils

    def explota(_instance):
        raise RuntimeError("base de datos de auditoría caída")

    monkeypatch.setattr(utils, "serializar_instancia", explota)

    producto.nombre = "Nombre nuevo"
    producto.save()  # no debe lanzar

    producto.refresh_from_db()
    assert producto.nombre == "Nombre nuevo"
