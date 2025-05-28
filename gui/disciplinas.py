import tkinter as tk
from tkinter import ttk, messagebox
from database import get_conn

class DisciplinasFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.frame_esquerda = None
        self.frame_direita = None
        self.tree = None
        self.tree_materias = None
        self.entry_disciplina = None
        self.entry_materia = None
        self.materias_scroll = None
        self.materias_scroll_horizontal = None
        self.build()
        self.refresh_disciplinas()

    def build(self):
        # Título principal
        tk.Label(self, text="Gerenciar Disciplinas", font=("Arial", 17, "bold"),
                 fg="#154b7c", anchor="center").pack(fill="x", padx=20, pady=(14, 2))

        # Frame principal agrupando esquerda (disciplinas) e direita (ações)
        frame_principal = tk.Frame(self, bg="#f6f6f6")
        frame_principal.pack(fill="both", padx=20, pady=10, expand=True)

        # Frame esquerda: Disciplinas
        self.frame_esquerda = tk.LabelFrame(
            frame_principal, text="Disciplinas cadastradas", padx=10, pady=10, font=("Arial", 11, "bold"))
        self.frame_esquerda.pack(side="left", fill="y", expand=False)

        # Treeview de Disciplinas
        self.tree = ttk.Treeview(self.frame_esquerda, columns=("Nome",), show="headings", height=10)
        self.tree.heading("Nome", text="Nome da Disciplina")
        self.tree.column("Nome", width=180)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_disciplina_select)

        # Estilo para Treeview de disciplinas
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Disciplinas.Treeview", font=("Arial", 10))
        style.configure("Disciplinas.Treeview.Heading", font=("Arial", 10, "bold"))
        self.tree.configure(style="Disciplinas.Treeview")
        self.tree.tag_configure('odd', background="#f5fafd")
        self.tree.tag_configure('even', background="#eaf4fb")

        # Frame direita: Ações e matérias
        self.frame_direita = tk.Frame(frame_principal, bg="#fafcff")
        self.frame_direita.pack(side="left", fill="both", expand=True, padx=(20, 0))

        # Bloco: Nova disciplina
        frame_nova_disciplina = tk.LabelFrame(self.frame_direita, text="Nova disciplina", padx=10, pady=10)
        frame_nova_disciplina.pack(fill="x", pady=(0, 10))
        self.entry_disciplina = tk.Entry(frame_nova_disciplina, font=("Arial", 11))
        self.entry_disciplina.pack(side="left", expand=True, fill="x", padx=(0, 10))
        tk.Button(frame_nova_disciplina, text="Inserir", width=10, command=self.inserir_disciplina, bg="#e1eafc").pack(side="left")
        tk.Button(frame_nova_disciplina, text="Remover selecionada", command=self.remover_disciplina, width=18, bg="#fce1e1").pack(side="left", padx=(10, 0))

        # Bloco: Nova matéria
        frame_nova_materia = tk.LabelFrame(self.frame_direita, text="Nova matéria", padx=10, pady=10)
        frame_nova_materia.pack(fill="x", pady=(0, 10))
        self.entry_materia = tk.Entry(frame_nova_materia, font=("Arial", 11))
        self.entry_materia.pack(side="left", expand=True, fill="x", padx=(0, 10))
        tk.Button(frame_nova_materia, text="Inserir Matéria", width=15, command=self.inserir_materia, bg="#e1fce6").pack(side="left")
        tk.Button(frame_nova_materia, text="Remover Matéria", command=self.remover_materia, width=16, bg="#fce1e1").pack(side="left", padx=(10, 0))

        # Bloco: Matérias da disciplina selecionada (Treeview)
        frame_materias = tk.LabelFrame(self.frame_direita, text="Matérias da disciplina selecionada:", padx=10, pady=10)
        frame_materias.pack(fill="both", expand=True)

        # Frame para Treeview e Scrollbars dentro do quadro de matérias
        frame_tv_scroll = tk.Frame(frame_materias)
        frame_tv_scroll.pack(fill="both", expand=True)

        # Treeview para matérias com zebra striping
        self.tree_materias = ttk.Treeview(frame_tv_scroll, columns=("NomeMateria",), show="headings", height=10)
        self.tree_materias.heading("NomeMateria", text="Nome da Matéria")
        self.tree_materias.column("NomeMateria", width=800)
        self.tree_materias.pack(side="left", fill="both", expand=True)

        # Scrollbar vertical DENTRO do quadro de matérias
        self.materias_scroll = ttk.Scrollbar(frame_tv_scroll, orient="vertical", command=self.tree_materias.yview)
        self.materias_scroll.pack(side="right", fill="y")
        self.tree_materias.configure(yscrollcommand=self.materias_scroll.set)

        # Scrollbar horizontal DENTRO do quadro de matérias
        self.materias_scroll_horizontal = ttk.Scrollbar(frame_materias, orient="horizontal", command=self.tree_materias.xview)
        self.materias_scroll_horizontal.pack(side="bottom", fill="x")
        self.tree_materias.configure(xscrollcommand=self.materias_scroll_horizontal.set)

        # Zebra striping para matérias
        self.tree_materias.tag_configure('odd', background="#f5fafd")
        self.tree_materias.tag_configure('even', background="#eaf4fb")

    def refresh_disciplinas(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, nome FROM disciplina ORDER BY id ASC")
        odd = True
        for id_, nome in c.fetchall():
            zebra_tag = "odd" if odd else "even"
            self.tree.insert("", "end", iid=id_, values=(nome,), tags=(zebra_tag,))
            odd = not odd
        conn.close()
        self.refresh_materias(None)

    def on_disciplina_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.refresh_materias(selected[0])
        else:
            self.refresh_materias(None)

    def refresh_materias(self, disciplina_id):
        for item in self.tree_materias.get_children():
            self.tree_materias.delete(item)
        if not disciplina_id:
            return
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, nome FROM materia WHERE disciplina_id=? ORDER BY id ASC", (disciplina_id,))
        odd = True
        max_text_len = 0
        materia_ids_nomes = []
        for id_, nome in c.fetchall():
            zebra_tag = "odd" if odd else "even"
            self.tree_materias.insert("", "end", iid=id_, values=(nome,), tags=(zebra_tag,))
            odd = not odd
            materia_ids_nomes.append((id_, nome))
            if len(nome) > max_text_len:
                max_text_len = len(nome)
        conn.close()

        # Ajuste da largura da coluna baseado no maior texto (em pixels)
        font = ("Arial", 11)
        # Cria um widget "invisível" só para medir o texto
        import tkinter.font
        f = tkinter.font.Font(family=font[0], size=font[1])
        max_text_pixel = 0
        for _, nome in materia_ids_nomes:
            largura = f.measure(nome)
            if largura > max_text_pixel:
                max_text_pixel = largura
        # Limite mínimo e máximo para não "quebrar" layout
        min_width = 800
        max_width = 2000
        largura_final = min(max(max_text_pixel + 20, min_width), max_width)
        self.tree_materias.column("NomeMateria", width=largura_final, stretch=False)

    def inserir_disciplina(self):
        nome = self.entry_disciplina.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "Digite o nome da disciplina.")
            return
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO disciplina (nome) VALUES (?)", (nome,))
        conn.commit()
        conn.close()
        self.entry_disciplina.delete(0, tk.END)
        self.refresh_disciplinas()
        messagebox.showinfo("Sucesso", "Disciplina adicionada com sucesso!")
        if hasattr(self, "frame_planejar"):
            self.frame_planejar.refresh()

    def remover_disciplina(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma disciplina para remover.")
            return
        disciplina_id = selected[0]
        if messagebox.askyesno("Confirmação", "Tem certeza que deseja remover esta disciplina e TODAS as matérias associadas?"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM materia WHERE disciplina_id=?", (disciplina_id,))
            c.execute("DELETE FROM disciplina WHERE id=?", (disciplina_id,))
            conn.commit()
            conn.close()
            self.refresh_disciplinas()
            messagebox.showinfo("Sucesso", "Disciplina e suas matérias removidas.")
            if hasattr(self, "frame_planejar"):
                self.frame_planejar.refresh()

    def inserir_materia(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma disciplina para adicionar a matéria.")
            return
        nome = self.entry_materia.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "Digite o nome da matéria.")
            return
        disciplina_id = selected[0]
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO materia (nome, disciplina_id) VALUES (?, ?)", (nome, disciplina_id))
        conn.commit()
        conn.close()
        self.entry_materia.delete(0, tk.END)
        self.refresh_materias(disciplina_id)
        messagebox.showinfo("Sucesso", "Matéria adicionada com sucesso!")

    def remover_materia(self):
        # Exclui diretamente a matéria selecionada na Treeview de matérias
        selected_disciplina = self.tree.selection()
        selected_materia = self.tree_materias.selection()
        if not selected_disciplina:
            messagebox.showwarning("Aviso", "Selecione uma disciplina para remover a matéria.")
            return
        if not selected_materia:
            messagebox.showwarning("Aviso", "Selecione a matéria para remover.")
            return
        disciplina_id = selected_disciplina[0]
        materia_id = selected_materia[0]
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM materia WHERE id=?", (materia_id,))
        conn.commit()
        conn.close()
        self.refresh_materias(disciplina_id)
        messagebox.showinfo("Sucesso", "Matéria removida com sucesso!")