import xml.etree.ElementTree as ET
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.produto import Produto, CategoriaEnum

class MigracaoService:
    @staticmethod
    def importar_produtos_xml(xml_content: bytes, db: Session):
        """
        Faz o parse do XML legado e importa para o banco de dados do iTagREST.
        Lida com conversão de preços e extração de dados fiscais da string CST.
        """
        root = ET.fromstring(xml_content)
        count = 0
        
        for p_node in root.findall('Produto'):
            try:
                # Extrair dados básicos com fallback para vazio
                desc_node = p_node.find('Descritivo')
                descricao = desc_node.text.strip() if desc_node is not None and desc_node.text else "PRODUTO SEM DESCRICAO"
                
                preco_node = p_node.find('PrecoUnitario')
                preco_str = preco_node.text.replace(',', '.') if preco_node is not None and preco_node.text else "0.00"
                
                unidade_node = p_node.find('Un')
                unidade = unidade_node.text.strip() if unidade_node is not None and unidade_node.text else "UN"
                
                # Parsing da string CST: "NCM;CST_ICMS;CST_PIS;ORIGEM;CST_COFINS;ALIQ_PIS;ALIQ_COF;CEST;"
                cst_node = p_node.find('CST')
                cst_raw = cst_node.text if cst_node is not None else ""
                cst_parts = cst_raw.split(';') if cst_raw else []
                
                # Mapeamento seguro das partes
                ncm = cst_parts[0] if len(cst_parts) > 0 else "00000000"
                cst_icms = cst_parts[1] if len(cst_parts) > 1 else "000"
                cst_pis = cst_parts[2] if len(cst_parts) > 2 else "07"
                origem = cst_parts[3] if len(cst_parts) > 3 else "0"
                cst_cofins = cst_parts[4] if len(cst_parts) > 4 else "07"
                
                # Alíquotas com fallback seguro
                aliquota_pis = Decimal("0.00")
                if len(cst_parts) > 5 and cst_parts[5]:
                    try: aliquota_pis = Decimal(cst_parts[5])
                    except: pass
                    
                aliquota_cofins = Decimal("0.00")
                if len(cst_parts) > 6 and cst_parts[6]:
                    try: aliquota_cofins = Decimal(cst_parts[6])
                    except: pass
                    
                cest = cst_parts[7] if len(cst_parts) > 7 else None

                # Detectar Categoria baseada na descrição (Heurística simples)
                categoria = CategoriaEnum.REFEICAO
                desc_upper = descricao.upper()
                if any(x in desc_upper for x in ['SUCO', 'COCA', 'AGUA', 'CERVEJA', 'SCHWEPPES', 'BEBIDA']):
                    categoria = CategoriaEnum.BEBIDA
                elif any(x in desc_upper for x in ['SORV', 'CHOC', 'TWIX', 'M&M', 'SNICKERS']):
                    categoria = CategoriaEnum.OUTROS

                # Validação de dados obrigatórios antes de persistir
                try:
                    preco_venda = Decimal(preco_str)
                except Exception:
                    print(f"AVISO: Pulando produto '{descricao}' por preço inválido: {preco_str}")
                    continue

                # Criar ou Atualizar Produto
                produto = db.query(Produto).filter(Produto.descricao == descricao).first()
                if not produto:
                    produto = Produto(descricao=descricao)
                    db.add(produto)
                
                produto.preco_venda = preco_venda
                produto.unidade = unidade
                produto.categoria = categoria
                produto.ncm = ncm.strip()[:8].zfill(8) # Garante 8 dígitos
                produto.cfop = "5102"
                produto.origem = origem
                produto.cst_icms = cst_icms
                produto.cst_pis = cst_pis
                produto.cst_cofins = cst_cofins
                produto.aliquota_pis = aliquota_pis
                produto.aliquota_cofins = aliquota_cofins
                produto.cest = cest.strip()[:7] if cest else None
                
                count += 1
            except Exception as p_err:
                print(f"ERRO: Falha ao processar produto no XML: {str(p_err)}")
                continue # Pula o produto com erro e continua a importação
            
        db.commit()
        return count
