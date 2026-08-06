from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Producto(models.Model):
    """Un producto del catálogo.

    Las reglas del inventario se defienden en tres capas, porque cada una tapa
    lo que la anterior deja pasar:

    - `PositiveIntegerField` impide el stock negativo en el formulario y el
      serializer (antes era `IntegerField`: se podía guardar stock = -5);
    - el `CheckConstraint` lo impide en la **base de datos**, que es la única
      barrera que un `queryset.update()` o una consulta cruda no pueden saltarse;
    - `StockService` valida antes de descontar, para dar un error de negocio
      entendible en vez de un IntegrityError.
    """

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    image = models.ImageField(upload_to='productos/images/', blank=True, null=True)
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    stock = models.PositiveIntegerField(default=0)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Sin un orden explícito la paginación es inestable: la misma página
        # puede devolver filas distintas entre dos peticiones.
        ordering = ['-creado']
        verbose_name_plural = 'Productos'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stock__gte=0),
                name="producto_stock_no_negativo",
            ),
            models.CheckConstraint(
                condition=models.Q(precio__gt=0),
                name="producto_precio_positivo",
            ),
        ]

    def __str__(self) -> str:
        return self.nombre

    @property
    def hay_stock(self) -> bool:
        return self.stock > 0
