"""
Configuración centralizada del proyecto.
Todo lo que puede variar entre entornos (dev/prod) vive acá,
nunca hardcodeado dentro de la lógica.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DBConfig:
    host: str = os.getenv("DQ_DB_HOST", "localhost")
    port: int = int(os.getenv("DQ_DB_PORT", "5432"))
    name: str = os.getenv("DQ_DB_NAME", "vidrio_aluminio_pvc")
    user: str = os.getenv("DQ_DB_USER", "postgres")
    password: str = os.getenv("DQ_DB_PASSWORD", "postgres")
    connect_timeout: int = int(os.getenv("DQ_DB_TIMEOUT", "5"))


@dataclass(frozen=True)
class AppConfig:
    log_dir: str = os.getenv("DQ_LOG_DIR", "logs")
    output_dir: str = os.getenv("DQ_OUTPUT_DIR", "output")
    max_retries: int = int(os.getenv("DQ_MAX_RETRIES", "3"))
    retry_backoff_seconds: float = float(os.getenv("DQ_RETRY_BACKOFF", "2"))


DB_CONFIG = DBConfig()
APP_CONFIG = AppConfig()

MATERIALES_VALIDOS = {"vidrio", "aluminio", "pvc"}
ESTADOS_PEDIDO_VALIDOS = {"pendiente", "en_proceso", "entregado", "cancelado"}
