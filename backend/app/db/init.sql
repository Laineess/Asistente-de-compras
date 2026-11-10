CREATE DATABASE IF NOT EXISTS analisis_compras
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE analisis_compras;

CREATE TABLE IF NOT EXISTS resultados (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre_producto VARCHAR(255) NOT NULL,
  comercio VARCHAR(100) NOT NULL,
  precio DECIMAL(12,2) NOT NULL,
  fecha_consulta DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_resultados_producto (nombre_producto),
  INDEX idx_resultados_comercio (comercio),
  INDEX idx_resultados_fecha (fecha_consulta)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE utf8mb4_unicode_ci;
