import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import setup_db, criar_novo_banco, listar_bancos, set_active_db
from gui.disciplinas import DisciplinasFrame
from gui.planejamento import PlanejamentoFrame
from gui.sessoes import SessoesFrame
from gui.revisao import RevisaoFrame
from gui.pomodoro import PomodoroFrame
from gui.dashboard import Dashboard
from gui.questoes_simulado import QuestoesSimuladoFrame
from gui.cronograma import CronogramaFrame
import os

def primeira_execucao():
    """
    Detecta se é a primeira execução e cria um banco inicial.
    Exibe pop-up explicativo e solicita nome do banco.
    """
    from database import get_active_db
    db_path = get_active_db()
    if not os.path.exists(db_path):
        # Mensagem explicativa
        explicacao = (
            "Bem-vindo ao Controle de Estudos!\n\n"
            "Para começar, você irá criar um novo banco de dados para armazenar todo o seu histórico de estudos, sessões, estatísticas etc.\n\n"
            "Você pode criar outros bancos no futuro (ex: para concursos diferentes) e acessar seus históricos antigos quando quiser.\n\n"
            "Digite um nome para o seu banco inicial (ex: 'concurso_inicial', 'meus_estudos', etc):"
        )
        while True:
            nome = simpledialog.askstring("Novo banco de dados", explicacao)
            if not nome:
                if messagebox.askyesno("Sair", "É necessário criar um banco de dados para continuar. Deseja sair?"):
                    quit()
                continue
            # Remove espaços e caracteres especiais simples
            nome = ''.join(c for c in nome if c.isalnum() or c in ('_', '-')).strip()
            if not nome:
                messagebox.showerror("Nome inválido", "Digite um nome válido (sem espaços apenas letras, números ou _ -)")
                continue
            criar_novo_banco(nome)
            break

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Controle de Estudos")
        self.geometry("1100x800")
        self.resizable(False, False)
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)
        print("Olá, seja Bem vindo!")

        # Dashboard
        self.frame_dashboard = Dashboard(self.tabs)
        self.tabs.add(self.frame_dashboard, text="Dashboard")

        # Instancia os frames
        self.frame_disc_mat = DisciplinasFrame(self.tabs)
        self.frame_planejar = PlanejamentoFrame(self.tabs)
        self.frame_sessoes = SessoesFrame(self.tabs)
        self.frame_revisao = RevisaoFrame(self.tabs)
        self.frame_pomodoro = PomodoroFrame(self.tabs)
        self.frame_questoes_simulado = QuestoesSimuladoFrame(self.tabs)
        self.frame_cronograma = CronogramaFrame(self.tabs)

        # Referências cruzadas para atualizar em tempo real entre guias
        self.frame_disc_mat.frame_sessoes = self.frame_sessoes
        self.frame_sessoes.frame_disc_mat = self.frame_disc_mat
        self.frame_planejar.frame_disc_mat = self.frame_disc_mat
        self.frame_revisao.frame_disc_mat = self.frame_disc_mat
        self.frame_planejar.frame_disc_mat = self.frame_disc_mat
        self.frame_revisao.frame_disc_mat = self.frame_disc_mat
        self.frame_sessoes.frame_revisao = self.frame_revisao
        self.frame_disc_mat.frame_planejar = self.frame_planejar
        self.frame_disc_mat.frame_questoes_simulado = self.frame_questoes_simulado
        self.frame_questoes_simulado.frame_disc_mat = self.frame_disc_mat

        self.tabs.add(self.frame_disc_mat, text="Disciplinas")
        self.tabs.add(self.frame_planejar, text="Planejamento")
        self.tabs.add(self.frame_cronograma, text="Cronograma")
        self.tabs.add(self.frame_sessoes, text="Sessões")
        self.tabs.add(self.frame_questoes_simulado, text="Questões/Simulado")
        self.tabs.add(self.frame_revisao, text="Revisão")
        self.tabs.add(self.frame_pomodoro, text="Pomodoro")

        # Atualiza combos/listas ao trocar de aba
        self.tabs.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Menu para gerenciar bancos de dados
        #self._add_db_menu()

        self.after(800, self.check_revisoes)

    #def _add_db_menu(self):
    #    menubar = tk.Menu(self)
     #   dbmenu = tk.Menu(menubar, tearoff=0)
      #  dbmenu.add_command(label="Criar novo banco...", command=self.criar_novo_banco_dialogo)
       # dbmenu.add_command(label="Selecionar banco existente...", command=self.selecionar_banco_dialogo)
        #menubar.add_cascade(label="Banco de Dados", menu=dbmenu)
        #self.config(menu=menubar)

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

    def selecionar_banco_dialogo(self):
        bancos = listar_bancos()
        if not bancos:
            messagebox.showinfo("Nenhum banco", "Não há bancos de dados disponíveis.")
            return
        win = tk.Toplevel(self)
        win.title("Selecionar banco de dados")
        win.geometry("380x200")
        tk.Label(win, text="Selecione um banco de dados para ativar:", font=("Arial", 11)).pack(pady=10)
        lb = tk.Listbox(win, font=("Arial", 10), height=6)
        for b in bancos:
            lb.insert(tk.END, b)
        lb.pack(padx=10, fill="both", expand=True)

        def ativar():
            idx = lb.curselection()
            if not idx:
                messagebox.showwarning("Atenção", "Selecione um banco para ativar.")
                return
            nome = lb.get(idx[0])
            from database import DB_FOLDER
            caminho = os.path.join(DB_FOLDER, nome)
            set_active_db(caminho)
            setup_db()
            messagebox.showinfo("Banco ativado", f"O banco '{nome}' está em uso.\n\nReinicie o programa para garantir que todas as telas usem o novo banco.")
            win.destroy()
        tk.Button(win, text="Ativar banco selecionado", command=ativar, bg="#65d6ce", fg="#fff", font=("Arial", 11, "bold")).pack(pady=10)

    def on_tab_changed(self, event):
        tab = event.widget.tab(event.widget.select(), "text")
        if tab == "Dashboard":
            self.frame_dashboard.refresh()
        elif tab == "Sessões":
            self.frame_sessoes.refresh_combo_disc()
            self.frame_sessoes.refresh_sessoes()
        elif tab == "Disciplinas":
            self.frame_disc_mat.refresh_disciplinas()
            items = self.frame_disc_mat.tree.get_children()
            if items:
                first_id = self.frame_disc_mat.tree.item(items[0])['values'][0]
                self.frame_disc_mat.refresh_materias(first_id)
            else:
                self.frame_disc_mat.refresh_materias(None)
        elif tab == "Planejamento":
            if hasattr(self.frame_planejar, "refresh"):
                self.frame_planejar.refresh()
        elif tab == "Revisão":
            if hasattr(self.frame_revisao, "refresh"):
                self.frame_revisao.refresh()
        elif tab == "Questões/Simulado":
            if hasattr(self.frame_questoes_simulado, "refresh"):
                self.frame_questoes_simulado.refresh()
        elif tab == "Cronograma":
            if hasattr(self.frame_cronograma, "refresh"):
                self.frame_cronograma.refresh()

    def check_revisoes(self):
        from database import get_conn
        from datetime import date
        conn = get_conn()
        c = conn.cursor()
        hoje = date.today().isoformat()
        c.execute('''SELECT revisao.id, materia.nome, revisao.data_revisao
                        FROM revisao
                        JOIN materia ON materia.id = revisao.materia_id
                        WHERE revisao.realizada=0 AND revisao.data_revisao<=?''', (hoje,))
        revisoes = c.fetchall()
        conn.close()
        if revisoes:
            materias = '\n'.join([f"{m} (Revisão {d})" for _, m, d in revisoes])
            messagebox.showinfo("Revisões Pendentes", f"Você tem revisões para hoje:\n\n{materias}")

if __name__ == "__main__":
    primeira_execucao()
    setup_db()
    app = App()
    app.mainloop()