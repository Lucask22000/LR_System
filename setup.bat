@echo off
echo Configurando LR System...
echo.

:: Criar ambiente virtual
python -m venv .venv

:: Ativar ambiente virtual
call .venv\Scripts\activate

:: Atualizar pip
python -m pip install --upgrade pip

:: Instalar dependências
pip install -r requirements.txt

echo.
echo Configuração concluída!
echo Execute run.bat para iniciar o sistema.
pause