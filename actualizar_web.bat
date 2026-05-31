@echo off
title Actualizar Aplicacion Web - Docker
echo ====================================================
echo   ACTUALIZANDO CODIGO WEB SIN TOCAR LA BASE DE DATOS
echo ====================================================
echo.
echo Recompilando cambios en HTML/Python...
docker compose up --build -d web
echo.
echo ====================================================
echo   ¡Proceso completado! Refresca tu navegador (F5).
echo ====================================================
echo.
pause