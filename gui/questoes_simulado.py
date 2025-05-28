import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import get_conn

def percent_to_hex_color(percent):
    """
    Retorna cor em hexadecimal em gradiente do vermelho (0%) ao verde (100%).
    """
    percent = max(0, min(100, percent))
    # Interpolar de vermelho (#d12d21) para amarelo (#e8e822) até 50%, depois para verde (#22a852)
    if percent < 50:
        r1, g1, b1 = 209, 45, 33
        r2, g2, b2 = 232, 232, 34
        p = percent / 50.0
    else:
        r1, g1, b1 = 232, 232, 34
        r2, g2, b2 = 34, 168, 82
        p = (percent - 50) / 50.0
    r = int(r1 + (r2 - r1) * p)
    g = int(g1 + (g2 - g1) * p)
    b = int(b1 + (b2 - b1) * p)
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

class QuestoesSimuladoFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.registros = []
        self._style_cache = {}
        self.build()
        self.carregar_disciplinas()
        self.carregar_materias()
        self.limpar_campos()
        self.atualizar_tabela()

    def build(self):
        self.configure(bg="#f7fafd")
        tk.Label(self, text="Registro de Questões e Simulados", font=("Arial", 17, "bold"),
                 bg="#f7fafd", fg="#154b7c", anchor="center").pack(fill="x", padx=20, pady=(14, 2))

        # Frame superior - formulário de registro
        frame_form = tk.LabelFrame(self, text="Novo Registro", bg="#f7fafd", font=("Arial", 11, "bold"))
        frame_form.pack(fill="x", padx=20, pady=(8, 6))

        # Data
        tk.Label(frame_form, text="Data:", bg="#f7fafd", font=("Arial", 11)).grid(row=0, column=0, sticky="e", padx=(2,4), pady=4)
        self.entry_data = ttk.Entry(frame_form, width=12)
        self.entry_data.grid(row=0, column=1, sticky="w", padx=(0,8), pady=4)
        self.entry_data.insert(0, datetime.now().strftime("%d/%m/%Y"))

        # Tipo (questões/simulado)
        tk.Label(frame_form, text="Tipo:", bg="#f7fafd", font=("Arial", 11)).grid(row=0, column=2, sticky="e", padx=(2,4), pady=4)
        self.combo_tipo = ttk.Combobox(frame_form, width=14, state="readonly", values=["Questões", "Simulado"])
        self.combo_tipo.grid(row=0, column=3, sticky="w", padx=(0,8), pady=4)
        self.combo_tipo.current(0)

        # Disciplina
        tk.Label(frame_form, text="Disciplina:", bg="#f7fafd", font=("Arial", 11)).grid(row=0, column=4, sticky="e", padx=(2,4), pady=4)
        self.combo_disciplina = ttk.Combobox(frame_form, width=18, state="readonly")
        self.combo_disciplina.grid(row=0, column=5, sticky="w", padx=(0,8), pady=4)
        self.combo_disciplina.bind("<<ComboboxSelected>>", self.atualizar_combo_materia)

        # Matéria
        tk.Label(frame_form, text="Matéria:", bg="#f7fafd", font=("Arial", 11)).grid(row=1, column=0, sticky="e", padx=(2,4), pady=4)
        self.combo_materia = ttk.Combobox(frame_form, width=22, state="readonly")
        self.combo_materia.grid(row=1, column=1, sticky="w", padx=(0,8), pady=4)

        # Total de questões
        tk.Label(frame_form, text="Total de Questões:", bg="#f7fafd", font=("Arial", 11)).grid(row=1, column=2, sticky="e", padx=(2,4), pady=4)
        self.entry_total = ttk.Entry(frame_form, width=8)
        self.entry_total.grid(row=1, column=3, sticky="w", padx=(0,8), pady=4)

        # Acertos
        tk.Label(frame_form, text="Acertos:", bg="#f7fafd", font=("Arial", 11)).grid(row=1, column=4, sticky="e", padx=(2,4), pady=4)
        self.entry_acertos = ttk.Entry(frame_form, width=8)
        self.entry_acertos.grid(row=1, column=5, sticky="w", padx=(0,8), pady=4)

        # Observação
        tk.Label(frame_form, text="Observação:", bg="#f7fafd", font=("Arial", 11)).grid(row=2, column=0, sticky="e", padx=(2,4), pady=4)
        self.entry_obs = ttk.Entry(frame_form, width=46)
        self.entry_obs.grid(row=2, column=1, columnspan=5, sticky="w", padx=(0,8), pady=4)

        # Botão adicionar
        self.btn_adicionar = tk.Button(frame_form, text="Adicionar Registro", command=self.adicionar_registro,
                                   font=("Arial", 10, "bold"), bg="#a3d5ff", fg="#174a6a", bd=0, width=18)
        self.btn_adicionar.grid(row=3, column=0, columnspan=5, pady=(8, 4), padx=(0,8))

        # Botões de ação (editar/excluir/filtros futuros)
        self.btn_excluir = tk.Button(frame_form, text="Excluir Selecionado", command=self.excluir_registro,
                                     font=("Arial", 10, "bold"), bg="#ffaaaa", fg="#a10000", bd=0, width=18)
        self.btn_excluir.grid(row=3, column=1, columnspan=7, pady=(8, 4))

        for col in range(6):
            frame_form.grid_columnconfigure(col, weight=1)

        # Histórico de registros (tabela)
        frame_table = tk.Frame(self, bg="#f7fafd")
        frame_table.pack(fill="both", expand=True, padx=22, pady=(6, 12))

        columns = ("Data", "Tipo", "Disciplina", "Matéria", "Total", "Acertos", "Aproveitamento", "Observação")
        self.tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=12)
        style = ttk.Style()
        style.configure("Treeview", background="#fff", foreground="#1c3144", fieldbackground="#f5fafd", font=("Arial", 11), rowheight=28)
        style.configure("Treeview.Heading", background="#eaf4fb", foreground="#174a6a", font=("Arial", 11, "bold"))
        self.tree.tag_configure("odd", background="#f5fafd")
        self.tree.tag_configure("even", background="#eaf4fb")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", minwidth=70, width=120)
        self.tree.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Resumo
        frame_resumo = tk.Frame(self, bg="#f7fafd")
        frame_resumo.pack(fill="x", padx=20, pady=(0, 4))
        self.lbl_quest_total = tk.Label(frame_resumo, text="Total resolvidas: 0", font=("Arial", 12, "bold"), bg="#f7fafd", fg="#174a6a")
        self.lbl_quest_total.grid(row=0, column=0, padx=(0,18), sticky="w")
        self.lbl_quest_erradas = tk.Label(frame_resumo, text="Total erradas: 0", font=("Arial", 12, "bold"), bg="#f7fafd", fg="#a10000")
        self.lbl_quest_erradas.grid(row=0, column=1, padx=(0,18), sticky="w")
        self.lbl_quest_pct = tk.Label(frame_resumo, text="Aproveitamento geral: -", font=("Arial", 12, "bold"), bg="#f7fafd", fg="#22a852")
        self.lbl_quest_pct.grid(row=0, column=2, padx=(0,18), sticky="w")

    def carregar_disciplinas(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, nome FROM disciplina ORDER BY nome")
        self.disciplinas = c.fetchall()
        conn.close()
        # Salva os ids e nomes separadamente
        self._disciplinas_ids = [id for id, nome in self.disciplinas]
        nomes = [nome for id, nome in self.disciplinas]
        self.combo_disciplina['values'] = nomes
        self.combo_disciplina.set("")

        idx = self.combo_disciplina.current()
        if idx >= 0:
            disciplina_id = self._disciplinas_ids[idx]
        else:
            disciplina_id = None

    def carregar_materias(self, disciplina_id=None):
        conn = get_conn()
        c = conn.cursor()
        if disciplina_id:
            c.execute("SELECT id, nome FROM materia WHERE disciplina_id=? ORDER BY nome", (disciplina_id,))
        else:
            c.execute("SELECT id, nome FROM materia ORDER BY nome")
        self.materias = c.fetchall()
        conn.close()
        self._materias_ids = [id for id, nome in self.materias]
        nomes = [nome for id, nome in self.materias]
        self.combo_materia['values'] = nomes
        self.combo_materia.set("")

        idx = self.combo_materia.current()
        if idx >= 0:
            materia_id = self._materias_ids[idx]
        else:
            materia_id = None

    def atualizar_combo_materia(self, event=None):
        idx = self.combo_disciplina.current()
        if idx >= 0:
            disciplina_id = self._disciplinas_ids[idx]
            self.carregar_materias(disciplina_id)
        else:
            self.carregar_materias(None)

    def limpar_campos(self):
        self.entry_data.delete(0, tk.END)
        self.entry_data.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.combo_tipo.current(0)
        self.combo_disciplina.set("")
        self.combo_materia.set("")
        self.entry_total.delete(0, tk.END)
        self.entry_acertos.delete(0, tk.END)
        self.entry_obs.delete(0, tk.END)

    def adicionar_registro(self):
        data = self.entry_data.get().strip()
        tipo = self.combo_tipo.get().strip()
        total = self.entry_total.get().strip()
        acertos = self.entry_acertos.get().strip()
        obs = self.entry_obs.get().strip()

        if not (data and tipo and total):
            messagebox.showwarning("Questões/Simulado", "Preencha pelo menos Data, Tipo e Total de Questões.")
            return
        try:
            total_int = int(total)
            acertos_int = int(acertos) if acertos else None
            if total_int <= 0 or (acertos and acertos_int < 0):
                raise Exception()
        except Exception:
            messagebox.showwarning("Questões/Simulado", "Total de questões e acertos devem ser números positivos.")
            return

        # Novo: obtendo índices selecionados
        idx_disc = self.combo_disciplina.current()
        if idx_disc >= 0:
            disciplina_id = self._disciplinas_ids[idx_disc]
        else:
            disciplina_id = None

        idx_mat = self.combo_materia.current()
        if idx_mat >= 0:
            materia_id = self._materias_ids[idx_mat]
        else:
            materia_id = None

        # Conversão de data para formato ISO
        try:
            data_sql = datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")
        except Exception:
            data_sql = data

        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            INSERT INTO questoes_simulado
            (data, tipo, disciplina_id, materia_id, total_questoes, acertos, descricao, observacao)
            VALUES (?, ?, ?, ?, ?, ?, '', ?)
        """, (data_sql, tipo, disciplina_id, materia_id, total_int, acertos_int, obs))
        conn.commit()
        conn.close()
        self.limpar_campos()
        self.atualizar_tabela()

    def atualizar_tabela(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Pega registros do banco
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT q.data, q.tipo,
                   d.nome as disciplina, m.nome as materia,
                   q.total_questoes, q.acertos, q.observacao
            FROM questoes_simulado q
            LEFT JOIN disciplina d ON q.disciplina_id = d.id
            LEFT JOIN materia m ON q.materia_id = m.id
            ORDER BY q.data DESC, q.id DESC
        """)
        registros = c.fetchall()

        # Cálculo para o resumo
        total_questoes = 0
        total_acertos = 0
        total_erradas = 0

        for idx, reg in enumerate(registros):
            # Converte data para dd/mm/yyyy para exibição
            data_str = reg[0]
            try:
                data_str = datetime.strptime(data_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                pass

            total = reg[4] if reg[4] is not None else 0
            acertos = reg[5] if reg[5] is not None else ""
            # Calcula o aproveitamento (%)
            if reg[5] is not None and total:
                pct = (reg[5] / total) * 100
                pct_str = f"{pct:.0f}%"
                total_questoes += total
                total_acertos += reg[5]
                total_erradas += (total - reg[5])
            else:
                pct = None
                pct_str = "-"

            # Gradiente de cor: define uma tag única por valor de pct
            if pct is not None:
                hex_color = percent_to_hex_color(pct)
                tag = f"aprov_{int(pct)}"
                if tag not in self._style_cache:
                    self.tree.tag_configure(tag, foreground=hex_color)
                    self._style_cache[tag] = hex_color
            else:
                tag = "even" if idx%2 else "odd"

            self.tree.insert(
                '', 'end',
                values=(data_str, reg[1], reg[2] or "", reg[3] or "", total, acertos, pct_str, reg[6] or ""),
                tags=(tag,)
            )
        # Atualiza o resumo superior
        self.lbl_quest_total.config(text=f"Total resolvidas: {total_questoes}")
        self.lbl_quest_erradas.config(text=f"Total erradas: {total_erradas}")
        if total_questoes > 0:
            pct_geral = (total_acertos / total_questoes) * 100
            pct_str = f"{pct_geral:.1f}%"
            hex_color = percent_to_hex_color(pct_geral)
            self.lbl_quest_pct.config(text=f"Aproveitamento geral: {pct_str}", fg=hex_color)
        else:
            self.lbl_quest_pct.config(text="Aproveitamento geral: -", fg="#174a6a")
        conn.close()

    def excluir_registro(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Excluir", "Selecione um registro para excluir.")
            return
        idx = self.tree.index(sel[0])
        # Para garantir o ID correto, busque os IDs dos registros na ordem de exibição:
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id FROM questoes_simulado
            ORDER BY data DESC, id DESC
        """)
        ids = [row[0] for row in c.fetchall()]
        conn.close()
        if idx >= len(ids):
            messagebox.showerror("Erro", "Registro não encontrado.")
            return
        reg_id = ids[idx]
        confirm = messagebox.askyesno("Excluir", f"Excluir o registro selecionado?")
        if confirm:
            conn = get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM questoes_simulado WHERE id=?", (reg_id,))
            conn.commit()
            conn.close()
            self.atualizar_tabela()
    def refresh(self):
        self.carregar_disciplinas()
        self.carregar_materias()