import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import get_conn

class PlanejamentoFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.build()
        self.refresh_disciplinas()
        self.refresh_planejamento()
        self.horas_semanais = 0

    def build(self):
        self.configure(bg="#f7fafd")
        tk.Label(self, text="Planejamento Inteligente", font=("Arial", 17, "bold"),
                 bg="#f7fafd", fg="#154b7c", anchor="center").pack(fill="x", padx=20, pady=(14, 2))

        frame_top = tk.Frame(self, bg="#f7fafd")
        frame_top.pack(fill="x", padx=20, pady=5)

        # Horas disponíveis semanais
        tk.Label(frame_top, text="Horas disponíveis/semana:", font=("Arial", 11, "bold"),
                 bg="#f7fafd", fg="#174a6a").grid(row=0, column=0, sticky="e", padx=(2,4), pady=6)
        self.entry_horas_semana = ttk.Entry(frame_top, width=10)
        self.entry_horas_semana.grid(row=0, column=1, sticky="w", padx=(0,18), pady=6)
        self.entry_horas_semana.insert(0, "20")

        self.btn_atualizar = tk.Button(frame_top, text="Atualizar", command=self.refresh_planejamento,
                                       font=("Arial", 10, "bold"), bg="#a3d5ff", fg="#174a6a", bd=0, width=10)
        self.btn_atualizar.grid(row=0, column=2, padx=(0,10), pady=6)

        # Cadastro de disciplina, peso, questões
        frame_disc = tk.LabelFrame(self, text="Disciplinas", bg="#f7fafd", font=("Arial", 11, "bold"))
        frame_disc.pack(fill="x", padx=20, pady=(8, 6))

        tk.Label(frame_disc, text="Disciplina:", font=("Arial", 11), bg="#f7fafd").grid(row=0, column=0, sticky="e", padx=(2,4), pady=6)
        self.combo_disciplina = ttk.Combobox(frame_disc, width=25, state="readonly")
        self.combo_disciplina.grid(row=0, column=1, sticky="w", padx=(0,10), pady=6)

        tk.Label(frame_disc, text="Peso:", font=("Arial", 11), bg="#f7fafd").grid(row=0, column=2, sticky="e", padx=(2,4), pady=6)
        self.entry_peso = ttk.Entry(frame_disc, width=7)
        self.entry_peso.grid(row=0, column=3, sticky="w", padx=(0,10), pady=6)

        tk.Label(frame_disc, text="Questões na prova:", font=("Arial", 11), bg="#f7fafd").grid(row=0, column=4, sticky="e", padx=(2,4), pady=6)
        self.entry_questoes = ttk.Entry(frame_disc, width=9)
        self.entry_questoes.grid(row=0, column=5, sticky="w", padx=(0,10), pady=6)

        self.btn_salvar = tk.Button(frame_disc, text="Salvar dados", command=self.salvar_dados_disciplina,
                                   font=("Arial", 10, "bold"), bg="#a3d5ff", fg="#174a6a", bd=0, width=12)
        self.btn_salvar.grid(row=0, column=6, padx=(8,6), pady=6)

        for col in range(7):
            frame_disc.grid_columnconfigure(col, weight=1)

        # Tabela de planejamento/sugestão
        frame_table = tk.Frame(self, bg="#f7fafd")
        frame_table.pack(fill="both", expand=True, padx=22, pady=(5, 12))

        # Coluna Progresso como segunda coluna!
        columns = ("Disciplina", "Progresso", "Peso", "Questões", "% Prova", "Horas Sugeridas", "Horas Estudadas")
        self.tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=12)
        style = ttk.Style()
        style.configure("Treeview", background="#fff", foreground="#1c3144", fieldbackground="#f5fafd", font=("Arial", 11), rowheight=28)
        style.configure("Treeview.Heading", background="#eaf4fb", foreground="#174a6a", font=("Arial", 11, "bold"))
        self.tree.tag_configure("odd", background="#f5fafd")
        self.tree.tag_configure("even", background="#eaf4fb")

        # Ajuste de largura das colunas conforme solicitado
        self.tree.heading("Disciplina", text="Disciplina")
        self.tree.column("Disciplina", anchor="center", minwidth=120, width=200)

        self.tree.heading("Progresso", text="Progresso")
        self.tree.column("Progresso", anchor="center", minwidth=120, width=170)

        self.tree.heading("Peso", text="Peso")
        self.tree.column("Peso", anchor="center", minwidth=40, width=70)

        self.tree.heading("Questões", text="Questões")
        self.tree.column("Questões", anchor="center", minwidth=40, width=70)

        self.tree.heading("% Prova", text="% Prova")
        self.tree.column("% Prova", anchor="center", minwidth=70, width=70)

        self.tree.heading("Horas Sugeridas", text="Horas Sugeridas")
        self.tree.column("Horas Sugeridas", anchor="center", minwidth=70, width=120)

        self.tree.heading("Horas Estudadas", text="Horas Estudadas")
        self.tree.column("Horas Estudadas", anchor="center", minwidth=70, width=120)

        self.tree.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def refresh_disciplinas(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, nome FROM disciplina")
        self.disciplina_nome_id = {}  # dicionário nome -> id
        nomes = []
        for id, nome in c.fetchall():
            self.disciplina_nome_id[nome] = id
            nomes.append(nome)
        self.combo_disciplina['values'] = nomes  # Só mostra o nome
        conn.close()
        if nomes:
            self.combo_disciplina.current(0)

    def salvar_dados_disciplina(self):
        disc_sel = self.combo_disciplina.get()
        peso = self.entry_peso.get().strip()
        questoes = self.entry_questoes.get().strip()
        if not (disc_sel and peso and questoes):
            messagebox.showwarning("Planejamento", "Preencha todos os campos!")
            return
        try:
            peso = int(peso)
            questoes = int(questoes)
            if peso <= 0 or questoes < 0:
                raise Exception()
        except Exception:
            messagebox.showwarning("Planejamento", "Peso e Questões devem ser números positivos!")
            return
        # Aqui está o ajuste: pega o id pelo nome
        disciplina_id = self.disciplina_nome_id.get(disc_sel)
        if disciplina_id is None:
            messagebox.showwarning("Planejamento", "Selecione uma disciplina válida!")
            return
        conn = get_conn()
        c = conn.cursor()
        # Atualiza dados na tabela disciplina
        c.execute(
            '''UPDATE disciplina SET peso=?, questoes=? WHERE id=?''',
            (peso, questoes, disciplina_id)
        )
        conn.commit()
        conn.close()
        self.entry_peso.delete(0, tk.END)
        self.entry_questoes.delete(0, tk.END)
        self.combo_disciplina.set("")
        self.refresh_planejamento()

    def obter_horas_estudadas(self, dados_disc):
        # Retorna {disciplina_id: total_horas_estudadas}
        conn = get_conn()
        c = conn.cursor()
        # Soma as durações (em minutos) das sessões por disciplina
        c.execute("""
            SELECT disciplina_id, SUM(duracao)
            FROM sessao
            WHERE disciplina_id IS NOT NULL
            GROUP BY disciplina_id
        """)
        resultado = c.fetchall()
        conn.close()
        # Converte minutos para horas e monta o dicionário
        horas_por_disciplina = {row[0]: (row[1] or 0) / 60 for row in resultado}
        # Garante que todas as disciplinas estejam presentes no dicionário
        for disc in dados_disc:
            if disc[0] not in horas_por_disciplina:
                horas_por_disciplina[disc[0]] = 0
        return horas_por_disciplina

    def refresh_planejamento(self):
        # Lê horas disponíveis
        try:
            self.horas_semanais = float(self.entry_horas_semana.get().replace(",", "."))
            if self.horas_semanais <= 0:
                raise Exception()
        except Exception:
            self.horas_semanais = 0

        for row in self.tree.get_children():
            self.tree.delete(row)

        # Busca disciplinas, pesos e questões
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, nome, peso, questoes FROM disciplina")
        dados = c.fetchall()
        conn.close()

        # Calcula importância (peso*questoes) e total
        importancias = []
        for disc in dados:
            peso = disc[2] or 1
            quest = disc[3] or 1
            importancia = peso * quest
            importancias.append(importancia)
        total_importancia = sum(importancias) if importancias else 1

        # Busca horas estudadas reais
        horas_estudadas = self.obter_horas_estudadas(dados)

        # Monta tabela
        odd = True
        for i, disc in enumerate(dados):
            nome = disc[1]
            peso = disc[2] or 1
            questoes = disc[3] or 1
            importancia = peso * questoes
            perc = importancia / total_importancia * 100 if total_importancia else 0
            horas_sugeridas = round((importancia / total_importancia) * self.horas_semanais, 2) if self.horas_semanais else 0
            horas_real = horas_estudadas.get(disc[0], 0)
            progresso = min(horas_real / horas_sugeridas * 100, 100) if horas_sugeridas else 0

            # Barra de progresso textual
            barra = "█" * int(progresso // 10) + "-" * (10 - int(progresso // 10))
            progresso_str = f"[{barra}] {progresso:.0f}%"

            tag = "odd" if odd else "even"
            # Ordem: (Disciplina, Progresso, Peso, Questões, % Prova, Horas Sugeridas, Horas Estudadas)
            self.tree.insert(
                '', 'end',
                values=(nome, progresso_str, peso, questoes, f"{perc:.1f}%", f"{horas_sugeridas:.2f}", f"{horas_real:.2f}"),
                tags=(tag,)
            )
            odd = not odd

    def refresh(self):
        self.refresh_disciplinas()
        self.refresh_planejamento()