"""
Orquestador del pipeline de calidad de datos.

Modo por defecto: lee productos.csv / pedidos.csv (generados por
src/generate_sample_data.py) para que el proyecto se pueda probar
sin levantar Postgres.

Modo --db: lee directamente de PostgreSQL usando src/db.py
(usado en el proyecto grande, acá queda como ejemplo de arquitectura).

Salida: output/reporte_calidad.json + log de la corrida en logs/
"""

import argparse
import json
import os
import sys
from datetime import datetime

import pandas as pd

from src.config import APP_CONFIG
from src.exceptions import DataQualityError
from src.logging_setup import get_logger
from src.quality_checks import ejecutar_suite

logger = get_logger("main")


def cargar_desde_csv() -> tuple[pd.DataFrame, pd.DataFrame]:
    ruta_productos = os.path.join(APP_CONFIG.output_dir, "productos.csv")
    ruta_pedidos = os.path.join(APP_CONFIG.output_dir, "pedidos.csv")

    if not (os.path.exists(ruta_productos) and os.path.exists(ruta_pedidos)):
        raise DataQualityError(
            "No se encontraron los CSV de entrada. "
            "Corré primero: python -m src.generate_sample_data"
        )

    return pd.read_csv(ruta_productos), pd.read_csv(ruta_pedidos)


def cargar_desde_db() -> tuple[pd.DataFrame, pd.DataFrame]:
    from src.db import fetch_table, get_connection

    conn = get_connection()
    try:
        productos = fetch_table(
            conn, "productos",
            {"id_producto", "nombre", "material", "ancho_mm", "alto_mm", "espesor_mm", "precio_unitario"},
        )
        pedidos = fetch_table(
            conn, "pedidos",
            {"id_pedido", "cliente", "id_producto", "cantidad", "fecha_pedido", "estado"},
        )
        return productos, pedidos
    finally:
        conn.close()


def guardar_reporte(resultados: list[dict]) -> str:
    os.makedirs(APP_CONFIG.output_dir, exist_ok=True)
    ruta = os.path.join(APP_CONFIG.output_dir, "reporte_calidad.json")

    reporte = {
        "generado_en": datetime.now().isoformat(timespec="seconds"),
        "resultados": resultados,
        "resumen": {
            "reglas_evaluadas": len(resultados),
            "reglas_100pct_ok": sum(1 for r in resultados if r["porcentaje_ok"] == 100),
        },
    }

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=2, ensure_ascii=False, default=str)

    return ruta


def main():
    parser = argparse.ArgumentParser(description="Pipeline de calidad de datos")
    parser.add_argument("--db", action="store_true", help="Leer desde PostgreSQL en vez de CSV")
    args = parser.parse_args()

    try:
        if args.db:
            logger.info("Cargando datos desde PostgreSQL...")
            productos, pedidos = cargar_desde_db()
        else:
            logger.info("Cargando datos desde CSV locales...")
            productos, pedidos = cargar_desde_csv()

        logger.info("Productos: %d filas | Pedidos: %d filas", len(productos), len(pedidos))

        resultados = ejecutar_suite(productos, pedidos)
        ruta_reporte = guardar_reporte(resultados)

        logger.info("Reporte de calidad guardado en: %s", ruta_reporte)

    except DataQualityError as e:
        # Errores esperados del dominio: se loggean con contexto y se corta limpio
        logger.error("Fallo controlado del pipeline: %s", e)
        sys.exit(1)
    except Exception:
        # Cualquier otra cosa (bug real, error no anticipado) se loggea con stacktrace completo
        logger.exception("Error inesperado en el pipeline")
        sys.exit(2)


if __name__ == "__main__":
    main()
