"""Pago con Webpay Plus: el flujo de dos pasos.

La pasarela se inyecta (`PasarelaRedirigida` falsa) para probar la lógica sin
salir a la red, igual que el resto del proyecto inyecta el despachador de
eventos. Que el SDK hable de verdad con Transbank es otro asunto y se verifica a
mano contra su ambiente de integración.
"""

from decimal import Decimal

import pytest

from apps.orden.models import Orden
from apps.pagos.models import Pago
from apps.pagos.services import IntencionDePago, PasarelaRedirigida, WebpayService
from core.exceptions import OrdenYaPagadaError, PagoRechazadoError

TOKEN = "token-de-prueba-01ab"


class PasarelaFalsa(PasarelaRedirigida):
    """Doble de Webpay: registra lo que se le pide y responde lo que se le diga."""

    nombre = "webpay"

    def __init__(self, respuesta: dict | None = None) -> None:
        self.respuesta = respuesta or {"response_code": 0, "status": "AUTHORIZED"}
        self.iniciada = None
        self.confirmaciones = 0

    def iniciar(self, buy_order, session_id, monto, url_retorno):
        self.iniciada = {
            "buy_order": buy_order,
            "session_id": session_id,
            "monto": monto,
            "url_retorno": url_retorno,
        }
        return IntencionDePago(url="https://webpay3gint.transbank.cl/init", token=TOKEN)

    def confirmar(self, token):
        self.confirmaciones += 1
        return self.respuesta


@pytest.fixture
def orden(db, usuario) -> Orden:
    return Orden.objects.create(usuario=usuario, total=Decimal("6000.00"))


# ------------------------------------------------------------------ iniciar


@pytest.mark.django_db
def test_iniciar_deja_un_pago_pendiente_con_el_token(orden):
    pasarela = PasarelaFalsa()

    intencion = WebpayService(pasarela=pasarela).iniciar(orden)

    assert intencion.url.startswith("https://")
    pago = Pago.objects.get(orden=orden)
    assert pago.estado == "pendiente"
    # El token es lo único que permite reconocer la vuelta, que llega sin sesión.
    assert pago.transaccion_id == intencion.token


@pytest.mark.django_db
def test_el_monto_va_en_pesos_enteros(orden):
    """El peso chileno no tiene decimales y Webpay rechaza un monto con coma."""
    pasarela = PasarelaFalsa()

    WebpayService(pasarela=pasarela).iniciar(orden)

    assert pasarela.iniciada["monto"] == 6000
    assert isinstance(pasarela.iniciada["monto"], int)


@pytest.mark.django_db
def test_cada_intento_usa_un_buy_order_distinto(orden, usuario):
    """Transbank rechaza un `buy_order` repetido.

    Si la clienta reintenta tras un rechazo, el segundo intento no puede reusar
    el identificador del primero.
    """
    otra = Orden.objects.create(usuario=usuario, total=Decimal("1000.00"))
    pasarela = PasarelaFalsa()
    servicio = WebpayService(pasarela=pasarela)

    servicio.iniciar(orden)
    primero = pasarela.iniciada["buy_order"]
    servicio.iniciar(otra)
    segundo = pasarela.iniciada["buy_order"]

    assert primero != segundo
    # Máximo que admite Transbank.
    assert len(primero) <= 26


@pytest.mark.django_db
def test_no_se_inicia_el_pago_de_una_orden_ya_pagada(orden):
    orden.pagado = True
    orden.save(update_fields=["pagado"])

    with pytest.raises(OrdenYaPagadaError):
        WebpayService(pasarela=PasarelaFalsa()).iniciar(orden)


# ----------------------------------------------------------------- confirmar


@pytest.mark.django_db
def test_confirmar_una_transaccion_autorizada_marca_la_orden(orden):
    pasarela = PasarelaFalsa()
    servicio = WebpayService(pasarela=pasarela)
    servicio.iniciar(orden)

    pago = servicio.confirmar(TOKEN)

    assert pago.estado == "pagado"
    orden.refresh_from_db()
    assert orden.pagado


@pytest.mark.django_db
@pytest.mark.parametrize(
    "respuesta",
    [
        {"response_code": -1, "status": "FAILED"},
        # Las dos condiciones son necesarias: un response_code 0 con un status
        # que no sea AUTHORIZED NO es una transacción exitosa.
        {"response_code": 0, "status": "REVERSED"},
        {"response_code": -1, "status": "AUTHORIZED"},
    ],
)
def test_una_transaccion_no_autorizada_no_marca_la_orden(orden, respuesta):
    pasarela = PasarelaFalsa(respuesta=respuesta)
    servicio = WebpayService(pasarela=pasarela)
    servicio.iniciar(orden)

    with pytest.raises(PagoRechazadoError):
        servicio.confirmar(TOKEN)

    orden.refresh_from_db()
    assert not orden.pagado
    assert Pago.objects.get(orden=orden).estado == "fallido"


@pytest.mark.django_db
def test_confirmar_dos_veces_no_cobra_dos_veces(orden):
    """La clienta puede recargar la página de retorno, o Transbank reintentar."""
    pasarela = PasarelaFalsa()
    servicio = WebpayService(pasarela=pasarela)
    servicio.iniciar(orden)

    servicio.confirmar(TOKEN)
    servicio.confirmar(TOKEN)

    # La segunda vez ni siquiera se le pregunta a Transbank.
    assert pasarela.confirmaciones == 1
    assert Pago.objects.filter(orden=orden).count() == 1


@pytest.mark.django_db
def test_un_token_desconocido_no_confirma_nada(db):
    with pytest.raises(Pago.DoesNotExist):
        WebpayService(pasarela=PasarelaFalsa()).confirmar("token-inventado")


@pytest.mark.django_db
def test_confirmar_avisa_a_la_clienta(orden, mailoutbox, django_capture_on_commit_callbacks):
    pasarela = PasarelaFalsa()
    servicio = WebpayService(pasarela=pasarela)
    servicio.iniciar(orden)

    with django_capture_on_commit_callbacks(execute=True):
        servicio.confirmar(TOKEN)

    assert len(mailoutbox) == 1
    assert "pago" in mailoutbox[0].subject.lower()


# --------------------------------------------------------------- el retorno
#
# El endpoint de vuelta es PÚBLICO a propósito: Transbank devuelve el control con
# un POST desde su dominio, y una cookie SameSite=Lax no viaja en un POST
# cross-site. Si exigiera sesión, ningún pago podría confirmarse nunca.


@pytest.mark.django_db
def test_el_retorno_no_exige_sesion(api_client, orden, monkeypatch):
    pasarela = PasarelaFalsa()
    WebpayService(pasarela=pasarela).iniciar(orden)

    import apps.pagos.views as vistas

    monkeypatch.setattr(
        vistas, "WebpayService", lambda *a, **k: WebpayService(pasarela=pasarela)
    )

    # `api_client` no está autenticado: es exactamente lo que llega de Transbank.
    respuesta = api_client.post("/api/v1/pagos/webpay/retorno/", {"token_ws": TOKEN})

    assert respuesta.status_code == 302
    assert "pago=pagado" in respuesta["Location"]
    orden.refresh_from_db()
    assert orden.pagado


@pytest.mark.django_db
def test_si_la_clienta_anula_el_pago_no_se_rompe_nada(api_client, orden):
    """Al anular en el formulario de Transbank no llega `token_ws`, sino TBK_TOKEN.

    No es un error: es un "no quiso pagar".
    """
    respuesta = api_client.post("/api/v1/pagos/webpay/retorno/", {"TBK_TOKEN": "abc"})

    assert respuesta.status_code == 302
    assert "pago=anulado" in respuesta["Location"]
    orden.refresh_from_db()
    assert not orden.pagado


@pytest.mark.django_db
def test_un_token_desconocido_en_el_retorno_redirige_sin_reventar(api_client):
    respuesta = api_client.post("/api/v1/pagos/webpay/retorno/", {"token_ws": "inventado"})

    assert respuesta.status_code == 302
    assert "pago=desconocido" in respuesta["Location"]
