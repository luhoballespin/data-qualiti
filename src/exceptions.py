"""
Excepciones propias del dominio.

Usar excepciones específicas (en vez de Exception genérica) permite:
- capturar solo lo que se espera capturar
- loggear con contexto claro
- decidir distinto comportamiento según el tipo de falla
"""


class DataQualityError(Exception):
    """Excepción base del proyecto. Todo error propio hereda de acá."""


class DatabaseConnectionError(DataQualityError):
    """No se pudo establecer o mantener la conexión a la base de datos."""


class DataValidationError(DataQualityError):
    """Un registro no cumple una regla de calidad obligatoria (bloqueante)."""


class SchemaMismatchError(DataQualityError):
    """La tabla consultada no tiene las columnas esperadas."""


class ConfigurationError(DataQualityError):
    """Falta o es inválida una variable de configuración requerida."""
