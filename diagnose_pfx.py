import os
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
import binascii

cert_path = "storage/certs/ROSICLER LUCIA DOS SANTOS_49112135000138.pfx"
password = b"123456"

print(f"--- Diagnóstico de Certificado ---")
print(f"Caminho: {cert_path}")
print(f"OPENSSL_CONF: {os.environ.get('OPENSSL_CONF')}")

if not os.path.exists(cert_path):
    print("ERRO: Arquivo não encontrado!")
else:
    with open(cert_path, "rb") as f:
        data = f.read()
    
    print(f"Tamanho do arquivo: {len(data)} bytes")
    print(f"Primeiros 10 bytes (hex): {binascii.hexlify(data[:10])}")
    
    try:
        # Tentativa de carregamento direto
        pkcs12.load_key_and_certificates(data, password, default_backend())
        print("SUCESSO: Certificado carregado corretamente via cryptography!")
    except Exception as e:
        print(f"FALHA: Erro ao carregar via cryptography: {str(e)}")
        
    # Teste via comando openssl (se disponível)
    import subprocess
    print("\n--- Teste via CLI openssl ---")
    try:
        # Tenta listar o conteúdo sem extrair a chave privada
        cmd = ["openssl", "pkcs12", "-in", cert_path, "-passin", f"pass:{password.decode()}", "-nokeys", "-info"]
        # Adiciona flag legacy se o openssl for versão 3
        result = subprocess.run(cmd + ["-legacy"], capture_output=True, text=True)
        if result.returncode == 0:
            print("SUCESSO: OpenSSL CLI (com -legacy) conseguiu ler o arquivo!")
        else:
            print(f"FALHA: OpenSSL CLI erro: {result.stderr}")
            # Tenta sem a flag legacy para comparar
            result_no_legacy = subprocess.run(cmd, capture_output=True, text=True)
            print(f"FALHA (sem -legacy) OpenSSL CLI erro: {result_no_legacy.stderr}")
    except Exception as e:
        print(f"ERRO ao rodar comando openssl: {str(e)}")
