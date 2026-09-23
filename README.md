# Data Quality Mini — Vidrio, Aluminio y PVC

Versión reducida de un pipeline de calidad de datos para una empresa ficticia
del rubro vidrio/aluminio/PVC. Pensado como muestra de arquitectura y manejo
de errores, no como el proyecto completo (ese vive en `data-quality-dashboard`).

## Qué demuestra

- **Separación de capas**: configuración, acceso a datos, reglas de negocio y
  orquestación en módulos independientes (no todo en un script).
- **Manejo de errores por capas**: excepciones propias del dominio
  (`DatabaseConnectionError`, `DataValidationError`, `SchemaMismatchError`),
  reintentos con backoff en la conexión a la base, y un `main.py` que
  distingue entre fallos esperados (se cortan limpio) y bugs (se loggean
  con stacktrace).
- **Logging estructurado**: consola + archivo por corrida en `logs/`.
- **Reglas de calidad de datos reales**: nulos en campos críticos,
  duplicados, valores fuera de rango, valores permitidos (enum) e
  integridad referencial entre `pedidos` y `productos`.
- **Reporte reproducible**: cada corrida genera `output/reporte_calidad.json`
  con el detalle de qué regla falló, en qué tabla y con qué ejemplos —
  ese JSON es lo que después alimentaría un dashboard (Power BI / Metabase).

## Estructura

```
data-quality-mini/
├── sql/schema.sql              # esquema de referencia (productos, pedidos, proveedores)
├── src/
│   ├── config.py                # configuración vía variables de entorno
│   ├── exceptions.py            # excepciones propias del dominio
│   ├── logging_setup.py         # logging a consola + archivo
│   ├── db.py                    # conexión a Postgres con retry/backoff
│   ├── generate_sample_data.py  # datos ficticios con errores inyectados
│   └── quality_checks.py        # motor de reglas de calidad
├── main.py                      # orquestador (CSV por defecto, --db opcional)
└── requirements.txt
```

## Cómo correrlo

No hace falta Postgres para probarlo: el modo por defecto trabaja sobre CSV.

```bash
pip install -r requirements.txt

# 1. generar datos ficticios (con errores a propósito)
python -m src.generate_sample_data

# 2. correr la suite de calidad
python main.py
```

Esto genera:
- `output/productos.csv`, `output/pedidos.csv` — datos de entrada
- `output/reporte_calidad.json` — resultado de cada regla
- `logs/run_<timestamp>.log` — log detallado de la corrida

Para correrlo contra una base Postgres real (usando `sql/schema.sql`),
configurar las variables `DQ_DB_*` y correr `python main.py --db`.

## Ejemplo de salida

```
2026-09-23 10:00:01 | INFO     | main | Productos: 41 filas | Pedidos: 150 filas
2026-09-23 10:00:01 | INFO     | src.quality_checks | nulos_en_campos_criticos          | productos | OK: 92.68% (3/41 fallidos)
2026-09-23 10:00:01 | INFO     | src.quality_checks | duplicados_por_id                 | productos | OK: 95.12% (2/41 fallidos)
2026-09-23 10:00:01 | WARNING  | src.quality_checks | valores_permitidos_material       | productos | OK: 90.24% (4/41 fallidos)
2026-09-23 10:00:01 | WARNING  | src.quality_checks | integridad_referencial_id_producto | pedidos   | OK: 94.67% (8/150 fallidos)
```

## Próximos pasos (versión grande)

- Conectar `reporte_calidad.json` a Power BI para visualizar tendencia de
  calidad por tabla y por corrida.
- Agregar tests unitarios (`pytest`) sobre `quality_checks.py`.
- Empaquetar la corrida como job programado (cron / Airflow).
