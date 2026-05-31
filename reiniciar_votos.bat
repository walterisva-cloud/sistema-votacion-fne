@echo off
title Reiniciar Votos - Docker
echo ====================================================
echo   ADVERTENCIA: SE ELIMINARAN TODOS LOS VOTOS EMITIDOS
echo ====================================================
echo.
echo Presiona CTRL+C si deseas cancelar. De lo contrario:
pause
echo.
echo Limpiando tabla de votos en la Base de Datos...
docker exec -i db_votacion mysql -u root --password="root_password_segura" -e "TRUNCATE TABLE votos;" sistema_votos
echo.
echo ====================================================
echo   ¡Votos reiniciados! El sistema esta listo en cero.
echo ====================================================
echo.
pause