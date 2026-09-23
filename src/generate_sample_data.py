"""
Genera datos ficticios para la empresa de vidrio, aluminio y PVC,
inyectando a propósito un porcentaje de registros con errores
(nulos, duplicados, valores fuera de rango, FK inválidas) para que
la suite de calidad tenga algo real que detectar.

Uso:
    python -m src.generate_sample_data
Genera: output/productos.csv, output/pedidos.csv
"""

import random
from datetime import date, timedelta

import pandas as pd

from src.config import APP_CONFIG, ESTADOS_PEDIDO_VALIDOS, MATERIALES_VALIDOS
from src.logging_setup import get_logger

logger = get_logger(__name__)

random.seed(42)

NOMBRES_PRODUCTO = {
    "vidrio": ["Vidrio Templado 6mm", "Vidrio Laminado 8mm", "DVH Vidrio"],
    "aluminio": ["Perfil Aluminio Línea 25", "Perfil Aluminio Línea 35", "Marco Aluminio"],
    "pvc": ["Perfil PVC Línea 60", "Ventana PVC 2 hojas", "Perfil PVC Reforzado"],
}


def generar_productos(n: int = 40) -> pd.DataFrame:
    filas = []
    for i in range(1, n + 1):
        material = random.choice(list(MATERIALES_VALIDOS))
        nombre = random.choice(NOMBRES_PRODUCTO[material])

        # ~10% de errores intencionales
        error = random.random() < 0.10

        filas.append({
            "id_producto": i,
            "nombre": None if error and random.random() < 0.3 else nombre,
            "material": material if not error or random.random() > 0.3 else "cobre",  # material inválido
            "ancho_mm": round(random.uniform(300, 2400), 1) if not error else -50,
            "alto_mm": round(random.uniform(300, 2400), 1),
            "espesor_mm": round(random.uniform(3, 25), 1),
            "precio_unitario": round(random.uniform(1000, 90000), 2) if not error else None,
        })

    df = pd.DataFrame(filas)

    # inyectar un duplicado de id a propósito
    dup = df.iloc[0].copy()
    dup["id_producto"] = df.iloc[1]["id_producto"]
    df = pd.concat([df, pd.DataFrame([dup])], ignore_index=True)

    return df


def generar_pedidos(productos: pd.DataFrame, n: int = 150) -> pd.DataFrame:
    ids_producto_validos = list(productos["id_producto"])
    filas = []
    hoy = date.today()

    for i in range(1, n + 1):
        error = random.random() < 0.10

        id_producto = (
            random.choice(ids_producto_validos)
            if not error or random.random() > 0.4
            else 9999  # FK inválida a propósito
        )

        filas.append({
            "id_pedido": i,
            "cliente": f"Cliente {random.randint(1, 60)}" if not (error and random.random() < 0.3) else None,
            "id_producto": id_producto,
            "cantidad": random.randint(1, 200) if not error else -5,
            "fecha_pedido": hoy - timedelta(days=random.randint(0, 180)),
            "estado": random.choice(list(ESTADOS_PEDIDO_VALIDOS)) if not error or random.random() > 0.3 else "en_deposito",
        })

    return pd.DataFrame(filas)


def main():
    import os
    os.makedirs(APP_CONFIG.output_dir, exist_ok=True)

    productos = generar_productos()
    pedidos = generar_pedidos(productos)

    ruta_productos = os.path.join(APP_CONFIG.output_dir, "productos.csv")
    ruta_pedidos = os.path.join(APP_CONFIG.output_dir, "pedidos.csv")

    productos.to_csv(ruta_productos, index=False)
    pedidos.to_csv(ruta_pedidos, index=False)

    logger.info("Generados %d productos -> %s", len(productos), ruta_productos)
    logger.info("Generados %d pedidos -> %s", len(pedidos), ruta_pedidos)


if __name__ == "__main__":
    main()
