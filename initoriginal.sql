-- 1. Crear la base de datos con soporte para emojis y acentos (utf8mb4)
CREATE DATABASE IF NOT EXISTS sistema_votos 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE sistema_votos;

SET FOREIGN_KEY_CHECKS = 0;
-- 2. Tabla de configuración
CREATE TABLE IF NOT EXISTS configuracion (
    id INT PRIMARY KEY,
    nombre_config VARCHAR(50),
    valor VARCHAR(10)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO configuracion (id, nombre_config, valor) 
VALUES (1, 'resultados_visibles', '0') 
ON DUPLICATE KEY UPDATE valor='0';
-- 1. Actualización de la Tabla de Configuración
-- Añadimos 'tipo_evento' (0 para Reina, 1 para Chico 10)
INSERT INTO configuracion (id, nombre_config, valor) 
VALUES (2, 'tipo_evento', '0') 
ON DUPLICATE KEY UPDATE valor='0';

DROP TABLE IF EXISTS votos; -- Borramos votos primero por la llave foránea
DROP TABLE IF EXISTS candidatas;

-- 3. Tabla de Candidatas (Ajustada para acentos)
CREATE TABLE IF NOT EXISTS candidatas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    foto VARCHAR(100) DEFAULT 'default.jpg'
	,genero CHAR(1) DEFAULT 'F'
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;


-- 4. Tabla de Jueces
CREATE TABLE IF NOT EXISTS jueces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    pin VARCHAR(4) NOT NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 5. Tabla de Votos
CREATE TABLE IF NOT EXISTS votos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    juez_id INT,
    candidata_id INT,
    cat_elegancia INT,
    cat_belleza INT,
    cat_simpatia INT,
    total_puntos INT,
    FOREIGN KEY (juez_id) REFERENCES jueces(id),
    FOREIGN KEY (candidata_id) REFERENCES candidatas(id),
    UNIQUE(juez_id, candidata_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;


-- 6. Inserción de datos (Asegúrate de que tu editor de texto guarde este archivo como UTF-8)
-- 3. Inserción de datos con género
-- Limpiamos e insertamos ejemplos de ambos para probar
TRUNCATE TABLE candidatas;

INSERT INTO candidatas (nombre) VALUES 
('Rodriguez Florencia'), 
('Mamani Nadia Denis'), 
('Marinez Ann Geraldine'), 
('Gaspar Serapio, Caterine'), 
('Carranque Mia Ayelen'), 
('Morales Macarena'), 
('Colque Tiara Dana Guadalupe'), 
('Espinosa Josefina Barbara'),
('Galarza Murillo Renata Pilar'),
('Sotar Joselin'),
('Martin Diana'),
('Tobar Jeckeln Pilar Gianna Camila'),
('Velazquez Abril Ariana'),
('Inca Tatiana Claribel Damaris'),
('Aleman Sofia'),
('Gamez Martina'),
('Velazquez Estefania'),
('Rivera Julieta Agostina'),
('Corimayo Rocio Salome'),
('Rios Flores Sofia'),
('Avellaneda Julieta'),
('Alarcon Malena');

UPDATE candidatas 
SET foto = CONCAT('cand (', id, ').jpeg');
	--genero = 'F';

INSERT INTO candidatas (nombre, genero, foto) VALUES 
('Mendez Ignacio (5to 1ra)', 'M', 'chico1.jpg'), 
('Caliva Bautista (5to 3ra)', 'M', 'chico2.jpg'), 
('Reinoso Lucas (3ro 1ra)', 'M', 'chico3.jpg'), 
('Claros Agustin (5to 3ra)', 'M', 'chico4.jpg'), 
('Brito Ramon (4to 1ra)', 'M', 'chico5.jpg'), 
('Guerrero Santiago (4to 2da)', 'M', 'chico6.jpg'), 
('Ramirez Oscar (5to 2da)', 'M', 'chico7.jpg'), 
('Bobadilla Luciano (3ro 3ra)', 'M', 'chico8.jpg'),
('Miranda Valentino (3ro 2da)', 'M', 'chico9.jpg'),
('Bejarano Facundo (2do 2da)', 'M', 'chico10.jpg'),
('Cruz Santiago (2do 1ra)', 'M', 'chico11.jpg'),
('Torres Maenga Feliciano (5to 1ra)', 'M', 'chico12.jpg'),
('Velazquez Matias (5to 1ra)', 'M', 'chico13.jpg'),
('Corimayo Andres (3ro 3ra)', 'M', 'chico14.jpg');

UPDATE candidatas 
SET foto = CONCAT('chico (', id, ').jpeg')
WHERE genero = 'M'

INSERT INTO jueces (nombre, pin) VALUES 
('Juez1', '1234'),
('Juez2', '4567'),
('Juez3', '8910'),
('Juez4', '1112'),
('Juez5', '1314'),
('Admin','1234');

SET FOREIGN_KEY_CHECKS = 1;