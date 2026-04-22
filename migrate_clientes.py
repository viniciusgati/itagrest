import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

# Configurações
SQLITE_DB = 'test.db'
POSTGRES_CONFIG = {
    'dbname': 'itagrest_homolog',
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'port': 5433
}

def migrate():
    print(f"📦 Iniciando migração de clientes: {SQLITE_DB} -> Docker Postgres (Port 5433)")
    
    try:
        # 1. Conectar no SQLite
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cur = sqlite_conn.cursor()
        
        # Buscar clientes
        sqlite_cur.execute("SELECT * FROM cliente")
        clientes = sqlite_cur.fetchall()
        print(f"🔍 Encontrados {len(clientes)} clientes no banco local.")
        
        if not clientes:
            print("⚠️ Nenhum cliente para migrar.")
            return

        # 2. Conectar no Postgres (Docker)
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        pg_cur = pg_conn.cursor()

        # 3. Inserir no Postgres
        migrados = 0
        for cli in clientes:
            try:
                pg_cur.execute(
                    """
                    INSERT INTO cliente (nome, documento, email, telefone, endereco, created_at, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (documento) DO NOTHING
                    """,
                    (cli['nome'], cli['documento'], cli['email'], cli['telefone'], cli['endereco'], cli['created_at'], cli['is_active'])
                )
                migrados += 1
            except Exception as e:
                print(f"❌ Erro ao migrar cliente {cli['nome']}: {e}")

        pg_conn.commit()
        print(f"✅ Sucesso! {migrados} clientes migrados para o ambiente Docker.")

    except Exception as e:
        print(f"💥 Erro fatal na migração: {e}")
    finally:
        if sqlite_conn: sqlite_conn.close()
        if pg_conn: pg_conn.close()

if __name__ == "__main__":
    migrate()
