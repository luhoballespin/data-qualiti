-- Esquema mínimo: empresa ficticia de vidrio, aluminio y PVC
-- Diseñado para forzar casos reales de mala calidad de datos

CREATE TABLE IF NOT EXISTS proveedores (
    id_proveedor SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    material_provisto VARCHAR(20) NOT NULL,  -- vidrio | aluminio | pvc
    contacto VARCHAR(120)
);

CREATE TABLE IF NOT EXISTS productos (
    id_producto SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    material VARCHAR(20) NOT NULL,           -- vidrio | aluminio | pvc
    ancho_mm NUMERIC(8,2),
    alto_mm NUMERIC(8,2),
    espesor_mm NUMERIC(6,2),
    precio_unitario NUMERIC(10,2),
    id_proveedor INTEGER REFERENCES proveedores(id_proveedor)
);

CREATE TABLE IF NOT EXISTS pedidos (
    id_pedido SERIAL PRIMARY KEY,
    cliente VARCHAR(120) NOT NULL,
    id_producto INTEGER REFERENCES productos(id_producto),
    cantidad INTEGER,
    fecha_pedido DATE,
    estado VARCHAR(20)  -- pendiente | en_proceso | entregado | cancelado
);
