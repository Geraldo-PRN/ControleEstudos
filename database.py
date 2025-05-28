import sqlite3
import os
import json

DB_FOLDER = "databases"
CONFIG = "config.json"

def get_config_path():
    return CONFIG

def get_db_folder():
    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)
    return DB_FOLDER

def get_active_db():
    """Retorna o caminho do banco de dados ativo a partir do config.json ou define o padrão."""
    config_path = get_config_path()
    db_folder = get_db_folder()
    default_db = os.path.join(db_folder, "controle_estudos.db")
    if not os.path.exists(config_path):
        # Cria config apontando para o banco padrão, se não existir
        with open(config_path, "w") as f:
            json.dump({"active_db": default_db}, f)
        return default_db
    with open(config_path) as f:
        data = json.load(f)
    return data.get("active_db", default_db)

def set_active_db(db_path):
    """Define o banco de dados ativo no config.json"""
    with open(get_config_path(), "w") as f:
        json.dump({"active_db": db_path}, f)

def get_conn():
    db_path = get_active_db()
    return sqlite3.connect(db_path)

def setup_db():
    conn = get_conn()
    c = conn.cursor()
    # Disciplinas (agora com peso e questoes)
    c.execute("""
    CREATE TABLE IF NOT EXISTS disciplina (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        peso INTEGER DEFAULT 1,
        questoes INTEGER DEFAULT 1
    )""")
    # Materias
    c.execute("""
    CREATE TABLE IF NOT EXISTS materia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        disciplina_id INTEGER,
        FOREIGN KEY(disciplina_id) REFERENCES disciplina(id)
    )""")
    # Planejamento (agora com disciplina_id, meta_minutos, periodo_inicio/fim)
    c.execute("""
    CREATE TABLE IF NOT EXISTS planejamento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disciplina_id INTEGER,
        tipo TEXT,
        meta_minutos INTEGER,
        periodo_inicio DATE,
        periodo_fim DATE,
        FOREIGN KEY(disciplina_id) REFERENCES disciplina(id)
    )""")
    # Sessões de estudo
    c.execute("""
    CREATE TABLE IF NOT EXISTS sessao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        materia_id INTEGER,
        data TEXT,
        duracao INTEGER,
        tipo TEXT,
        anotacoes TEXT,
        disciplina_id INTEGER,
        FOREIGN KEY(materia_id) REFERENCES materia(id),
        FOREIGN KEY(disciplina_id) REFERENCES disciplina(id)
    )""")
    # Revisões
    c.execute("""
    CREATE TABLE IF NOT EXISTS revisao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sessao_id INTEGER,
        materia_id INTEGER,
        data_revisao DATE,
        realizada INTEGER DEFAULT 0,
        tipo TEXT,
        FOREIGN KEY(sessao_id) REFERENCES sessao(id),
        FOREIGN KEY(materia_id) REFERENCES materia(id)
    )""")
    # Questões e Simulados (NOVO)
    c.execute("""
    CREATE TABLE IF NOT EXISTS questoes_simulado (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data DATE NOT NULL,
        tipo TEXT NOT NULL, -- 'Questões' ou 'Simulado'
        disciplina_id INTEGER,
        materia_id INTEGER,
        total_questoes INTEGER NOT NULL,
        acertos INTEGER,
        observacao TEXT,
        descricao TEXT,
        FOREIGN KEY (disciplina_id) REFERENCES disciplina(id),
        FOREIGN KEY (materia_id) REFERENCES materia(id)
    )""")
    # Cronograma semanal (NOVA TABELA)
    c.execute("""
    CREATE TABLE IF NOT EXISTS cronograma (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dia_semana TEXT NOT NULL,         -- "Segunda", "Terça", ...
        periodo TEXT NOT NULL,            -- "Manhã", "Tarde", "Noite"
        disciplina_id INTEGER,            -- FK para disciplina
        atividade TEXT,                   -- "Aula", "Questões", "Revisão", etc
        concluido INTEGER DEFAULT 0,      -- 0 = não, 1 = sim
        prioridade INTEGER DEFAULT 1,     -- Prioridade (1=normal, pode ser maior para mais importante)
        observacao TEXT,                  -- Notas rápidas
        data_ref DATE,                    -- Opcional: referência para cronogramas semanais diferentes
        FOREIGN KEY(disciplina_id) REFERENCES disciplina(id)
    )""")
    conn.commit()
    conn.close()

def listar_bancos():
    """Lista todos os bancos de dados disponíveis na pasta databases."""
    db_folder = get_db_folder()
    return [f for f in os.listdir(db_folder) if f.endswith(".db")]

def criar_novo_banco(nome_db):
    """Cria um novo banco de dados com o nome informado e inicializa suas tabelas."""
    db_folder = get_db_folder()
    new_db_path = os.path.join(db_folder, f"{nome_db}.db")
    # Cria o arquivo vazio e inicializa as tabelas
    set_active_db(new_db_path)
    setup_db()
    return new_db_path