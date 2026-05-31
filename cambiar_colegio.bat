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

echo 2. Levantando los contenedores limpios...
docker compose up -d
echo.

echo 3. Esperando 10 segundos a que MySQL inicie internamente1...
timeout /t 10 /nobreak >nul
echo.

echo 4. Forzando la inyeccion del script SQL fresco...
docker exec -i db_votacion bash -c "mysql -u root -proot_password_segura sistema_votos < /docker-entrypoint-initdb.d/init.sql"
echo.

echo ====================================================
echo   ¡Proceso Exitoso! 
echo   Recarga http://localhost:5000 en tu navegador.
echo ====================================================
echo.
pause