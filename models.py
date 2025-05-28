from database import get_conn

class Disciplina:
    @staticmethod
    def criar(nome):
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO disciplina (nome) VALUES (?)", (nome,))
        conn.commit()
        conn.close()

    @staticmethod
    def listar():
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, nome FROM disciplina")
        disciplinas = c.fetchall()
        conn.close()
        return disciplinas

    @staticmethod
    def editar(id, novo_nome):
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE disciplina SET nome=? WHERE id=?", (novo_nome, id))
        conn.commit()
        conn.close()

    @staticmethod
    def remover(id):
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM disciplina WHERE id=?", (id,))
        conn.commit()
        conn.close()

class Materia:
    @staticmethod
    def criar(nome, disciplina_id):
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO materia (nome, disciplina_id) VALUES (?,?)", (nome, disciplina_id))
        conn.commit()
        conn.close()

    @staticmethod
    def listar():
        conn = get_conn()
        c = conn.cursor()
        c.execute("""SELECT materia.id, materia.nome, disciplina.nome
                     FROM materia LEFT JOIN disciplina ON disciplina.id = materia.disciplina_id""")
        materias = c.fetchall()
        conn.close()
        return materias

    @staticmethod
    def editar(id, novo_nome, nova_disciplina_id):
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE materia SET nome=?, disciplina_id=? WHERE id=?", (novo_nome, nova_disciplina_id, id))
        conn.commit()
        conn.close()

    @staticmethod
    def remover(id):
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM materia WHERE id=?", (id,))
        conn.commit()
        conn.close()