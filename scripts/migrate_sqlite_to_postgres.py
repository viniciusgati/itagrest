import sqlite3
import os
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.produto import Produto
from app.models.venda import Venda, VendaItem
from app.models.nota_fiscal import NotaFiscal

# Configurações
SQLITE_PATH = "test.db"
POSTGRES_URL = "postgresql://root:root@localhost:5432/itagrest_homolog"

def migrate():
    if not os.path.exists(SQLITE_PATH):
        print(f"Erro: Arquivo {SQLITE_PATH} não encontrado.")
        return

    # Conectar no SQLite (Origem)
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    
    # Conectar no Postgres (Destino)
    pg_engine = create_engine(POSTGRES_URL)
    Session = sessionmaker(bind=pg_engine)
    pg_session = Session()

    print("🚀 Iniciando migração de dados...")

    try:
        # 1. MIGRAR USUÁRIOS
        print("Migrando Usuários...")
        users = sqlite_conn.execute("SELECT * FROM usuarios").fetchall()
        for u in users:
            if not pg_session.get(Usuario, u['id']):
                pg_session.add(Usuario(
                    id=u['id'], username=u['username'], email=u['email'], 
                    hashed_password=u['hashed_password'], is_active=u['is_active']
                ))

        # 2. MIGRAR EMPRESA
        print("Migrando Configuração Fiscal...")
        empresas = sqlite_conn.execute("SELECT * FROM empresas").fetchall()
        for e in empresas:
            if not pg_session.get(Empresa, e['id']):
                pg_session.add(Empresa(
                    id=e['id'], cnpj=e['cnpj'], razao_social=e['razao_social'],
                    inscricao_estadual=e['inscricao_estadual'], logradouro=e.get('logradouro'),
                    numero=e.get('numero'), bairro=e.get('bairro'), municipio_nome=e.get('municipio_nome'),
                    uf=e.get('uf'), cep=e.get('cep'), ambiente=e.get('ambiente', 2), 
                    csc_token=e.get('csc_token'), csc_id=e.get('csc_id'),
                    certificado_path=e.get('certificado_path'), certificado_senha=e.get('certificado_senha'),
                    configurado=e.get('configurado', False), pix_chave=e.get('pix_chave')
                ))

        # 3. MIGRAR PRODUTOS
        print("Migrando Cardápio...")
        prods = sqlite_conn.execute("SELECT * FROM produtos").fetchall()
        for p in prods:
            if not pg_session.get(Produto, p['id']):
                pg_session.add(Produto(
                    id=p['id'], descricao=p['descricao'], preco_venda=p['preco_venda'],
                    unidade=p.get('unidade'), categoria=p.get('categoria'), imagem_url=p.get('imagem_url'),
                    ncm=p.get('ncm'), cest=p.get('cest'), cfop=p.get('cfop'), origem=p.get('origem'),
                    cst_icms=p.get('cst_icms'), cst_pis=p.get('cst_pis'), cst_cofins=p.get('cst_cofins'),
                    aliquota_pis=p.get('aliquota_pis', 0), aliquota_cofins=p.get('aliquota_cofins', 0),
                    aliquota_icms=p.get('aliquota_icms', 0)
                ))

        # 4. MIGRAR VENDAS
        print("Migrando Histórico de Vendas...")
        vendas = sqlite_conn.execute("SELECT * FROM vendas").fetchall()
        for v in vendas:
            if not pg_session.get(Venda, v['id']):
                pg_session.add(Venda(
                    id=v['id'], mesa=v['mesa'], total=v['total'], status=v['status'],
                    forma_pagamento=v.get('forma_pagamento'), data_abertura=v['data_abertura'],
                    data_fechamento=v.get('data_fechamento'), pix_payload=v.get('pix_payload'),
                    pix_expiracao=v.get('pix_expiracao')
                ))

        # 5. MIGRAR ITENS
        print("Migrando Itens das Comandas...")
        itens = sqlite_conn.execute("SELECT * FROM venda_itens").fetchall()
        for i in itens:
            # Verifica se o produto e a venda existem no destino para evitar erro de FK
            if pg_session.get(Produto, i['produto_id']) and pg_session.get(Venda, i['venda_id']):
                if not pg_session.get(VendaItem, i['id']):
                    pg_session.add(VendaItem(
                        id=i['id'], venda_id=i['venda_id'], produto_id=i['produto_id'],
                        quantidade=i['quantidade'], preco_unitario=i['preco_unitario'],
                        subtotal=i['subtotal']
                    ))
            else:
                print(f"⚠️ Pulando item órfão #{i['id']} (Venda {i['venda_id']} ou Produto {i['produto_id']} não existem)")

        pg_session.commit()
        
        # 6. SINCRONIZAR SEQUÊNCIAS
        print("Sincronizando sequências de ID...")
        tables = ['usuarios', 'empresas', 'produtos', 'vendas', 'venda_itens', 'notas_fiscais']
        for table in tables:
            pg_session.execute(text(f"SELECT setval('{table}_id_seq', (SELECT COALESCE(MAX(id), 1) FROM {table}))"))
        
        pg_session.commit()
        print("✅ Migração concluída com sucesso para o PostgreSQL!")

    except Exception as err:
        pg_session.rollback()
        print(f"❌ Erro durante a migração: {str(err)}")
    finally:
        sqlite_conn.close()
        pg_session.close()

if __name__ == "__main__":
    migrate()
