from database import get_conn

conn = get_conn()
c = conn.cursor()
try:
    c.execute("ALTER TABLE questoes_simulado ADD COLUMN descricao TEXT;")
    conn.commit()
    print("Coluna 'descricao' adicionada com sucesso!")
except Exception as e:
    print("Coluna 'descricao' já existe ou erro:", e)
conn.close()