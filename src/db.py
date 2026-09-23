"""
Capa de acceso a datos.

Aísla toda la lógica de conexión a Postgres: reintentos con backoff,
timeouts, y traducción de errores de psycopg2 a excepciones propias
del dominio (para que el resto del código no dependa del driver).
"""

import time

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

from src.config import APP_CONFIG, DB_CONFIG
from src.exceptions import DatabaseConnectionError, SchemaMismatchError
from src.logging_setup import get_logger

logger = get_logger(__name__)


def get_connection():
    """
    Intenta conectar con reintentos y backoff exponencial simple.
    Traduce cualquier error del driver a DatabaseConnectionError,
    con el mensaje original conservado para debugging.
    """
    last_error = None

    for intento in range(1, APP_CONFIG.max_retries + 1):
        try:
            conn = psycopg2.connect(
                host=DB_CONFIG.host,
                port=DB_CONFIG.port,
                dbname=DB_CONFIG.name,
                user=DB_CONFIG.user,
                password=DB_CONFIG.password,
                connect_timeout=DB_CONFIG.connect_timeout,
            )
            logger.info("Conexión a la base establecida (intento %d)", intento)
            return conn

        except psycopg2.OperationalError as e:
            last_error = e
            espera = APP_CONFIG.retry_backoff_seconds * intento
            logger.warning(
                "Fallo de conexión (intento %d/%d): %s. Reintentando en %.1fs",
                intento, APP_CONFIG.max_retries, e, espera,
            )
            time.sleep(espera)

    raise DatabaseConnectionError(
        f"No se pudo conectar a la base tras {APP_CONFIG.max_retries} intentos: {last_error}"
    )


def fetch_table(conn, table_name: str, expected_columns: set[str]) -> pd.DataFrame:
    """
    Trae una tabla completa como DataFrame y valida que tenga
    las columnas esperadas antes de devolverla.
    """
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"SELECT * FROM {table_name};")
            rows = cur.fetchall()
            df = pd.DataFrame(rows)
    except psycopg2.Error as e:
        raise DatabaseConnectionError(f"Error consultando '{table_name}': {e}") from e

    if df.empty:
        logger.warning("La tabla '%s' no tiene registros", table_name)
        return df

    faltantes = expected_columns - set(df.columns)
    if faltantes:
        raise SchemaMismatchError(
            f"La tabla '{table_name}' no tiene las columnas esperadas: {faltantes}"
        )

    return df
