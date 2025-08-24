
class InvalidRowError(Exception):
    """
    Se lanza cuando una fila no cumple las validaciones básicas
    o el CSV excede los límites de tamaño.
    """
    pass
