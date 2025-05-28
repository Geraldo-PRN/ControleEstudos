import tkinter as tk
from tkinter import ttk, messagebox
from database import get_conn
from datetime import date, timedelta
import matplotlib.pyplot as plt

class GraficosFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.build()

    def build(self):
        tk.Label(self, text="Relatórios e Gráficos", font=("Arial", 13)).place(x=10, y=10)
        tk.Button(self, text="Tempo por matéria (mês)", command=self.graf_tempo_materia_mes).place(x=10, y=50)
        tk.Button(self, text="Tempo por dia (últ. 7 dias)", command=self.graf_tempo_dia).place(x=200, y=50)
        tk.Button(self, text="Progresso das metas", command=self.graf_progresso_metas).place(x=400, y=50)

    def graf_tempo_materia_mes(self):
        conn = get_conn()
        c = conn.cursor()
        mes_ini = date.today().replace(day=1).isoformat()
        c.execute('''SELECT m.nome, SUM(s.duracao) FROM sessao s
                     JOIN materia m ON m.id = s.materia_id
                     WHERE s.data_inicio >= ?
                     GROUP BY m.id''', (mes_ini,))
        dados = c.fetchall()
        conn.close()
        if not dados:
            messagebox.showinfo("Gráfico", "Nenhum dado para o mês.")
            return
        nomes = [d[0] for d in dados]
        valores = [d[1] for d in dados]
        plt.figure(figsize=(7,4))
        plt.bar(nomes, valores)
        plt.ylabel('Minutos')
        plt.title('Tempo estudado por matéria (mês)')
        plt.tight_layout()
        plt.show()

    def graf_tempo_dia(self):
        conn = get_conn()
        c = conn.cursor()
        hoje = date.today()
        dias = [(hoje - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
        valores = []
        for d in dias:
            c.execute('''SELECT SUM(duracao) FROM sessao
                         WHERE date(data_inicio)=?''', (d,))
            v = c.fetchone()[0] or 0
            valores.append(v)
        conn.close()
        plt.figure(figsize=(7,4))
        plt.plot(dias, valores, marker='o')
        plt.title('Tempo estudado por dia (últimos 7 dias)')
        plt.ylabel('Minutos')
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.show()

    def graf_progresso_metas(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute('''SELECT p.id, m.nome, p.tipo, p.meta_minutos, p.periodo_inicio, p.periodo_fim
                     FROM planejamento p
                     JOIN materia m ON m.id = p.materia_id''')
        metas = c.fetchall()
        nomes, percentuais = [], []
        for pid, nome, tipo, meta, ini, fim in metas:
            c.execute('''SELECT SUM(duracao) FROM sessao
                         WHERE materia_id=? AND date(data_inicio)>=? AND date(data_fim)<=?''',
                         (pid, ini, fim))
            feito = c.fetchone()[0] or 0
            perc = min(100, int(100 * feito/meta)) if meta > 0 else 0
            nomes.append(f"{nome}-{tipo}")
            percentuais.append(perc)
        conn.close()
        if not nomes:
            messagebox.showinfo("Metas", "Nenhuma meta cadastrada.")
            return
        plt.figure(figsize=(7,4))
        plt.bar(nomes, percentuais)
        plt.ylabel('% Concluído')
        plt.title('Progresso das Metas')
        plt.tight_layout()
        plt.show()