@echo off
title Iniciar Proyecto - Docker
echo ====================================================
echo   INICIANDO LOS SERVICIOS DE LA APP Y BASE DE DATOS
echo ====================================================
echo.
echo Encendiendo contenedores en segundo plano...
docker compose up -d
echo.
echo ====================================================
echo   ¡Proyecto iniciado con exito! 
echo   Por favor, espera unos 10 segundos a que cargue MySQL.
echo   Luego ingresa a: http://localhost:5000
echo ====================================================
echo.
pause