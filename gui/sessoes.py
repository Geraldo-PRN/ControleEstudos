import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from database import get_conn

class Cronometro:
    def __init__(self, label, tempo_callback):
        self.label = label
        self.tempo_callback = tempo_callback
        self.running = False
        self.paused = False
        self.start_time = None
        self.elapsed = timedelta()
        self._job = None

    def _update(self):
        if self.running and not self.paused:
            now = datetime.now()
            self.elapsed = now - self.start_time
            tempo_str = str(self.elapsed).split(".")[0]
            if len(tempo_str) == 7:
                tempo_str = "0" + tempo_str
            self.label.config(text=tempo_str)
            self._job = self.label.after(1000, self._update)

    def play(self):
        if not self.running:
            self.start_time = datetime.now()
            self.elapsed = timedelta()
            self.running = True
            self.paused = False
            self._update()
        elif self.paused:
            self.start_time = datetime.now() - self.elapsed
            self.paused = False
            self._update()

    def pause(self):
        if self.running and not self.paused:
            self.paused = True
            if self._job:
                self.label.after_cancel(self._job)

    def stop(self):
        if self.running:
            if not self.paused and self._job:
                self.label.after_cancel(self._job)
            tempo_str = str(self.elapsed).split(".")[0]
            if len(tempo_str) == 7:
                tempo_str = "0" + tempo_str
            self.tempo_callback(tempo_str)
            self.label.config(text="00:00:00")
            self.running = False
            self.paused = False
            self.elapsed = timedelta()
            self._job = None

class SessoesFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.disciplina_nome_id = {}  # nome -> id
        self.materia_nome_id = {}     # nome -> id
        self.build()
        self.refresh_combo_disc()
        self.refresh_sessoes()

    def build(self):
        self.configure(bg="#f7fafd")
        tk.Label(self, text="Registro de Sessão", font=("Arial", 17, "bold"),
                 bg="#f7fafd", fg="#154b7c", anchor="center").pack(fill="x", padx=20, pady=(14, 2))

        frame_form = tk.Frame(self, bg="#fff", bd=2, relief="groove")
        frame_form.pack(padx=20, pady=(0, 12), fill="x", ipadx=8, ipady=7)

        lbl_font = ("Arial", 11)
        pady_row = 5
        padx_lbl = (8, 2)
        padx_entry = (0, 14)

        # Primeira linha: Disciplina | Tipo | Data
        tk.Label(frame_form, text="Disciplina:", font=lbl_font, bg="#fff", fg="#174a6a").grid(row=0, column=0, sticky="e", pady=pady_row, padx=padx_lbl)
        self.combo_disciplina = ttk.Combobox(frame_form, width=24, state="readonly")
        self.combo_disciplina.grid(row=0, column=1, sticky="w", pady=pady_row, padx=padx_entry)
        self.combo_disciplina.bind("<<ComboboxSelected>>", self.on_disciplina_change)

        tk.Label(frame_form, text="Tipo:", font=lbl_font, bg="#fff", fg="#174a6a").grid(row=0, column=2, sticky="e", pady=pady_row, padx=padx_lbl)
        self.combo_tipo = ttk.Combobox(frame_form, width=16, state="readonly")
        self.combo_tipo['values'] = ["Estudo", "Revisão", "Questões", "outro"]
        self.combo_tipo.current(0)
        self.combo_tipo.grid(row=0, column=3, sticky="w", pady=pady_row, padx=padx_entry)
        self.combo_tipo.bind("<<ComboboxSelected>>", self.on_tipo_change)

        tk.Label(frame_form, text="Data:", font=lbl_font, bg="#fff", fg="#174a6a").grid(row=0, column=4, sticky="e", pady=pady_row, padx=padx_lbl)
        self.entry_data = ttk.Entry(frame_form, width=12)
        self.entry_data.grid(row=0, column=5, sticky="w", pady=pady_row, padx=(0,8))
        self.entry_data.insert(0, datetime.today().strftime("%d/%m/%Y"))

        # Segunda linha: Matéria | Tempo | Anotações
        tk.Label(frame_form, text="Matéria:", font=lbl_font, bg="#fff", fg="#174a6a").grid(row=1, column=0, sticky="e", pady=pady_row, padx=padx_lbl)
        self.combo_materia = ttk.Combobox(frame_form, width=24, state="readonly")
        self.combo_materia.grid(row=1, column=1, sticky="w", pady=pady_row, padx=padx_entry)

        tk.Label(frame_form, text="Tempo (HH:MM:SS):", font=lbl_font, bg="#fff", fg="#174a6a").grid(row=1, column=2, sticky="e", pady=pady_row, padx=padx_lbl)
        self.entry_tempo = ttk.Entry(frame_form, width=12)
        self.entry_tempo.grid(row=1, column=3, sticky="w", pady=pady_row, padx=padx_entry)
        self.entry_tempo.insert(0, "00:00:00")

        tk.Label(frame_form, text="Anotações:", font=lbl_font, bg="#fff", fg="#174a6a").grid(row=1, column=4, sticky="e", pady=pady_row, padx=padx_lbl)
        self.entry_anotacoes = ttk.Entry(frame_form, width=26)
        self.entry_anotacoes.grid(row=1, column=5, sticky="w", pady=pady_row, padx=(0,8))

        # Terceira linha: Cronômetro, Revisão, Botões
        cronometro_card = tk.Frame(frame_form, bg="#eaf4fb", bd=1, relief="solid")
        cronometro_card.grid(row=2, column=0, columnspan=2, pady=(15,6), padx=(8,16), sticky="nsew")
        tk.Label(cronometro_card, text="Cronômetro", font=("Arial", 11, "bold"), bg="#eaf4fb", fg="#125288").pack(pady=(8,1))
        self.lbl_cronometro = tk.Label(cronometro_card, text="00:00:00", fg="#0b5394", bg="#eaf4fb", font=("Consolas", 20, "bold"))
        self.lbl_cronometro.pack(pady=(1,8))
        botoes_cronometro = tk.Frame(cronometro_card, bg="#eaf4fb")
        botoes_cronometro.pack(pady=(0,7))
        self.cronometro = Cronometro(self.lbl_cronometro, self.set_tempo_from_cronometro)
        btn_style = dict(font=("Arial", 10, "bold"), bg="#d9f1fa", fg="#154b7c", bd=0, width=8, height=1, activebackground="#a3d5ff", activeforeground="#0b4576", cursor="hand2")
        tk.Button(botoes_cronometro, text="Play", command=self.cronometro.play, **btn_style).pack(side="left", padx=2)
        tk.Button(botoes_cronometro, text="Pause", command=self.cronometro.pause, **btn_style).pack(side="left", padx=2)
        tk.Button(botoes_cronometro, text="Finalizar", command=self.cronometro.stop, **btn_style).pack(side="left", padx=2)

        tk.Label(frame_form, text="Agendar Revisão:", font=lbl_font, bg="#fff", fg="#174a6a").grid(row=2, column=2, sticky="e", padx=(8,2), pady=(12, 1))
        self.combo_revisao = ttk.Combobox(frame_form, width=15, state="readonly")
        self.combo_revisao['values'] = ["Não", "1 dia", "7 dias", "15 dias", "30 dias", "45 dias", "60 dias"]
        self.combo_revisao.current(0)
        self.combo_revisao.grid(row=2, column=3, sticky="w", padx=(0,12), pady=(12, 1))

        self.btn_registrar = tk.Button(
            frame_form, text="Registrar Sessão", font=("Arial", 11, "bold"),
            bg="#a3d5ff", fg="#174a6a", bd=0, activebackground="#6cb6f2",
            width=17, height=2, cursor="hand2", command=self.registrar_sessao
        )
        self.btn_registrar.grid(row=2, column=4, padx=(8,2), pady=(10,1), sticky="w")

        self.btn_excluir = tk.Button(
            frame_form, text="Excluir Selecionado", font=("Arial", 11, "bold"),
            bg="#ffaaaa", fg="#a10000", bd=0, activebackground="#f29e9e",
            width=17, height=2, cursor="hand2", command=self.excluir_sessao
        )
        self.btn_excluir.grid(row=2, column=5, padx=(2,8), pady=(10,1), sticky="w")

        for col in range(6):
            frame_form.grid_columnconfigure(col, weight=1)

        # Frame histórico de sessões com barra de rolagem
        frame_historico = tk.LabelFrame(
            self, text="Histórico de Sessões", padx=10, pady=10,
            bg="#f7fafd", fg="#174a6a", font=("Arial", 12, "bold")
        )
        frame_historico.pack(fill="both", expand=True, padx=18, pady=(0, 14))

        columns = ("Disciplina", "Matéria", "Tipo", "Data", "Tempo")
        self.tree = ttk.Treeview(frame_historico, columns=columns, show="headings", height=12)
        style = ttk.Style()
        style.configure("Treeview", background="#fff", foreground="#1c3144", fieldbackground="#f5fafd", font=("Arial", 11), rowheight=28)
        style.configure("Treeview.Heading", background="#eaf4fb", foreground="#174a6a", font=("Arial", 11, "bold"))
        self.tree.tag_configure("odd", background="#f5fafd")
        self.tree.tag_configure("even", background="#eaf4fb")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", minwidth=60, width=130)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_historico, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def set_tempo_from_cronometro(self, tempo_str):
        self.entry_tempo.delete(0, tk.END)
        self.entry_tempo.insert(0, tempo_str)

    def refresh_combo_disc(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, nome FROM disciplina")
        self.disciplina_nome_id.clear()
        nomes = []
        for id, nome in c.fetchall():
            self.disciplina_nome_id[nome] = id
            nomes.append(nome)
        self.combo_disciplina['values'] = nomes
        conn.close()
        if nomes:
            self.combo_disciplina.current(0)
            self.on_disciplina_change()
        else:
            self.combo_materia['values'] = []
            self.combo_materia.set("")
            self.materia_nome_id.clear()

    def on_disciplina_change(self, event=None):
        sel = self.combo_disciplina.get()
        if sel:
            disc_id = self.disciplina_nome_id.get(sel)
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT id, nome FROM materia WHERE disciplina_id=?", (disc_id,))
            self.materia_nome_id.clear()
            nomes_mat = []
            for id, nome in c.fetchall():
                self.materia_nome_id[nome] = id
                nomes_mat.append(nome)
            self.combo_materia['values'] = nomes_mat
            self.combo_materia.set("")
            conn.close()
        else:
            self.combo_materia['values'] = []
            self.combo_materia.set("")
            self.materia_nome_id.clear()

    def on_tipo_change(self, event=None):
        tipo = self.combo_tipo.get()
        if tipo == "Revisão":
            self.combo_revisao.set("Não")
            self.combo_revisao.configure(state="disabled")
        else:
            self.combo_revisao.configure(state="readonly")

    def validar_tempo(self, tempo_str):
        try:
            h, m, s = map(int, tempo_str.split(":"))
            return h >= 0 and m >= 0 and s >= 0 and m < 60 and s < 60
        except Exception:
            return False

    def tempo_para_minutos(self, tempo_str):
        h, m, s = map(int, tempo_str.split(":"))
        return h*60 + m + s/60

    def data_ddmmaaaa_para_iso(self, data_str):
        try:
            d = datetime.strptime(data_str, "%d/%m/%Y")
            return d.strftime("%Y-%m-%d")
        except Exception:
            return datetime.today().strftime("%Y-%m-%d")

    def registrar_sessao(self):
        mat_sel = self.combo_materia.get()
        disc_sel = self.combo_disciplina.get()
        tipo = self.combo_tipo.get()
        data_sessao = self.entry_data.get()
        tempo_str = self.entry_tempo.get().strip()
        anot = self.entry_anotacoes.get().strip()
        revisar = self.combo_revisao.get()
        if not (mat_sel and disc_sel and tempo_str and data_sessao):
            messagebox.showwarning("Sessão", "Preencha todos os campos obrigatórios.")
            return
        if not tipo or tipo.strip() == "":
            messagebox.showwarning("Sessão", "Selecione um tipo para a sessão.")
            return
        if not self.validar_tempo(tempo_str):
            messagebox.showwarning("Tempo inválido", "Informe o tempo no formato HH:MM:SS!")
            return
        materia_id = self.materia_nome_id.get(mat_sel)
        disciplina_id = self.disciplina_nome_id.get(disc_sel)
        if materia_id is None or disciplina_id is None:
            messagebox.showwarning("Sessão", "Selecione disciplina e matéria válidas.")
            return
        dur = int(self.tempo_para_minutos(tempo_str))
        data_iso = self.data_ddmmaaaa_para_iso(data_sessao)
        conn = get_conn()
        c = conn.cursor()
        c.execute('''INSERT INTO sessao (materia_id, disciplina_id, data, duracao, tipo, anotacoes)
                     VALUES (?,?,?,?,?,?)''', (materia_id, disciplina_id, data_iso, dur, tipo, anot))
        sessao_id = c.lastrowid
        conn.commit()

        self.refresh_sessoes()

        # SE FOR REVISÃO: marca revisões pendentes como realizadas
        if tipo == "Revisão":
            # Marca como realizada=1 todas as revisões pendentes daquela matéria até a data da sessão
            try:
                c.execute("UPDATE revisao SET realizada=1, data_realizada=? WHERE materia_id=? AND data_revisao<=? AND realizada=0",
                          (data_iso, materia_id, data_iso))
            except Exception:
                c.execute("UPDATE revisao SET realizada=1 WHERE materia_id=? AND data_revisao<=? AND realizada=0",
                          (materia_id, data_iso))
            conn.commit()
            agendar = messagebox.askyesno("Agendar Revisão", "Deseja agendar uma próxima revisão para essa matéria?")
            if agendar:
                dias_opcoes = [1, 7, 15, 30, 45, 60]
                top = tk.Toplevel(self)
                top.title("Nova Revisão")
                tk.Label(top, text="Quando deseja agendar a próxima revisão?", font=("Arial", 11)).pack(pady=(10,5))
                var_combo = ttk.Combobox(top, values=[f"{d} dias" if d > 1 else "1 dia" for d in dias_opcoes], state="readonly", width=12)
                var_combo.current(1)
                var_combo.pack(padx=12, pady=8)
                def confirmar():
                    val = var_combo.get()
                    if not val or not val.split()[0].isdigit():
                        messagebox.showwarning("Revisão", "Escolha um prazo válido.")
                        return
                    dias_nova = int(val.split()[0])
                    data_nova = (datetime.strptime(data_iso, "%Y-%m-%d") + timedelta(days=dias_nova)).strftime("%Y-%m-%d")
                    c.execute('''INSERT INTO revisao (sessao_id, materia_id, data_revisao, tipo)
                                 VALUES (?,?,?,?)''', (sessao_id, materia_id, data_nova, val))
                    conn.commit()
                    top.destroy()
                ttk.Button(top, text="Agendar", command=confirmar).pack(pady=(0,12))
                top.transient(self)
                top.grab_set()
                top.wait_window()
        elif revisar and revisar != "Não" and revisar.split()[0].isdigit():
            dias = int(revisar.split()[0])
            dt_revisao = datetime.strptime(data_iso, "%Y-%m-%d") + timedelta(days=dias)
            data_revisao = dt_revisao.strftime("%Y-%m-%d")
            c.execute('''INSERT INTO revisao (sessao_id, materia_id, data_revisao, tipo)
                         VALUES (?,?,?,?)''', (sessao_id, materia_id, data_revisao, revisar))
            conn.commit()
        conn.close()
        messagebox.showinfo("Sessão registrada", "Sessão registrada com sucesso!")
        self.entry_tempo.delete(0, tk.END)
        self.entry_tempo.insert(0, "00:00:00")
        self.entry_anotacoes.delete(0, tk.END)
        self.combo_tipo.set("")
        self.combo_materia.set("")
        self.combo_disciplina.set("")
        self.combo_revisao.set("")
        self.combo_revisao.configure(state="readonly")

    def refresh_sessoes(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = get_conn()
        c = conn.cursor()
        c.execute('''
            SELECT d.nome, m.nome, s.tipo, s.data, s.duracao
            FROM sessao s
            JOIN materia m ON m.id = s.materia_id
            JOIN disciplina d ON d.id = s.disciplina_id
            ORDER BY s.data DESC, s.id DESC
        ''')
        odd = True
        for disc_nome, mat_nome, tipo, data_db, dur in c.fetchall():
            try:
                data_fmt = datetime.strptime(data_db, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                data_fmt = data_db
            h = dur // 60
            m = dur % 60
            s = 0
            tempo_fmt = f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
            tag = "odd" if odd else "even"
            self.tree.insert('', 'end', values=(disc_nome, mat_nome, tipo, data_fmt, tempo_fmt), tags=(tag,))
            odd = not odd
        conn.close()

    def excluir_sessao(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Excluir", "Selecione uma sessão para excluir.")
            return
        idx = self.tree.index(sel[0])
        conn = get_conn()
        c = conn.cursor()
        c.execute('''
            SELECT s.id
            FROM sessao s
            JOIN materia m ON m.id = s.materia_id
            JOIN disciplina d ON d.id = s.disciplina_id
            ORDER BY s.data DESC, s.id DESC
        ''')
        ids = [row[0] for row in c.fetchall()]
        if idx >= len(ids):
            conn.close()
            messagebox.showerror("Erro", "Sessão não encontrada.")
            return
        sessao_id = ids[idx]
        # Excluir revisões associadas a essa sessão
        c.execute("DELETE FROM revisao WHERE sessao_id=?", (sessao_id,))
        # Excluir sessão
        c.execute("DELETE FROM sessao WHERE id=?", (sessao_id,))
        conn.commit()
        conn.close()
        self.refresh_sessoes()

    def atualizar_disciplinas_materias(self):
        self.refresh_combo_disc()
        self.on_disciplina_change()