import os
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend

STORAGE_PATH = "storage/certs/"

class CertificadoService:
    @staticmethod
    def validar_pfx(file_content: bytes, password: str) -> bool:
        """
        Tenta abrir o certificado PFX com a senha fornecida para validar se o par está correto.
        """
        try:
            pkcs12.load_key_and_certificates(
                file_content, 
                password.encode(), 
                default_backend()
            )
            return True
        except Exception as e:
            print(f"DEBUG: Falha na validação do PFX: {str(e)}")
            return False

    @staticmethod
    def salvar_pfx(file_content: bytes, filename: str) -> str:
        """
        Salva o certificado no diretório de storage e retorna o caminho relativo.
        """
        # Criar diretório se não existir
        if not os.path.exists(STORAGE_PATH):
            os.makedirs(STORAGE_PATH)
            
        file_path = os.path.join(STORAGE_PATH, filename)
        
        with open(file_path, "wb") as f:
            f.write(file_content)
            
        return file_path
