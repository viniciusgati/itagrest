
import pytest
import concurrent.futures
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.venda import Venda, StatusVenda

def abrir_mesa_task(mesa_id):
    client = TestClient(app)
    return client.post("/api/v1/vendas/", json={"mesa": mesa_id})

def test_stress_duplicate_openings():
    """
    Simula 10 tentativas simultâneas de abrir a mesma mesa.
    O sistema deve garantir que apenas UMA venda seja criada.
    """
    mesa_id = 99
    num_threads = 10
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(abrir_mesa_task, mesa_id) for _ in range(num_threads)]
        results = [f.result() for f in futures]
    
    # Todos devem retornar 200 (seja criando ou recuperando)
    for res in results:
        assert res.status_code == 200
        
    # Verificar no banco quantas vendas existem para a mesa 99 com status aberto
    db = SessionLocal()
    try:
        vendas = db.query(Venda).filter(
            Venda.mesa == mesa_id,
            Venda.status.in_([StatusVenda.ABERTA, StatusVenda.AGUARDANDO_PAGAMENTO])
        ).all()
        
        assert len(vendas) == 1, f"Deveria existir apenas 1 venda aberta para a mesa {mesa_id}, mas existem {len(vendas)}"
        
        # Limpeza
        for v in vendas:
            db.delete(v)
        db.commit()
    finally:
        db.close()
