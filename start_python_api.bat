@echo off
title API Python SensCritique
color 0A
mode con: cols=100 lines=30

echo.
echo ========================================================================
echo                    API PYTHON SENS CRITIQUE
echo ========================================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    color 0C
    echo [X] ERREUR: Python n'est pas installe!
    echo.
    echo Telechargez Python depuis: https://www.python.org/downloads/
    echo Installez la version 3.8 ou superieure
    echo.
    pause
    exit /b 1
)

echo [OK] Python detecte
python --version
echo.

if not exist "venv\" (
    echo [INFO] Creation de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 (
        color 0C
        echo.
        echo [X] ERREUR: Echec de la creation de l'environnement virtuel
        echo.
        pause
        exit /b 1
    )
    echo [OK] Environnement virtuel cree
    echo.
)

echo [INFO] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
if errorlevel 1 (
    color 0C
    echo.
    echo [X] ERREUR: Echec de l'activation de l'environnement virtuel
    echo.
    pause
    exit /b 1
)

if not exist "venv\Lib\site-packages\flask\" (
    echo [INFO] Installation des dependances Python...
    echo Cela peut prendre 1-2 minutes, patientez...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        color 0C
        echo.
        echo [X] ERREUR: Echec de l'installation des dependances
        echo.
        echo Verifiez:
        echo - Votre connexion internet
        echo - Que vous avez les droits administrateur
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependances installees avec succes
    echo.
) else (
    echo [OK] Dependances deja installees
    echo.
)

echo ========================================================================
echo                    DEMARRAGE DE L'API
echo ========================================================================
echo.
echo L'API sera accessible sur: http://localhost:5000/api/critiques
echo.
echo Appuyez sur Ctrl+C pour arreter l'API
echo.
echo ========================================================================
echo.

python api_senscritique.py

pause

