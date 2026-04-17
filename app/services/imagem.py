import os
import uuid
from typing import Optional

STORAGE_PATH = "storage/produtos/"

class ImagemService:
    @staticmethod
    def salvar_imagem_produto(file_content: bytes, filename: str) -> str:
        """
        Salva uma imagem de produto no storage e retorna o caminho relativo.
        Gera um nome único para evitar colisões.
        """
        if not os.path.exists(STORAGE_PATH):
            os.makedirs(STORAGE_PATH)
            
        extension = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{extension}"
        file_path = os.path.join(STORAGE_PATH, unique_filename)
        
        with open(file_path, "wb") as f:
            f.write(file_content)
            
        # Retorna o caminho para ser acessível via URL (necessário configurar static files no app)
        return f"/static/produtos/{unique_filename}"

    @staticmethod
    def excluir_imagem(imagem_path: str):
        """Exclui o arquivo de imagem físico se ele existir."""
        if not imagem_path or not imagem_path.startswith("/static/produtos/"):
            return
            
        filename = imagem_path.split("/")[-1]
        file_path = os.path.join(STORAGE_PATH, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
