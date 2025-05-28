import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, datetime, timedelta
from database import get_conn, listar_bancos, set_active_db, criar_novo_banco, get_active_db, DB_FOLDER
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import os

class Dashboard(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        # Scrollable setup
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Para responder ao mousewheel
        self.scrollable_frame.bind_all("<MouseWheel>", self._on_mousewheel)

        # Props dashboard
        self.disciplinas = []
        self.selected_disciplina_id = None
        self.concurso_nome = ""
        self.data_prova = None
        self.grafico_canvas = None
        self.grafico_canvas2 = None

        # Widgets dentro do scrollable_frame
        self.create_widgets()
        self.create_gerenciar_bancos_section()
        self.load_concurso_info()
        self.load_disciplinas()
        self.refresh()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_widgets(self):
        tk.Label(self.scrollable_frame, text="Dashboard de Estudos", font=("Arial", 18, "bold"),
                 fg="#154b7c", anchor="center").pack(fill="x", padx=20, pady=(16, 4))

        frame_concurso = tk.Frame(self.scrollable_frame, pady=6)
        frame_concurso.pack(fill="x", padx=14)
        self.label_concurso = tk.Label(frame_concurso, text="", font=("Arial", 12, "bold"), fg="#236f3a")
        self.label_concurso.pack(side="left", anchor="w", padx=(0, 12))
        self.label_data_prova = tk.Label(frame_concurso, text="", font=("Arial", 12), fg="#8a5803")
        self.label_data_prova.pack(side="left", padx=(0, 12))
        self.label_dias_restantes = tk.Label(frame_concurso, text="", font=("Arial", 12, "bold"), fg="#b13a1a")
        self.label_dias_restantes.pack(side="left", padx=(0, 12))
        btn_config = ttk.Button(frame_concurso, text="Configurar Concurso", command=self.abrir_config_concurso)
        btn_config.pack(side="right", padx=(0, 6))

        frame_filtro = tk.Frame(self.scrollable_frame)
        frame_filtro.pack(pady=(4, 12))
        tk.Label(frame_filtro, text="Filtrar por disciplina: ", font=("Arial", 11)).pack(side="left", padx=(0, 5))
        self.combo_disciplinas = ttk.Combobox(frame_filtro, state="readonly", width=24)
        self.combo_disciplinas.pack(side="left")
        self.combo_disciplinas.bind("<<ComboboxSelected>>", self.on_disciplina_change)

        painel = tk.Frame(self.scrollable_frame)
        painel.pack(padx=14, pady=(0, 8), fill="x")

        frame_progresso = tk.LabelFrame(painel, text="Progresso Geral", padx=12, pady=10)
        frame_progresso.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.progress_var = tk.DoubleVar(value=0)
        self.barra_progresso = ttk.Progressbar(frame_progresso, variable=self.progress_var, maximum=100, length=200)
        self.barra_progresso.pack(fill="x", padx=5, pady=4)
        self.label_progresso = tk.Label(frame_progresso, text="0.0% concluído", font=("Arial", 11))
        self.label_progresso.pack()

        frame_metas = tk.LabelFrame(painel, text="Metas de Estudo", padx=12, pady=10)
        frame_metas.pack(side="left", fill="both", expand=True)
        self.label_meta_questoes = tk.Label(frame_metas, text="Meta de questões: -", font=("Arial", 11))
        self.label_meta_questoes.pack(anchor="w")
        self.label_meta_tempo = tk.Label(frame_metas, text="Meta de horas: -", font=("Arial", 11))
        self.label_meta_tempo.pack(anchor="w")
        self.label_meta_progresso = tk.Label(frame_metas, text="Progresso das metas: -", font=("Arial", 11, "italic"))
        self.label_meta_progresso.pack(anchor="w", pady=(7,0))
        btn_config_meta = ttk.Button(frame_metas, text="Definir Metas", command=self.abrir_config_metas)
        btn_config_meta.pack(anchor="e", pady=(4,0))

        painel2 = tk.Frame(self.scrollable_frame)
        painel2.pack(padx=14, pady=(0, 8), fill="x")
        frame_revisoes = tk.LabelFrame(painel2, text="Revisões Pendentes", padx=12, pady=10)
        frame_revisoes.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.revisoes_label = tk.Label(frame_revisoes, text="0 revisão(ões) pendente(s)", font=("Arial", 11))
        self.revisoes_label.pack()
        self.alerta_revisao = tk.Label(frame_revisoes, text="", font=("Arial", 10, "italic"), fg="#b13a1a")
        self.alerta_revisao.pack()

        frame_tempo = tk.LabelFrame(painel2, text="Tempo Total Estudado", padx=12, pady=10)
        frame_tempo.pack(side="left", fill="both", expand=True)
        self.tempo_label = tk.Label(frame_tempo, text="0h 0min", font=("Arial", 11))
        self.tempo_label.pack(anchor="w")

        self.frame_graficos = tk.LabelFrame(self.scrollable_frame, text="Evolução Semanal", padx=12, pady=10)
        self.frame_graficos.pack(fill="both", expand=True, padx=14, pady=(0, 4))
        self.frame_graficos2 = tk.LabelFrame(self.scrollable_frame, text="Distribuição por Disciplina", padx=12, pady=10)
        self.frame_graficos2.pack(fill="both", expand=True, padx=14, pady=(0, 12))

    def create_gerenciar_bancos_section(self):
        # Seção separada para gerenciamento de bancos de dados
        frame_gerenciar = tk.LabelFrame(self.scrollable_frame, text="Gerenciar Bancos de Dados", padx=12, pady=10)
        frame_gerenciar.pack(fill="x", padx=16, pady=(14, 12))

        # Nome do banco ativo
        db_path = get_active_db()
        banco_ativo = os.path.basename(db_path)
        self.label_banco_ativo = tk.Label(frame_gerenciar, text=f"Banco ativo: {banco_ativo}", font=("Arial", 11, "bold"), fg="#154b7c")
        self.label_banco_ativo.pack(anchor="w", pady=(0, 4))
        
        # Listar bancos
        bancos = listar_bancos()
        self.lb_bancos = tk.Listbox(frame_gerenciar, font=("Arial", 10), height=min(6, len(bancos)), exportselection=False)
        for b in bancos:
            self.lb_bancos.insert(tk.END, b)
            if b == banco_ativo:
                self.lb_bancos.selection_set(tk.END)
        self.lb_bancos.pack(fill="x", padx=0, pady=4)

        # Botões
        btns_frame = tk.Frame(frame_gerenciar)
        btns_frame.pack(fill="x", pady=(6, 0))
        ttk.Button(btns_frame, text="Ativar Selecionado", command=self.ativar_banco).pack(side="left", padx=4)
        ttk.Button(btns_frame, text="Criar Novo Banco", command=self.criar_novo_banco_dialogo).pack(side="left", padx=4)
        ttk.Button(btns_frame, text="Excluir Selecionado", command=self.excluir_banco_dialogo).pack(side="left", padx=4)
        ttk.Button(btns_frame, text="Renomear Selecionado", command=self.renomear_banco_dialogo).pack(side="left", padx=4)

    def ativar_banco(self):
        idx = self.lb_bancos.curselection()
        if not idx:
            messagebox.showwarning("Atenção", "Selecione um banco para ativar.")
            return
        nome = self.lb_bancos.get(idx[0])
        caminho = os.path.join(DB_FOLDER, nome)
        set_active_db(caminho)
        messagebox.showinfo("Banco ativado", f"O banco '{nome}' está ativo.\n\nReinicie o programa para garantir que todas as telas usem o novo banco.")
        self.label_banco_ativo.config(text=f"Banco ativo: {nome}")

    def criar_novo_banco_dialogo(self):
        nome = simpledialog.askstring("Novo banco de dados", "Digite um nome para o novo banco de dados:")
        if not nome:
            return
        nome = ''.join(c for c in nome if c.isalnum() or c in ('_', '-')).strip()
        if not nome:
            messagebox.showerror("Nome inválido", "Digite um nome válido (sem espaços, apenas letras, números ou _ -)")
            return
        criar_novo_banco(nome)
        messagebox.showinfo("Novo banco criado", f"O banco '{nome}' foi criado e está em uso.")
        self._refresh_bancos_section()

    def excluir_banco_dialogo(self):
        idx = self.lb_bancos.curselection()
        if not idx:
            messagebox.showwarning("Atenção", "Selecione um banco para excluir.")
            return
        nome = self.lb_bancos.get(idx[0])
        db_path = os.path.join(DB_FOLDER, nome)
        banco_ativo = os.path.basename(get_active_db())
        if nome == banco_ativo:
            messagebox.showerror("Erro", "Não é possível excluir o banco de dados que está ativo.")
            return
        if messagebox.askyesno("Excluir banco", f"Tem certeza que deseja excluir o banco '{nome}'?\nEssa ação não poderá ser desfeita."):
            try:
                os.remove(db_path)
                messagebox.showinfo("Banco excluído", f"O banco '{nome}' foi excluído.")
                self._refresh_bancos_section()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir banco: {str(e)}")

    def renomear_banco_dialogo(self):
        idx = self.lb_bancos.curselection()
        if not idx:
            messagebox.showwarning("Atenção", "Selecione um banco para renomear.")
            return
        nome_antigo = self.lb_bancos.get(idx[0])
        banco_ativo = os.path.basename(get_active_db())
        new_nome = simpledialog.askstring("Renomear banco de dados", f"Digite o novo nome para o banco '{nome_antigo}':")
        if not new_nome:
            return
        new_nome = ''.join(c for c in new_nome if c.isalnum() or c in ('_', '-')).strip()
        if not new_nome:
            messagebox.showerror("Nome inválido", "Digite um nome válido (sem espaços, apenas letras, números ou _ -)")
            return
        old_path = os.path.join(DB_FOLDER, nome_antigo)
        new_path = os.path.join(DB_FOLDER, f"{new_nome}.db" if not new_nome.endswith(".db") else new_nome)
        if os.path.exists(new_path):
            messagebox.showerror("Erro", f"Já existe um banco chamado '{new_nome}'.")
            return
        try:
            os.rename(old_path, new_path)
            # Se for o banco ativo, atualiza o config
            if nome_antigo == banco_ativo:
                set_active_db(new_path)
                messagebox.showinfo("Banco renomeado", f"O banco ativo foi renomeado para '{os.path.basename(new_path)}'.\nReinicie o programa para garantir que todas as telas usem o novo banco.")
            else:
                messagebox.showinfo("Banco renomeado", f"O banco '{nome_antigo}' foi renomeado para '{os.path.basename(new_path)}'.")
            self._refresh_bancos_section()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao renomear banco: {str(e)}")

    def _refresh_bancos_section(self):
        # Remove e recria a seção de bancos
        self.label_banco_ativo.master.destroy()
        self.create_gerenciar_bancos_section()

    # --- Abaixo todas as funcionalidades originais do Dashboard ---

    def load_concurso_info(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS concurso_info (id INTEGER PRIMARY KEY, nome TEXT, data_prova TEXT)")
        c.execute("SELECT nome, data_prova FROM concurso_info WHERE id=1")
        row = c.fetchone()
        conn.close()
        if row:
            self.concurso_nome, self.data_prova = row
        else:
            self.concurso_nome = ""
            self.data_prova = None
        self.atualiza_info_concurso()

    def atualiza_info_concurso(self):
        txt = f"Concurso: {self.concurso_nome}" if self.concurso_nome else "Concurso: [não definido]"
        self.label_concurso.config(text=txt)
        if self.data_prova:
            try:
                data_pv = datetime.strptime(self.data_prova, "%Y-%m-%d").date()
                self.label_data_prova.config(text=f"Data da prova: {data_pv.strftime('%d/%m/%Y')}")
                dias = (data_pv - date.today()).days
                cor = "#236f3a" if dias > 30 else "#b13a1a"
                msg = f"Faltam {dias} dias!" if dias >= 0 else "Prova já realizada!"
                self.label_dias_restantes.config(text=msg, fg=cor)
            except Exception:
                self.label_data_prova.config(text="Data da prova: [inválida]")
                self.label_dias_restantes.config(text="")
        else:
            self.label_data_prova.config(text="Data da prova: [não definida]")
            self.label_dias_restantes.config(text="")

    def abrir_config_concurso(self):
        win = tk.Toplevel(self)
        win.title("Configurar Concurso")
        win.geometry("320x180")
        tk.Label(win, text="Nome do concurso:", font=("Arial", 11)).pack(pady=(16,3))
        entry_nome = tk.Entry(win, font=("Arial", 11))
        entry_nome.pack(fill="x", padx=20)
        entry_nome.insert(0, self.concurso_nome)
        tk.Label(win, text="Data da prova (DD/MM/AAAA):", font=("Arial", 11)).pack(pady=(10,3))
        entry_data = tk.Entry(win, font=("Arial", 11))
        entry_data.pack(fill="x", padx=20)
        if self.data_prova:
            try:
                data_fmt = datetime.strptime(self.data_prova, "%Y-%m-%d").strftime("%d/%m/%Y")
                entry_data.insert(0, data_fmt)
            except Exception:
                entry_data.insert(0, self.data_prova)
        def salvar():
            nome = entry_nome.get().strip()
            data = entry_data.get().strip()
            if nome and data:
                try:
                    data_sql = datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")
                except Exception:
                    messagebox.showerror("Erro", "Data inválida. Use o formato DD/MM/AAAA.")
                    return
            elif nome and not data:
                data_sql = None
            else:
                data_sql = None
            conn = get_conn()
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS concurso_info (id INTEGER PRIMARY KEY, nome TEXT, data_prova TEXT)")
            c.execute("INSERT OR REPLACE INTO concurso_info (id, nome, data_prova) VALUES (1, ?, ?)", (nome, data_sql))
            conn.commit()
            conn.close()
            self.concurso_nome = nome
            self.data_prova = data_sql
            self.atualiza_info_concurso()
            win.destroy()
        ttk.Button(win, text="Salvar", command=salvar).pack(pady=(20,0))
        win.transient(self)
        win.grab_set()
        win.wait_window()

    def abrir_config_metas(self):
        win = tk.Toplevel(self)
        win.title("Definir Metas de Estudo")
        win.geometry("320x170")
        tk.Label(win, text="Meta de questões (por semana):", font=("Arial", 11)).pack(pady=(14,3))
        entry_q = tk.Entry(win, font=("Arial", 11))
        entry_q.pack(fill="x", padx=20)
        meta_q_old = self.get_meta("questoes")
        if meta_q_old:
            entry_q.insert(0, str(meta_q_old))
        tk.Label(win, text="Meta de horas (por semana):", font=("Arial", 11)).pack(pady=(8,3))
        entry_h = tk.Entry(win, font=("Arial", 11))
        entry_h.pack(fill="x", padx=20)
        meta_h_old = self.get_meta("horas")
        if meta_h_old:
            entry_h.insert(0, str(meta_h_old))
        def salvar():
            q = entry_q.get().strip()
            h = entry_h.get().strip()
            conn = get_conn()
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY, questoes INTEGER, horas REAL)")
            c.execute("INSERT OR REPLACE INTO metas (id, questoes, horas) VALUES (1, ?, ?)",
                      (int(q) if q else None, float(h) if h else None))
            conn.commit()
            conn.close()
            self.refresh()
            win.destroy()
        ttk.Button(win, text="Salvar", command=salvar).pack(pady=(16,0))
        win.transient(self)
        win.grab_set()
        win.wait_window()

    def get_meta(self, tipo):
        conn = get_conn()
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS metas (id INTEGER PRIMARY KEY, questoes INTEGER, horas REAL)")
        c.execute("SELECT questoes, horas FROM metas WHERE id=1")
        row = c.fetchone()
        conn.close()
        if row:
            if tipo == "questoes":
                return row[0]
            elif tipo == "horas":
                return row[1]
        return None

    def load_disciplinas(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, nome FROM disciplina ORDER BY nome ASC")
        self.disciplinas = c.fetchall()
        conn.close()
        disciplinas_combo = ["Todas as disciplinas"] + [nome for _, nome in self.disciplinas]
        self.combo_disciplinas['values'] = disciplinas_combo
        self.combo_disciplinas.current(0)

    def on_disciplina_change(self, event=None):
        idx = self.combo_disciplinas.current()
        if idx == 0:
            self.selected_disciplina_id = None
        else:
            self.selected_disciplina_id = self.disciplinas[idx - 1][0]
        self.refresh()

    def refresh(self):
        progresso = self.get_progresso(self.selected_disciplina_id)
        self.progress_var.set(progresso)
        self.label_progresso.config(text=f"{progresso:.1f}% concluído")
        revisoes_pendentes = self.get_revisoes_pendentes(self.selected_disciplina_id)
        self.revisoes_label.config(text=f"{revisoes_pendentes} revisão(ões) pendente(s)")
        if revisoes_pendentes > 0:
            self.alerta_revisao.config(text="⚠️ Faça suas revisões pendentes!", fg="#b13a1a")
        else:
            self.alerta_revisao.config(text="Nenhuma revisão pendente! Parabéns!", fg="#236f3a")
        tempo_estudado = self.get_tempo_estudado(self.selected_disciplina_id)
        horas = tempo_estudado // 60
        minutos = tempo_estudado % 60
        self.tempo_label.config(text=f"{horas}h {minutos}min")
        meta_q = self.get_meta("questoes") or "-"
        meta_h = self.get_meta("horas") or "-"
        self.label_meta_questoes.config(text=f"Meta de questões: {meta_q}")
        self.label_meta_tempo.config(text=f"Meta de horas: {meta_h}")
        questoes_semana = self.get_questoes_semana(self.selected_disciplina_id)
        horas_semana = self.get_tempo_semana(self.selected_disciplina_id) / 60
        prog_q = f"{questoes_semana}" if isinstance(meta_q, int) and meta_q else "-"
        prog_h = f"{horas_semana:.1f}h" if isinstance(meta_h, (int, float)) and meta_h else "-"
        meta_prog = f"Questões semana: {prog_q}/{meta_q} | Horas semana: {prog_h}/{meta_h if meta_h!='-' else '-'}"
        self.label_meta_progresso.config(text=f"Progresso das metas: {meta_prog}")
        self.atualiza_info_concurso()
        self.refresh_graficos()
        self.refresh_graficos2()

    def get_questoes_semana(self, disciplina_id=None):
        hoje = date.today()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        conn = get_conn()
        c = conn.cursor()
        if disciplina_id:
            c.execute("""
                SELECT SUM(qs.total_questoes)
                FROM questoes_simulado qs
                JOIN disciplina d ON qs.disciplina_id = d.id
                WHERE qs.data >= ? AND d.id = ?
            """, (inicio_semana.isoformat(), disciplina_id))
        else:
            c.execute("""
                SELECT SUM(total_questoes)
                FROM questoes_simulado
                WHERE data >= ?
            """, (inicio_semana.isoformat(),))
        qtd = c.fetchone()[0]
        conn.close()
        return qtd if qtd else 0

    def get_tempo_semana(self, disciplina_id=None):
        hoje = date.today()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        conn = get_conn()
        c = conn.cursor()
        if disciplina_id:
            c.execute("""
                SELECT SUM(s.duracao)
                FROM sessao s
                JOIN materia m ON s.materia_id = m.id
                WHERE s.data >= ? AND m.disciplina_id = ?
            """, (inicio_semana.isoformat(), disciplina_id))
        else:
            c.execute("""
                SELECT SUM(duracao)
                FROM sessao
                WHERE data >= ?
            """, (inicio_semana.isoformat(),))
        tempo = c.fetchone()[0]
        conn.close()
        return tempo if tempo else 0

    def get_progresso(self, disciplina_id=None):
        conn = get_conn()
        c = conn.cursor()
        if disciplina_id:
            c.execute("SELECT COUNT(*) FROM materia WHERE disciplina_id=?", (disciplina_id,))
            total_materias = c.fetchone()[0]
            if total_materias == 0:
                conn.close()
                return 0.0
            c.execute("""
                SELECT COUNT(DISTINCT m.id)
                FROM materia m
                JOIN sessao s ON s.materia_id = m.id
                WHERE m.disciplina_id=? AND s.duracao > 0
            """, (disciplina_id,))
            materias_estudadas = c.fetchone()[0]
            conn.close()
            return (materias_estudadas / total_materias) * 100
        else:
            c.execute("SELECT COUNT(*) FROM materia")
            total_materias = c.fetchone()[0]
            if total_materias == 0:
                conn.close()
                return 0.0
            c.execute("SELECT COUNT(DISTINCT materia_id) FROM sessao WHERE duracao>0")
            materias_estudadas = c.fetchone()[0]
            conn.close()
            return (materias_estudadas / total_materias) * 100

    def get_revisoes_pendentes(self, disciplina_id=None):
        hoje = date.today().isoformat()
        conn = get_conn()
        c = conn.cursor()
        if disciplina_id:
            c.execute("""
                SELECT COUNT(*)
                FROM revisao r
                JOIN materia m ON r.materia_id = m.id
                WHERE r.realizada=0 AND r.data_revisao<=? AND m.disciplina_id=?
            """, (hoje, disciplina_id))
        else:
            c.execute("""
                SELECT COUNT(*) FROM revisao
                WHERE realizada=0 AND data_revisao<=?
            """, (hoje,))
        revisoes = c.fetchone()[0]
        conn.close()
        return revisoes

    def get_tempo_estudado(self, disciplina_id=None):
        conn = get_conn()
        c = conn.cursor()
        if disciplina_id:
            c.execute("""
                SELECT SUM(s.duracao)
                FROM sessao s
                JOIN materia m ON s.materia_id = m.id
                WHERE m.disciplina_id=?
            """, (disciplina_id,))
        else:
            c.execute("SELECT SUM(duracao) FROM sessao")
        tempo = c.fetchone()[0]
        conn.close()
        return tempo if tempo else 0

    def refresh_graficos(self):
        if self.grafico_canvas:
            self.grafico_canvas.get_tk_widget().destroy()
            self.grafico_canvas = None
        semanas, tempo_por_semana = self.get_tempo_por_semana(self.selected_disciplina_id, n_sem=6)
        _, questoes_por_semana = self.get_questoes_por_semana(self.selected_disciplina_id, n_sem=6)
        fig, axs = plt.subplots(1, 2, figsize=(8, 3))
        axs[0].bar(range(len(semanas)), tempo_por_semana, color="#4072b3")
        axs[0].set_title("Tempo de Estudo (min/sem)")
        axs[0].set_ylabel("Minutos")
        axs[0].set_xticks(range(len(semanas)))
        axs[0].set_xticklabels(semanas, rotation=35, ha='right', fontsize=8)
        axs[1].bar(range(len(semanas)), questoes_por_semana, color="#3fa554")
        axs[1].set_title("Questões Resolvidas (sem)")
        axs[1].set_ylabel("Questões")
        axs[1].set_xticks(range(len(semanas)))
        axs[1].set_xticklabels(semanas, rotation=35, ha='right', fontsize=8)
        fig.tight_layout()
        self.grafico_canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        self.grafico_canvas.draw()
        self.grafico_canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    def get_tempo_por_semana(self, disciplina_id=None, n_sem=6):
        conn = get_conn()
        c = conn.cursor()
        hoje = date.today()
        semanas = []
        tempos = []
        for i in reversed(range(n_sem)):
            ini = hoje - timedelta(days=hoje.weekday() + i*7)
            fim = ini + timedelta(days=6)
            ini_str = ini.isoformat()
            fim_str = fim.isoformat()
            # Formato DD/MM
            semanas.append(f"{ini.strftime('%d/%m')}-{fim.strftime('%d/%m')}")
            if disciplina_id:
                c.execute("""
                    SELECT SUM(s.duracao)
                    FROM sessao s
                    JOIN materia m ON s.materia_id = m.id
                    WHERE s.data BETWEEN ? AND ? AND m.disciplina_id = ?
                """, (ini_str, fim_str, disciplina_id))
            else:
                c.execute("""
                    SELECT SUM(duracao)
                    FROM sessao
                    WHERE data BETWEEN ? AND ?
                """, (ini_str, fim_str))
            tempo = c.fetchone()[0]
            tempos.append(tempo if tempo else 0)
        conn.close()
        return semanas, tempos

    def get_questoes_por_semana(self, disciplina_id=None, n_sem=6):
        conn = get_conn()
        c = conn.cursor()
        hoje = date.today()
        semanas = []
        questoes = []
        for i in reversed(range(n_sem)):
            ini = hoje - timedelta(days=hoje.weekday() + i*7)
            fim = ini + timedelta(days=6)
            ini_str = ini.isoformat()
            fim_str = fim.isoformat()
            semanas.append(f"{ini.strftime('%d/%m')}-{fim.strftime('%d/%m')}")
            if disciplina_id:
                c.execute("""
                    SELECT SUM(qs.total_questoes)
                    FROM questoes_simulado qs
                    JOIN disciplina d ON qs.disciplina_id = d.id
                    WHERE qs.data BETWEEN ? AND ? AND d.id = ?
                """, (ini_str, fim_str, disciplina_id))
            else:
                c.execute("""
                    SELECT SUM(total_questoes)
                    FROM questoes_simulado
                    WHERE data BETWEEN ? AND ?
                """, (ini_str, fim_str))
            qtd = c.fetchone()[0]
            questoes.append(qtd if qtd else 0)
        conn.close()
        return semanas, questoes

    def refresh_graficos2(self):
        if self.grafico_canvas2:
            self.grafico_canvas2.get_tk_widget().destroy()
            self.grafico_canvas2 = None

        # Tempo de estudo por disciplina (filtra só valores > 0)
        labels, valores = self.get_tempo_por_disciplina()
        labels_tempo = [l for l, v in zip(labels, valores) if v > 0]
        valores_tempo = [v for v in valores if v > 0]

        # Questões por disciplina (filtra só valores > 0)
        labels2, valores2 = self.get_questoes_por_disciplina()
        labels_quest = [l for l, v in zip(labels2, valores2) if v > 0]
        valores_quest = [v for v in valores2 if v > 0]

        fig, axs = plt.subplots(1, 2, figsize=(8, 3))
        # Tempo de estudo
        if valores_tempo:
            axs[0].pie(valores_tempo, labels=labels_tempo, autopct='%1.0f%%')
            axs[0].set_title("Tempo de Estudo por Disciplina")
        else:
            axs[0].text(0.5, 0.5, 'Sem dados', ha='center', va='center')
            axs[0].set_title("Tempo de Estudo por Disciplina")
        # Questões resolvidas
        if valores_quest:
            axs[1].pie(valores_quest, labels=labels_quest, autopct='%1.0f%%')
            axs[1].set_title("Questões por Disciplina")
        else:
            axs[1].text(0.5, 0.5, 'Sem dados', ha='center', va='center')
            axs[1].set_title("Questões por Disciplina")
        fig.tight_layout()
        self.grafico_canvas2 = FigureCanvasTkAgg(fig, master=self.frame_graficos2)
        self.grafico_canvas2.draw()
        self.grafico_canvas2.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    def get_tempo_por_disciplina(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, nome FROM disciplina ORDER BY nome")
        disciplinas = c.fetchall()
        labels = []
        valores = []
        for id_disc, nome in disciplinas:
            c.execute("""
                SELECT SUM(s.duracao)
                FROM sessao s
                JOIN materia m ON s.materia_id = m.id
                WHERE m.disciplina_id = ?
            """, (id_disc,))
            tempo = c.fetchone()[0]
            labels.append(nome)
            valores.append(tempo if tempo else 0)
        conn.close()
        return labels, valores

    def get_questoes_por_disciplina(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, nome FROM disciplina ORDER BY nome")
        disciplinas = c.fetchall()
        labels = []
        valores = []
        for id_disc, nome in disciplinas:
            c.execute("""
                SELECT SUM(total_questoes)
                FROM questoes_simulado
                WHERE disciplina_id = ?
            """, (id_disc,))
            qtd = c.fetchone()[0]
            labels.append(nome)
            valores.append(qtd if qtd else 0)
        conn.close()
        return labels, valores

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Dashboard de Estudos")
    dashboard = Dashboard(root)
    dashboard.pack(fill="both", expand=True)
    root.mainloop()