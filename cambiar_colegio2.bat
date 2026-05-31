@echo off
title Cambiar Participantes - Docker
echo ====================================================
echo   ADVERTENCIA: SE REINICIARA LA BASE DE DATOS COMPLETA
echo ====================================================
echo.
echo Asegurate de haber modificado el archivo 'mysql-init/init.sql' 
echo con la consulta de ROW_NUMBER() antes de continuar.
echo.
pause
echo.

echo 1. Eliminando contenedores viejos y volumenes de datos...
docker compose down -v
echo.

echo 2. Levantando los contenedores e inicializando datos desde init.sql...
docker compose up -d
echo.

echo 3. Esperando 12 segundos a que el motor procese los registros...
timeout /t 12 /nobreak >nul
echo.

echo ====================================================
echo   ¡Proceso Exitoso! 
echo   Recarga http://localhost:5000 en tu navegador.
echo ====================================================
echo.
pause