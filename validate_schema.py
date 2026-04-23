import os
import requests
import zipfile
import io
from lxml import etree

SCHEMAS_DIR = "storage/schemas"
ZIP_URL = "http://www.nfe.fazenda.gov.br/portal/exibirArquivo.aspx?conteudo=96V6OonWv/Y=" # PL_009_v4.00_nt2023.004

def download_schemas():
    if not os.path.exists(SCHEMAS_DIR):
        os.makedirs(SCHEMAS_DIR)
    
    print(f"Baixando esquemas de {ZIP_URL}...")
    # SEFAZ bloqueia bots simples, vamos usar um User-Agent comum
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(ZIP_URL, headers=headers)
    
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(SCHEMAS_DIR)
        print("Esquemas extraídos com sucesso.")
    else:
        print(f"Falha ao baixar esquemas: {response.status_code}")

def validate_xml(xml_string):
    # Procura o arquivo principal do esquema
    xsd_file = os.path.join(SCHEMAS_DIR, "enviNFe_v4.00.xsd")
    if not os.path.exists(xsd_file):
        print(f"Arquivo XSD não encontrado: {xsd_file}")
        return

    try:
        # Carrega o esquema
        with open(xsd_file, 'rb') as f:
            schema_root = etree.XML(f.read())
            # Ajusta caminhos relativos se necessário (lxml lida bem se estiverem na mesma pasta)
            schema = etree.XMLSchema(schema_root)
        
        # Carrega o XML (emoldurado em enviNFe para bater com o XSD de lote)
        parser = etree.XMLParser(remove_blank_text=True)
        xml_node = etree.fromstring(xml_string.encode('utf-8'), parser)
        
        # Validação
        if schema.validate(xml_node):
            print("XML VÁLIDO de acordo com o Schema!")
        else:
            print("XML INVÁLIDO!")
            for error in schema.error_log:
                print(f"LINHA {error.line}: {error.message}")

    except Exception as e:
        print(f"Erro no validador: {e}")

if __name__ == "__main__":
    if not os.listdir(SCHEMAS_DIR):
        download_schemas()
    
    # Aqui vamos pegar o último XML enviado do banco
    print("\nLendo último XML enviado do banco...")
    import subprocess
    cmd = "docker exec itagrest_db psql -U root -d itagrest_homolog -t -c \"SELECT xml_enviado FROM notas_fiscais ORDER BY id DESC LIMIT 1;\""
    xml_data = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
    
    if xml_data:
        # O XSD de lote (enviNFe) espera um envelope <enviNFe>
        # Vamos envolver a nota se ela estiver solta
        if "<enviNFe" not in xml_data:
            xml_data = f'<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><idLote>1</idLote><indSinc>1</indSinc>{xml_data}</enviNFe>'
        
        validate_xml(xml_data)
    else:
        print("Nenhum XML encontrado no banco.")

