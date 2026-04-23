import io
import os
import sys
sys.path.insert(0, os.path.abspath('temp_libs'))

from nfelib.v4_00 import leiauteNFe as nfe

# 1. Simulação do Patch (conforme está no seu código)
def apply_patch(module):
    def wrap_export(old_export):
        def new_export(self, outfile, level, namespace_='', name_=None, namespacedef_='xmlns="http://www.portalfiscal.inf.br/nfe"', pretty_print=True):
            if not name_:
                name_ = self.__class__.__name__.replace('Type', '')
                if name_ == 'TNFe': name_ = 'NFe'
            buf = io.StringIO()
            old_export(self, buf, level, '', name_, namespacedef_, pretty_print)
            content = buf.getvalue().replace('editix:', '').replace('xmlns:editix="http://www.portalfiscal.inf.br/nfe"', '')
            outfile.write(content)
        return new_export
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and hasattr(obj, 'export'):
            obj.export = wrap_export(obj.export)

apply_patch(nfe)

# 2. Simulação da Montagem da Nota
chave = "35260449112135000138650010000000351000000350"
inf_nfe = nfe.infNFeType(Id=f"NFe{chave}", versao="4.00", ide=nfe.ideType(cUF='35', mod='65', serie='1', nNF='35', dhEmi='2026-04-22T22:38:50-03:00', tpAmb='1', tpImp='4', tpEmis='1', cDV='0', cNF='1', idDest='1', indFinal='1', indPres='1', procEmi='0', verProc='1.0', tpNF='1', cMunFG='3550308'), emit=nfe.emitType(CNPJ='49112135000138', xNome='TESTE', IE='123', CRT='1', enderEmit=nfe.TEnderEmi(xLgr='A', nro='1', xBairro='B', cMun='3550308', xMun='S', UF='SP', CEP='01000000', cPais='1058', xPais='B')), det=[nfe.detType(nItem='1', prod=nfe.prodType(cProd='1', xProd='P', NCM='123', CFOP='5102', uCom='UN', qCom='1', vUnCom='1', vProd='1', cEANTrib='', uTrib='UN', qTrib='1', vUnTrib='1', indTot='1'), imposto=nfe.impostoType())], total=nfe.totalType(ICMSTot=nfe.ICMSTotType(vBC='0', vICMS='0', vICMSDeson='0', vFCP='0', vBCST='0', vST='0', vFCPST='0', vFCPSTRet='0', vProd='1', vFrete='0', vSeg='0', vDesc='0', vII='0', vIPI='0', vIPIDevol='0', vPIS='0', vCOFINS='0', vOutro='0', vNF='1')), pag=nfe.pagType(detPag=[nfe.detPagType(tPag='01', vPag='1')]))
nota_obj = nfe.TNFe(infNFe=inf_nfe)

# O ponto crítico: Criar a tag ANTES da atribuição
nota_obj.infNFeSupl = nfe.infNFeSuplType(qrCode="http://placeholder.url", urlChave="http://placeholder.url")

print("--- XML EXPORTADO ANTES DO AJUSTE ---")
out = io.StringIO()
nota_obj.export(out, 0)
print(out.getvalue()[-350:])

# 3. Aplicando ajuste (igual ao emitir_nfce)
print("\n--- APLICANDO AJUSTE MANUAL NO OBJETO ---")
nota_obj.infNFeSupl.qrCode = "https://sefaz.sp.gov.br/qrcode?p=35260449112135000138650010000000351000000350|2|1|01|HASH_TESTE"
nota_obj.infNFeSupl.urlChave = "https://sefaz.sp.gov.br/consulta"

print("--- XML EXPORTADO APÓS O AJUSTE ---")
out2 = io.StringIO()
nota_obj.export(out2, 0)
xml_final = out2.getvalue()
print(xml_final[-350:])

if "placeholder" in xml_final:
    print("\n[RESULTADO] FALHA: O XML AINDA CONTÉM O PLACEHOLDER!")
else:
    print("\n[RESULTADO] SUCESSO: O XML FOI ATUALIZADO CORRETAMENTE.")

