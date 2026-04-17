
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.venda import Venda, VendaItem, StatusVenda
from app.models.produto import Produto
from app.models.cliente import Cliente
from app.models.empresa import Empresa
from sqlalchemy.orm import joinedload

def test_venda_items():
    db = SessionLocal()
    try:
        # Pega todas as vendas
        vendas = db.query(Venda).options(
            joinedload(Venda.itens),
            joinedload(Venda.cliente)
        ).all()

        if not vendas:
            print("Nenhuma venda encontrada.")
            return

        print(f"Total de vendas encontradas: {len(vendas)}")
        
        for venda in vendas:
            print(f"\nVenda ID: {venda.id}, Mesa: {venda.mesa}, Status: {venda.status}, Total: {venda.total}")
            print(f"Quantidade de itens: {len(venda.itens)}")
            
            for item in venda.itens:
                print(f"  - Item ID: {item.id}, Produto ID: {item.produto_id}, Quantidade: {item.quantidade}")
                if item.produto:
                    print(f"    Produto: {item.produto.descricao}, Preço Venda: {item.produto.preco_venda}")
                else:
                    print("    ERRO: Produto não carregado!")
    finally:
        db.close()

if __name__ == "__main__":
    test_venda_items()
