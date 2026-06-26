CREATE DATABASE IF NOT EXISTS sistema_votos 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE sistema_votos;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. TABLA CONFIGURACIÓN
CREATE TABLE IF NOT EXISTS configuracion (
    id INT PRIMARY KEY,
    nombre_config VARCHAR(50),
    valor VARCHAR(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO configuracion (id, nombre_config, valor) VALUES (1, 'resultados_visibles', '0') ON DUPLICATE KEY UPDATE valor='0';
INSERT INTO configuracion (id, nombre_config, valor) VALUES (2, 'tipo_evento', '0') ON DUPLICATE KEY UPDATE valor='0';
INSERT INTO configuracion (id, nombre_config, valor) VALUES (3, 'puntaje_min', '5') ON DUPLICATE KEY UPDATE valor=valor;
INSERT INTO configuracion (id, nombre_config, valor) VALUES (4, 'puntaje_max', '10') ON DUPLICATE KEY UPDATE valor=valor;
INSERT INTO configuracion (id, nombre_config, valor) VALUES (5, 'nombre_colegio', 'Secundario N° 43') ON DUPLICATE KEY UPDATE valor=valor;

-- 2. TABLA CANDIDATAS
CREATE TABLE IF NOT EXISTS candidatas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    foto VARCHAR(100) DEFAULT 'default.jpg',
    genero CHAR(1) DEFAULT 'F',
    activo TINYINT(1) DEFAULT 1
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 3. TABLA CATEGORIAS
CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    icono VARCHAR(20) DEFAULT '✨'
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 4. TABLA JUECES
CREATE TABLE IF NOT EXISTS jueces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    pin VARCHAR(4) NOT NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 5. TABLA VOTOS DETALLE (NUEVA ESTRUCTURA RELACIONAL COMPLETADA)
CREATE TABLE IF NOT EXISTS votos_detalle (
    id INT AUTO_INCREMENT PRIMARY KEY,
    juez_id INT,
    candidata_id INT,
    categoria_id INT,
    puntaje INT,
    FOREIGN KEY (juez_id) REFERENCES jueces(id) ON DELETE CASCADE,
    FOREIGN KEY (candidata_id) REFERENCES candidatas(id) ON DELETE CASCADE,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE CASCADE,
    UNIQUE KEY unica_votacion (juez_id, candidata_id, categoria_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Limpieza absoluta de tablas para el reinicio
TRUNCATE TABLE votos_detalle;
TRUNCATE TABLE candidatas;
TRUNCATE TABLE jueces;
TRUNCATE TABLE categorias;

-- Inicializamos Categorías
INSERT INTO categorias (id, nombre, icono) VALUES 
(1, 'Belleza', '>'),
(2, 'Simpatía', '>'),
(3, 'Elegancia', '>'),
(4, 'Desempeño', '>');

-- Inicializamos Candidatas (Mujeres)
INSERT INTO candidatas (nombre, genero) VALUES  
('Rodriguez Florencia', 'F'), ('Mamani Nadia Denis', 'F'), ('Marinez Ann Geraldine', 'F'),  
('Gaspar Serapio, Caterine', 'F'), ('Carranque Mia Ayelen', 'F'), ('Morales Macarena', 'F'),  
('Colque Tiara Dana Guadalupe', 'F'), ('Espinosa Josefina Barbara', 'F'), ('Galarza Murillo Renata Pilar', 'F'),
('Sotar Joselin', 'F'), ('Martin Diana', 'F'), ('Tobar Jeckeln Pilar Gianna Camila', 'F'),
('Velazquez Abril Ariana', 'F'), ('Inca Tatiana Claribel Damaris', 'F'), ('Aleman Sofia', 'F'),
('Gamez Martina', 'F'), ('Velazquez Estefania', 'F'), ('Rivera Julieta Agostina', 'F'),
('Corimayo Rocio Salome', 'F'), ('Rios Flores Sofia', 'F'), ('Avellaneda Julieta', 'F'), ('Alarcon Malena', 'F');

-- Inicializamos Candidatos (Varones)
INSERT INTO candidatas (nombre, genero) VALUES  
('Mendez Ignacio (5to 1ra)', 'M'), ('Caliva Bautista (5to 3ra)', 'M'), ('Reinoso Lucas (3ro 1ra)', 'M'),  
('Claros Agustin (5to 3ra)', 'M'), ('Brito Ramon (4to 1ra)', 'M'), ('Guerrero Santiago (4to 2da)', 'M'),  
('Ramirez Oscar (5to 2da)', 'M'), ('Bobadilla Luciano (3ro 3ra)', 'M'), ('Miranda Valentino (3ro 2da)', 'M'),
('Bejarano Facundo (2do 2da)', 'M'), ('Cruz Santiago (2do 1ra)', 'M'), ('Torres Maenga Feliciano (5to 1ra)', 'M'),
('Velazquez Matias (5to 1ra)', 'M'), ('Corimayo Andres (3ro 3ra)', 'M');

-- Mapeo automático de nombres de archivos de fotos según su posición y género
UPDATE candidatas c
JOIN (
    SELECT id, 
           ROW_NUMBER() OVER (PARTITION BY genero ORDER BY id) as posicion,
           genero
    FROM candidatas
) n ON c.id = n.id
SET c.foto = CASE 
    WHEN c.genero = 'F' THEN CONCAT('cand (', n.posicion, ').jpeg')
    WHEN c.genero = 'M' THEN CONCAT('chico (', n.posicion, ').jpeg')
END;

-- Inicializamos los Jueces y la cuenta Administradora
INSERT INTO jueces (nombre, pin) VALUES  
('Juez1', '1234'), 
('Juez2', '1234'), 
('Juez3', '8910'), 
('Juez4', '1112'), 
('Juez5', '1314'), 
('Admin', '1234');

SET FOREIGN_KEY_CHECKS = 1;