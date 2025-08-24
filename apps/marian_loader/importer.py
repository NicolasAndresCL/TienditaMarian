import pandas as pd
from io import TextIOWrapper

from apps.marian_loader.constants import EXPECTED_COLUMNS, MAX_ROWS
from apps.marian_loader.exceptions import InvalidRowError
from apps.marian_loader.validators import (
    validar_columnas_presentes,
    validar_precio,
    validar_stock,
    validar_imagen,
    crear_producto_desde_datos,
)


def importar_csv(file) -> list[dict]:
    """
    Lee un CSV, valida cada fila y crea instancias de Producto.
    Retorna:
      [
        {
          'fila': int,
          'datos': dict original,
          'errores': list[str],
          'producto': Producto | None
        },
        ...
      ]
    """
    # envolver file.file para pandas
    wrapper = TextIOWrapper(file.file, encoding='utf-8')
    df = pd.read_csv(wrapper, dtype=str).fillna('')
    total_rows = len(df)
    if total_rows > MAX_ROWS:
        raise InvalidRowError(f"CSV excede límite de {MAX_ROWS} filas.")

    cols = set(col.lower() for col in df.columns)
    validar_columnas_presentes(cols)

    resultados = []
    for idx, row in df.iterrows():
        fila_num = idx + 1
        datos = {
            'nombre': row.get('nombre', '').strip(),
            'descripcion': row.get('descripcion', '').strip(),
            'image': row.get('image', '').strip(),
            'precio': row.get('precio', '').strip(),
            'stock': row.get('stock', '').strip(),
        }
        errores = []
        producto = None

        # Ejecutar validaciones
        try:
            validar_precio(datos['precio'])
        except ValueError as e:
            errores.append(str(e))

        try:
            validar_stock(datos['stock'])
        except ValueError as e:
            errores.append(str(e))

        try:
            validar_imagen(datos['image'])
        except ValueError as e:
            errores.append(str(e))

        # Crear producto si no hay errores
        if not errores:
            producto = crear_producto_desde_datos(datos)

        resultados.append({
            'fila': fila_num,
            'datos': datos,
            'errores': errores,
            'producto': producto,
        })

    return resultados
