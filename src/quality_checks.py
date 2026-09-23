"""
Motor de reglas de calidad de datos.

Cada regla:
- recibe un DataFrame
- devuelve un dict con: regla, tabla, registros_evaluados,
  registros_fallidos, porcentaje_ok, detalle
No lanza excepción por datos sucios (eso es lo esperado);
sólo lanza excepción si la regla no se puede evaluar (columna inexistente, etc).
"""

from __future__ import annotations

import pandas as pd

from src.config import ESTADOS_PEDIDO_VALIDOS, MATERIALES_VALIDOS
from src.exceptions import SchemaMismatchError
from src.logging_setup import get_logger

logger = get_logger(__name__)


def _resultado(regla: str, tabla: str, total: int, fallidos: pd.DataFrame) -> dict:
    n_fallidos = len(fallidos)
    pct_ok = round(100 * (total - n_fallidos) / total, 2) if total else 100.0
    return {
        "regla": regla,
        "tabla": tabla,
        "registros_evaluados": total,
        "registros_fallidos": n_fallidos,
        "porcentaje_ok": pct_ok,
        "ejemplos_fallidos": fallidos.head(5).to_dict("records"),
    }


def check_nulos_criticos(df: pd.DataFrame, tabla: str, columnas: list[str]) -> dict:
    faltantes = [c for c in columnas if c not in df.columns]
    if faltantes:
        raise SchemaMismatchError(f"Columnas inexistentes en '{tabla}': {faltantes}")
    fallidos = df[df[columnas].isnull().any(axis=1)]
    return _resultado("nulos_en_campos_criticos", tabla, len(df), fallidos)


def check_duplicados(df: pd.DataFrame, tabla: str, columna_id: str) -> dict:
    fallidos = df[df.duplicated(subset=columna_id, keep=False)]
    return _resultado("duplicados_por_id", tabla, len(df), fallidos)


def check_rango_positivo(df: pd.DataFrame, tabla: str, columnas: list[str]) -> dict:
    condicion = pd.Series(False, index=df.index)
    for c in columnas:
        condicion = condicion | (df[c] <= 0) | df[c].isnull()
    fallidos = df[condicion]
    return _resultado(f"valores_positivos_{'_'.join(columnas)}", tabla, len(df), fallidos)


def check_valores_permitidos(df: pd.DataFrame, tabla: str, columna: str, permitidos: set) -> dict:
    fallidos = df[~df[columna].isin(permitidos)]
    return _resultado(f"valores_permitidos_{columna}", tabla, len(df), fallidos)


def check_integridad_referencial(
    df_hijo: pd.DataFrame, tabla_hijo: str, columna_fk: str,
    ids_validos: set,
) -> dict:
    fallidos = df_hijo[~df_hijo[columna_fk].isin(ids_validos)]
    return _resultado(f"integridad_referencial_{columna_fk}", tabla_hijo, len(df_hijo), fallidos)


def ejecutar_suite(productos: pd.DataFrame, pedidos: pd.DataFrame) -> list[dict]:
    """Corre todas las reglas y devuelve la lista de resultados."""
    resultados = []

    resultados.append(check_nulos_criticos(productos, "productos", ["nombre", "material", "precio_unitario"]))
    resultados.append(check_duplicados(productos, "productos", "id_producto"))
    resultados.append(check_rango_positivo(productos, "productos", ["ancho_mm", "alto_mm", "espesor_mm", "precio_unitario"]))
    resultados.append(check_valores_permitidos(productos, "productos", "material", MATERIALES_VALIDOS))

    resultados.append(check_nulos_criticos(pedidos, "pedidos", ["cliente", "id_producto", "cantidad"]))
    resultados.append(check_rango_positivo(pedidos, "pedidos", ["cantidad"]))
    resultados.append(check_valores_permitidos(pedidos, "pedidos", "estado", ESTADOS_PEDIDO_VALIDOS))
    resultados.append(
        check_integridad_referencial(
            pedidos, "pedidos", "id_producto", set(productos["id_producto"])
        )
    )

    for r in resultados:
        nivel = logger.info if r["porcentaje_ok"] == 100 else logger.warning
        nivel("%-35s | %s | OK: %s%% (%d/%d fallidos)",
              r["regla"], r["tabla"], r["porcentaje_ok"],
              r["registros_fallidos"], r["registros_evaluados"])

    return resultados
