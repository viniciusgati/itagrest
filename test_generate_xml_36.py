import os
import sys
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.venda import Venda
from app.models.empresa import Empresa
from app.services.sefaz import SefazService, DocumentoEletronico

def test_gen():
    db = SessionLocal()
    try:
        venda = db.query(Venda).filter(Venda.id == 36).first()
        empresa = db.query(Empresa).first()
        
        if not venda or not empresa:
            print("Venda 36 ou Empresa não encontrada no banco.")
            return

        print(f"Gerando XML para Venda {venda.id}...")
        chave = f"352604{empresa.cnpj.zfill(14)}65001{venda.id:09}1{venda.id:08}0"[:44]
        
        # 1. Monta o objeto
        nfe_obj = SefazService._montar_xml_nfce(empresa, venda, chave)
        
        # 2. Usa o método patcheado da lib para gerar a string (exatamente como o emitir_nfce faz)
        xml_string, _ = DocumentoEletronico()._generateds_to_string_etree(nfe_obj)
        
        # 3. Salva em arquivo
        with open("venda_36_generated.xml", "w") as f:
            f.write(xml_string)
            
        print("\nSUCESSO! XML gerado em: venda_36_generated.xml")
        print("\n--- INICIO DO XML (Primeiras 5 linhas) ---")
        print("\n".join(xml_string.split("\n")[:5]))
        print("\n--- FINAL DO XML (Onde fica o QR Code) ---")
        print(xml_string[-500:])
        
    finally:
        db.close()

if __name__ == "__main__":
    test_gen()
