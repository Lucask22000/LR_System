@echo off
echo Iniciando LR System...
echo.

:: Ativar ambiente virtual
if exist .venv\Scripts\activate (
    call .venv\Scripts\activate
) else (
    echo Criando ambiente virtual...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
)

:: Iniciar o sistema
streamlit run app.py

pause