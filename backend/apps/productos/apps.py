from django.apps import AppConfig


class ProductosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.productos'
    verbose_name = 'Productos'

    def ready(self):
        # `STOCK_AGOTADO` se emitía sin un solo suscriptor. El aviso de venta
        # perdida vive aquí, en la app dueña del inventario, y no en la de
        # órdenes: el hecho es del stock, no de la orden (que ni siquiera llega
        # a existir).
        from apps.productos.subscribers import registrar_suscriptores

        registrar_suscriptores()
