import tkinter as tk
from tkinter import ttk, messagebox
from database import get_conn
from datetime import date, timedelta

class RevisaoFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#f5f6fa")
        self.disciplinas = self.get_disciplinas()
        self.status_op = ["Todas", "Pendente", "Realizada", "Atrasada"]
        self.periodos = ["Todas", "Hoje", "Próx. 7 dias", "Mês atual"]
        self.build()
    
    def build(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="#f8f9fa", foreground="#1e1e1e", fieldbackground="#f8f9fa", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background="#e2e6ea")
        style.map("Treeview", background=[("selected", "#d1e7dd")])
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), foreground="#fff", background="#007bff")
        style.map("Accent.TButton", background=[("active", "#0056b3")])

        # Filtros modernos
        filtro_frame = tk.Frame(self, bg="#f5f6fa")
        filtro_frame.pack(fill="x", padx=18, pady=(16, 4))

        tk.Label(filtro_frame, text="Disciplina:", font=("Segoe UI", 10), bg="#f5f6fa").pack(side="left")
        self.combo_disc = ttk.Combobox(filtro_frame, state="readonly", width=18, values=["Todas"] + self.disciplinas)
        self.combo_disc.current(0)
        self.combo_disc.pack(side="left", padx=(3, 10))
        self.combo_disc.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        tk.Label(filtro_frame, text="Status:", font=("Segoe UI", 10), bg="#f5f6fa").pack(side="left")
        self.combo_status = ttk.Combobox(filtro_frame, state="readonly", width=12, values=self.status_op)
        self.combo_status.current(0)
        self.combo_status.pack(side="left", padx=(3, 10))
        self.combo_status.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        tk.Label(filtro_frame, text="Período:", font=("Segoe UI", 10), bg="#f5f6fa").pack(side="left")
        self.combo_periodo = ttk.Combobox(filtro_frame, state="readonly", width=14, values=self.periodos)
        self.combo_periodo.current(0)
        self.combo_periodo.pack(side="left", padx=(3, 10))
        self.combo_periodo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # Botões de ação
        ttk.Button(filtro_frame, text="Atualizar", command=self.refresh, style="Accent.TButton").pack(side="right", padx=(0, 6))       
        #actions = tk.Frame(self, bg="#f5f6fa")
        #actions.pack(fill="x", padx=18, pady=(0, 2))
        self.btn_realizar = ttk.Button(filtro_frame, text="Marcar como Realizada", command=self.toggle_realizada, style="Accent.TButton")
        self.btn_realizar.pack(side="right", padx=(0, 8))

        # Avisos do dia
        self.aviso_label = tk.Label(self, text="", font=("Segoe UI", 10, "bold"), fg="#e67e22", bg="#f5f6fa")
        self.aviso_label.pack(fill="x", padx=18, pady=(2, 6))

        # Treeview para listagem
        columns = ("mat", "data", "realizada", "tipo")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse", height=12)
        self.tree.heading("mat", text="Matéria")
        self.tree.heading("data", text="Data Revisão")
        self.tree.heading("realizada", text="Realizada")
        self.tree.heading("tipo", text="Tipo")
        self.tree.column("mat", width=200, anchor="center")
        self.tree.column("data", width=100, anchor="center")
        self.tree.column("realizada", width=90, anchor="center")
        self.tree.column("tipo", width=90, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=18, pady=6)

        # Scrollbar vertical moderna
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        vsb.place(in_=self.tree, relx=1.0, rely=0, relheight=1.0, bordermode="outside")
        self.tree.configure(yscrollcommand=vsb.set)

        # Tags para revisões
        self.tree.tag_configure('atrasada', foreground='#d90429', font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure('hoje', background='#ffe066')
        self.tree.tag_configure('realizada', foreground='#218838')
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.refresh()

    def get_disciplinas(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT d.nome FROM disciplina d
            JOIN materia m ON d.id = m.disciplina_id
            JOIN revisao r ON m.id = r.materia_id
            ORDER BY d.nome ASC
        """)
        res = [row[0] for row in c.fetchall()]
        conn.close()
        return res

    def get_filtros(self):
        disc = self.combo_disc.get()
        status = self.combo_status.get()
        periodo = self.combo_periodo.get()
        return disc, status, periodo

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        disc, status, periodo = self.get_filtros()
        conn = get_conn()
        c = conn.cursor()
        query = """
            SELECT revisao.id, materia.nome, revisao.data_revisao, revisao.realizada, disciplina.nome, revisao.tipo
            FROM revisao
            JOIN materia ON materia.id = revisao.materia_id
            JOIN disciplina ON materia.disciplina_id = disciplina.id
        """
        filtros = []
        params = []
        if disc and disc != "Todas":
            filtros.append("disciplina.nome = ?")
            params.append(disc)
        if status == "Pendente":
            filtros.append("revisao.realizada=0 AND revisao.data_revisao >= ?")
            params.append(date.today().isoformat())
        elif status == "Realizada":
            filtros.append("revisao.realizada=1")
        elif status == "Atrasada":
            filtros.append("revisao.realizada=0 AND revisao.data_revisao < ?")
            params.append(date.today().isoformat())

        if periodo == "Hoje":
            filtros.append("revisao.data_revisao = ?")
            params.append(date.today().isoformat())
        elif periodo == "Próx. 7 dias":
            filtros.append("revisao.data_revisao BETWEEN ? AND ?")
            params.append(date.today().isoformat())
            params.append((date.today() + timedelta(days=7)).isoformat())
        elif periodo == "Mês atual":
            hoje = date.today()
            inicio = hoje.replace(day=1)
            if hoje.month == 12:
                fim = hoje.replace(year=hoje.year+1, month=1, day=1) - timedelta(days=1)
            else:
                fim = hoje.replace(month=hoje.month+1, day=1) - timedelta(days=1)
            filtros.append("revisao.data_revisao BETWEEN ? AND ?")
            params.append(inicio.isoformat())
            params.append(fim.isoformat())

        if filtros:
            query += " WHERE " + " AND ".join(filtros)
        # Ordena pendentes primeiro (realizada=0), depois por data_revisao desc (mais próximas primeiro)
        query += " ORDER BY revisao.realizada ASC, revisao.data_revisao ASC "

        c.execute(query, params)
        hoje = date.today().isoformat()
        revisoes_hoje = 0
        for id_rev, nome, data_revisao, realizada, disciplina_nome, tipo in c.fetchall():
            atrasada = (not realizada) and (data_revisao < hoje)
            hoje_tag = data_revisao == hoje and not realizada
            realizada_tag = bool(realizada)
            values = (nome, self.formatar_data(data_revisao), "Sim" if realizada else "Não", tipo if tipo else "")
            tags = ()
            if atrasada:
                tags = ('atrasada',)
            elif hoje_tag:
                tags = ('hoje',)
                revisoes_hoje += 1
            elif realizada_tag:
                tags = ('realizada',)
            self.tree.insert("", "end", iid=id_rev, values=values, tags=tags)
        conn.close()

        # Avisos do dia
        if revisoes_hoje > 0:
            self.aviso_label.config(text=f"🔔 Você tem {revisoes_hoje} revisão(ões) para hoje!", fg="#e67e22")
        else:
            self.aviso_label.config(text="")

        # Atualiza o estado do botão ao recarregar
        self.update_realizar_button()

    def formatar_data(self, data_iso):
        try:
            ano, mes, dia = data_iso.split("-")
            return f"{dia}/{mes}/{ano}"
        except Exception:
            return data_iso

    def on_tree_select(self, event=None):
        self.update_realizar_button()

    def update_realizar_button(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            realizada = item['values'][2] == "Sim"
            if realizada:
                self.btn_realizar.config(text="Marcar como Não Realizada")
            else:
                self.btn_realizar.config(text="Marcar como Realizada")
        else:
            self.btn_realizar.config(text="Marcar como Realizada")

    def toggle_realizada(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma revisão para marcar.")
            return
        revisao_id = selected[0]
        item = self.tree.item(selected[0])
        realizada = item['values'][2] == "Sim"
        novo_status = 0 if realizada else 1
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE revisao SET realizada=? WHERE id=?", (novo_status, revisao_id))
        conn.commit()
        conn.close()
        self.refresh()
        if novo_status:
            messagebox.showinfo("Sucesso", "Revisão marcada como realizada.")
        else:
            messagebox.showinfo("Sucesso", "Revisão marcada como NÃO realizada.")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Revisão")
    root.geometry("780x520")
    frame = RevisaoFrame(root)
    frame.pack(fill="both", expand=True)
    root.mainloop()