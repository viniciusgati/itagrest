
import random
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.venda import Venda, VendaItem, StatusVenda, FormaPagamento
from app.models.produto import Produto
from app.models.cliente import Cliente

def seed_data():
    db = SessionLocal()
    try:
        # 1. Garantir Produtos
        produtos = db.query(Produto).all()
        if not produtos:
            prods_data = [
                {"descricao": "CERVEJA LATA", "preco_venda": 7.50, "categoria": "BEBIDA"},
                {"descricao": "MARMITA MEDIA", "preco_venda": 18.00, "categoria": "REFEICAO"},
                {"descricao": "REFRIGERANTE 600ML", "preco_venda": 6.00, "categoria": "BEBIDA"},
                {"descricao": "SUCO NATURAL", "preco_venda": 9.00, "categoria": "BEBIDA"},
                {"descricao": "PRATO FEITO", "preco_venda": 22.00, "categoria": "REFEICAO"},
            ]
            for p in prods_data:
                new_p = Produto(**p, unidade="UN", ncm="22030000", cfop="5102")
                db.add(new_p)
            db.commit()
            produtos = db.query(Produto).all()

        # 2. Garantir Clientes
        clientes = db.query(Cliente).all()
        if not clientes:
            clis_data = [
                {"nome": "João da Silva", "documento": "12345678901"},
                {"nome": "Maria Oliveira", "documento": "98765432100"},
            ]
            for c in clis_data:
                db.add(Cliente(**c))
            db.commit()
            clientes = db.query(Cliente).all()

        # 3. Gerar Vendas (Últimos 365 dias)
        print("Gerando dados de vendas dos últimos 12 meses...")
        hoje = datetime.utcnow()
        vendas_criadas = 0
        
        # Vamos gerar entre 2 a 8 vendas por dia para dar volume
        for i in range(365):
            data_venda = hoje - timedelta(days=i)
            # Menos vendas nos meses mais antigos, mais nas recentes
            num_vendas = random.randint(2, 10)
            
            for _ in range(num_vendas):
                venda = Venda(
                    mesa=random.randint(1, 12),
                    status=StatusVenda.PAGA,
                    data_abertura=data_venda - timedelta(hours=random.randint(1, 5)),
                    data_fechamento=data_venda,
                    forma_pagamento=random.choice(list(FormaPagamento)),
                    cliente_id=random.choice(clientes).id if random.random() > 0.7 else None
                )
                db.add(venda)
                db.flush() # Para pegar o ID
                
                # Itens da venda
                total_venda = Decimal("0.00")
                for _ in range(random.randint(1, 4)):
                    p = random.choice(produtos)
                    qtd = random.randint(1, 3)
                    subtotal = Decimal(qtd) * p.preco_venda
                    item = VendaItem(
                        venda_id=venda.id,
                        produto_id=p.id,
                        quantidade=qtd,
                        preco_unitario=p.preco_venda,
                        subtotal=subtotal
                    )
                    db.add(item)
                    total_venda += subtotal
                
                venda.total = total_venda
                vendas_criadas += 1
                
            if i % 30 == 0:
                db.commit()
                print(f"Processado: {i} dias...")

        db.commit()
        print(f"Sucesso! {vendas_criadas} vendas geradas.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
