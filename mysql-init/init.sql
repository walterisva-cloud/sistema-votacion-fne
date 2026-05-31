
CREATE DATABASE IF NOT EXISTS sistema_votos 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE sistema_votos;

SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS configuracion (
    id INT PRIMARY KEY,
    nombre_config VARCHAR(50),
    valor VARCHAR(10)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

INSERT INTO configuracion (id, nombre_config, valor) 
VALUES (1, 'resultados_visibles', '0') 
ON DUPLICATE KEY UPDATE valor='0';

INSERT INTO configuracion (id, nombre_config, valor) 
VALUES (2, 'tipo_evento', '0') 
ON DUPLICATE KEY UPDATE valor='0';

CREATE TABLE IF NOT EXISTS candidatas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    foto VARCHAR(100) DEFAULT 'default.jpg'
	,genero CHAR(1) DEFAULT 'F'
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS jueces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    pin VARCHAR(4) NOT NULL
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

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


TRUNCATE TABLE votos;
TRUNCATE TABLE candidatas;
TRUNCATE TABLE jueces;

INSERT INTO candidatas (nombre, genero) VALUES  
('Rodriguez Florencia', 'F'), ('Mamani Nadia Denis', 'F'), ('Marinez Ann Geraldine', 'F'),  
('Gaspar Serapio, Caterine', 'F'), ('Carranque Mia Ayelen', 'F'), ('Morales Macarena', 'F'),  
('Colque Tiara Dana Guadalupe', 'F'), ('Espinosa Josefina Barbara', 'F'), ('Galarza Murillo Renata Pilar', 'F'),
('Sotar Joselin', 'F'), ('Martin Diana', 'F'), ('Tobar Jeckeln Pilar Gianna Camila', 'F'),
('Velazquez Abril Ariana', 'F'), ('Inca Tatiana Claribel Damaris', 'F'), ('Aleman Sofia', 'F'),
('Gamez Martina', 'F'), ('Velazquez Estefania', 'F'), ('Rivera Julieta Agostina', 'F'),
('Corimayo Rocio Salome', 'F'), ('Rios Flores Sofia', 'F'), ('Avellaneda Julieta', 'F'), ('Alarcon Malena', 'F');

INSERT INTO candidatas (nombre, genero) VALUES  
('Mendez Ignacio (5to 1ra)', 'M'), ('Caliva Bautista (5to 3ra)', 'M'), ('Reinoso Lucas (3ro 1ra)', 'M'),  
('Claros Agustin (5to 3ra)', 'M'), ('Brito Ramon (4to 1ra)', 'M'), ('Guerrero Santiago (4to 2da)', 'M'),  
('Ramirez Oscar (5to 2da)', 'M'), ('Bobadilla Luciano (3ro 3ra)', 'M'), ('Miranda Valentino (3ro 2da)', 'M'),
('Bejarano Facundo (2do 2da)', 'M'), ('Cruz Santiago (2do 1ra)', 'M'), ('Torres Maenga Feliciano (5to 1ra)', 'M'),
('Velazquez Matias (5to 1ra)', 'M'), ('Corimayo Andres (3ro 3ra)', 'M');

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

INSERT INTO jueces (nombre, pin) VALUES  
('Juez1', '1234'), ('Juez2', '1234'), ('Juez3', '8910'), ('Juez4', '1112'), ('Juez5', '1314'), ('Admin','1234');

SET FOREIGN_KEY_CHECKS = 1;