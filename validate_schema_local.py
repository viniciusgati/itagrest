import os, subprocess, re
from lxml import etree

def validate():
    # 1. Busca o XML assinado da nota
    cmd = ["docker", "exec", "itagrest_db", "psql", "-U", "root", "-d", "itagrest_homolog", "-t", "-A", "-c", "SELECT xml_enviado FROM notas_fiscais WHERE venda_id = 36 ORDER BY id DESC LIMIT 1;"]
    xml_nota = subprocess.check_output(cmd).decode('utf-8').strip()

    if not xml_nota:
        print("Erro: Nenhum XML encontrado no banco.")
        return

    # Limpeza da declaração XML para não quebrar o lote
    xml_nota = re.sub(r'^\s*<\?xml.*?\?>', '', xml_nota)
    
    # 2. Monta o LOTE (enviNFe) conforme o código do SefazService
    id_lote = "36"
    lote_xml = f'<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><idLote>{id_lote}</idLote><indSinc>1</indSinc>{xml_nota}</enviNFe>'

    # 3. Carrega o Schema do LOTE
    schema_path = "PL_010c_NT2022_002v1.30/enviNFe_v4.00.xsd"
    
    class LocalResolver(etree.Resolver):
        def resolve(self, url, pubid, context):
            path = os.path.join("PL_010c_NT2022_002v1.30", url)
            if os.path.exists(path):
                return self.resolve_filename(path, context)
            return None

    parser_xsd = etree.XMLParser()
    parser_xsd.resolvers.add(LocalResolver())
    
    with open(schema_path, 'rb') as f:
        schema_root = etree.fromstring(f.read(), parser=parser_xsd)
        try:
            schema = etree.XMLSchema(schema_root)
        except Exception as e:
            print(f"Erro ao carregar Schema: {e}")
            return

    # 4. Valida o Lote completo
    try:
        xml_doc = etree.fromstring(lote_xml.encode('utf-8'))
        if schema.validate(xml_doc):
            print("\n✅ O LOTE (enviNFe) está 100% VÁLIDO localmente!")
        else:
            print("\n❌ ERRO DE SCHEMA NO LOTE:")
            for error in schema.error_log:
                print(f"Linha {error.line}, Col {error.column}: {error.message}")
    except Exception as e:
        print(f"Erro ao processar XML do Lote: {e}")

if __name__ == "__main__":
    validate()
