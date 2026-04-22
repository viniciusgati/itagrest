import sys
import os
import uvicorn

# Remover diretórios do Python 3.14 do sys.path para evitar conflitos
sys.path = [p for p in sys.path if "3.14" not in p]

if __name__ == "__main__":
    # Forçar o ambiente de homologação
    os.environ["APP_ENV"] = "homolog"
    
    # Iniciar o servidor de forma programática
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
