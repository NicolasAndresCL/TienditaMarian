from pathlib import Path

ALLOWED_EXTENSIONS = {'.csv'}

EXPECTED_COLUMNS = {
    'nombre',
    'descripcion',
    'image',
    'precio',
    'stock',
}

MAX_ROWS = 1000

REPORTS_DIR = Path('marian_loader_reports')
