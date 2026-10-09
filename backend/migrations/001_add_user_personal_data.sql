-- Migración no destructiva para MySQL 8+. Ejecutar una sola vez antes de desplegar.
-- Las columnas permanecen NULL para conservar la validez de los usuarios existentes.
ALTER TABLE users ADD COLUMN paternal_surname VARCHAR(100) NULL AFTER name;
ALTER TABLE users ADD COLUMN maternal_surname VARCHAR(100) NULL AFTER paternal_surname;
ALTER TABLE users ADD COLUMN phone VARCHAR(25) NULL AFTER maternal_surname;

-- Estrategia de transición: el API exige estos tres valores sólo en registros nuevos.
-- Tras completar datos históricos, una migración futura podrá volverlos NOT NULL.
