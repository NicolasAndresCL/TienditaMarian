from datetime import datetime
import os

from apps.marian_loader.constants import REPORTS_DIR


def generar_markdown(hito, detalles: list[dict]) -> str:
    """
    Construye un reporte en Markdown con:
    - Resumen del HitoCarga
    - Tabla de errores por fila
    Guarda el archivo en REPORTS_DIR y devuelve el contenido.
    """
    lines = [
        f"# Reporte de HitoCarga #{hito.pk}",
        f"- Usuario: {hito.usuario}",
        f"- Inicio: {hito.fecha_inicio}",
        f"- Fin: {hito.fecha_fin}",
        f"- Total filas: {hito.total}",
        f"- Exitosos: {hito.exitosos}",
        f"- Fallidos: {hito.fallidos}",
        "",
        "## Errores por fila",
        "| Fila | Errores |",
        "| ---- | ------- |",
    ]

    for d in detalles:
        if d['errores']:
            joined = "<br>".join(d['errores'])
            lines.append(f"| {d['fila']} | {joined} |")

    markdown = "\n".join(lines)

    # Asegurar directorio y guardar
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"hito_{hito.pk}_{datetime.now():%Y%m%d_%H%M%S}.md"
    path = REPORTS_DIR / filename
    with open(path, 'w', encoding='utf-8') as f:
        f.write(markdown)

    return markdown
