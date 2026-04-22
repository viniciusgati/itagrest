import os
import binascii
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend

# 1. Configuração de Banco (Igual à aplicação)
DATABASE_URL = "postgresql://root:root@db:5432/itagrest_homolog"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("--- DEBUG FISCAL FINAL ---")

try:
    # 2. Busca Empresa
    from sqlalchemy import text
    empresa = db.execute(text("SELECT razao_social, certificado_senha, certificado_path, uf, ambiente FROM empresas LIMIT 1")).fetchone()
    
    if not empresa:
        print("ERRO: Nenhuma empresa cadastrada.")
    else:
        print(f"Empresa: {empresa.razao_social}")
        print(f"Ambiente: {empresa.ambiente} (2=Homologação)")
        
        # 3. Testa Caminho e Leitura
        path = empresa.certificado_path
        if not os.path.exists(path):
            path = os.path.join("storage/certs", os.path.basename(path))
            
        print(f"Tentando ler arquivo em: {path}")
        with open(path, "rb") as f:
            pfx_data = f.read()
        
        print(f"Tamanho PFX: {len(pfx_data)} bytes")
        
        # 4. Testa Senha
        password = empresa.certificado_senha
        password_bytes = password.strip().encode('utf-8')
        print(f"Senha DB: '{password}' | Hex: {binascii.hexlify(password_bytes)}")
        
        # 5. Tentativa de carga via Cryptography (Backend do ERPBrasil)
        try:
            # Tenta sem o legacy provider explicitamente primeiro
            pkcs12.load_key_and_certificates(pfx_data, password_bytes, default_backend())
            print("SUCESSO: Cryptography carregou o PFX!")
        except Exception as e:
            print(f"FALHA: Cryptography erro: {str(e)}")
            
            # Se falhar, tenta forçar o legacy provider se estivermos no OpenSSL 3
            try:
                import os
                os.environ["OPENSSL_CONF"] = "/app/openssl_legacy.cnf"
                # Força reload (em alguns sistemas isso ajuda)
                pkcs12.load_key_and_certificates(pfx_data, password_bytes, default_backend())
                print("SUCESSO: Cryptography carregou o PFX (COM LEGACY_CONF)!")
            except Exception as e2:
                print(f"FALHA: Mesmo com OPENSSL_CONF falhou: {str(e2)}")

        # 6. Teste de Importação das Classes Reais do Projeto
        try:
            from erpbrasil.assinatura.certificado import Certificado
            from erpbrasil.edoc.nfe import NFe
            
            cert = Certificado(pfx_data, password)
            print("SUCESSO: Classe Certificado (Projeto) carregada!")
            
            # 7. Teste de Conexão SEFAZ (Status do Serviço)
            # Isso valida se o certificado é aceito para SSL
            edoc = NFe(transmitir=True, certificado=cert, estado=empresa.uf, ambiente=str(empresa.ambiente), versao='4.00')
            status = edoc.status_servico()
            print(f"SUCESSO SEFAZ: Status do Serviço: {status.status} - {status.motivo}")
            
        except Exception as e:
            print(f"FALHA PROJETO: Erro nas classes reais: {str(e)}")
            print(traceback.format_exc())

finally:
    db.close()
