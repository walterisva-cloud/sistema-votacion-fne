@echo off
title Apagar Proyecto - Docker
echo ====================================================
echo   APAGANDO LOS SERVICIOS DE APPS Y BASE DE DATOS
echo ====================================================
echo.
docker compose down
echo.
echo ====================================================
echo   ¡Proyecto apagado con exito! Memoria RAM liberada.
echo ====================================================
echo.
pause