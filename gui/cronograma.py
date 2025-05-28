import tkinter as tk
from tkinter import ttk, messagebox
from database import get_conn
from datetime import datetime, date

DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
PERIODOS = ["Manhã", "Tarde", "Noite"]
TIPOS_ATIVIDADE = ["Aula", "Questões", "Revisão"]

class CronogramaFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#f6fafd")
        self.disciplinas = self.carregar_disciplinas()
        self._build_tabs()
        self.refresh_all_tabs()

    def carregar_disciplinas(self):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, nome FROM disciplina ORDER BY nome ASC")
        disciplinas = c.fetchall()
        conn.close()
        return disciplinas

    def _build_tabs(self):
        self.tabs = ttk.Notebook(self)
        self.frames_dia = {}
        for dia in DIAS:
            frame = tk.Frame(self.tabs, bg="#fafdfe")
            self.frames_dia[dia] = frame
            self.tabs.add(frame, text=dia)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_all_tabs(self):
        for dia in DIAS:
            self._build_day_view(dia)
        self._update_motivational_box()  # Atualiza motivação geral

    def _build_day_view(self, dia):
        frame = self.frames_dia[dia]
        for widget in frame.winfo_children():
            widget.destroy()

        # Título do dia
        tk.Label(frame, text=f"Cronograma de {dia}", font=("Arial", 14, "bold"),
                 bg="#fafdfe", fg="#206090").pack(anchor="w", padx=8, pady=(8,0))

        total_atividades = 0
        realizadas = 0

        for periodo in PERIODOS:
            # Card do período
            card = tk.LabelFrame(frame, text=f"Período: {periodo}", bg="#eaf6fe",
                                 fg="#184886", font=("Arial", 11, "bold"), padx=8, pady=5)
            card.pack(fill="x", padx=14, pady=7)

            atividades = self.get_atividades(dia, periodo)
            total_atividades += len(atividades)
            realizadas += sum(1 for atv in atividades if atv["realizada"])

            if atividades:
                for atv in atividades:
                    self._monta_linha_atividade(card, atv, dia, periodo)
            else:
                tk.Label(card, text="Nenhuma atividade cadastrada.", font=("Arial", 10, "italic"),
                         bg="#eaf6fe", fg="#a0a0a0").pack(anchor="w", pady=(2,2))

            # Botão adicionar
            btn_add = tk.Button(card, text="+ Adicionar atividade", width=22, 
                                command=lambda d=dia, p=periodo: self.popup_add_atividade(d, p),
                                bg="#65d6ce", fg="#fff", font=("Arial", 10, "bold"), cursor="hand2", relief="ridge", activebackground="#35b3a9")
            btn_add.pack(anchor="w", pady=(5,0))

        # Resumo do dia
        resumo_txt = f"Resumo: {realizadas}/{total_atividades} realizadas"
        tk.Label(frame, text=resumo_txt, font=("Arial", 11, "bold"),
                 bg="#fafdfe", fg="#206090").pack(anchor="w", padx=8, pady=(10,8))
        
        # Caixa de motivação do dia
        motivacao = self._get_motivational_message(realizadas, total_atividades, dia)
        if motivacao:
            box = tk.LabelFrame(frame, text="Motivação do dia", bg="#e1fbe1", fg="#157c2b", font=("Arial", 10, "bold"))
            box.pack(fill="x", padx=14, pady=(0, 12))
            tk.Label(box, text=motivacao, bg="#e1fbe1", fg="#157c2b", font=("Arial", 11, "italic")).pack(anchor="w", padx=6, pady=(1, 6))

    def get_atividades(self, dia, periodo):
        conn = get_conn()
        c = conn.cursor()
        # Adiciona campos se não existirem
        try:
            c.execute("ALTER TABLE cronograma ADD COLUMN realizada INTEGER DEFAULT 0")
        except Exception:
            pass
        try:
            c.execute("ALTER TABLE cronograma ADD COLUMN data_realizada TEXT")
        except Exception:
            pass
        c.execute("""
            SELECT cr.id, cr.dia_semana, cr.periodo, d.nome, cr.atividade, cr.observacao, cr.realizada, cr.data_realizada
            FROM cronograma cr
            LEFT JOIN disciplina d ON cr.disciplina_id = d.id
            WHERE cr.dia_semana=? AND cr.periodo=? AND (cr.data_ref IS NULL OR cr.data_ref=?)
            ORDER BY cr.id ASC
        """, (dia, periodo, None))
        rows = c.fetchall()
        conn.close()
        atividades = []
        for row in rows:
            cid, _, _, disciplina, atividade, obs, realizada, data_realizada = row
            atividades.append({
                "id": cid,
                "disciplina": disciplina or "-",
                "atividade": atividade or "",
                "observacao": obs or "",
                "realizada": realizada or 0,
                "data_realizada": data_realizada
            })
        return atividades

    def _monta_linha_atividade(self, parent, atv, dia, periodo):
        frame = tk.Frame(parent, bg="#eaf6fe")
        frame.pack(fill="x", pady=2, padx=2)

        # Nome e tipo
        cor_tipo = "#2e7d32" if atv["atividade"]=="Aula" else "#d84315" if atv["atividade"]=="Questões" else "#6d28d9"
        label = tk.Label(frame, text=f"{atv['disciplina']} [{atv['atividade']}]", font=("Arial", 11, "bold"),
                         bg="#eaf6fe", fg=cor_tipo)
        label.pack(side="left", padx=(0,7))

        # Observação (se houver)
        if atv["observacao"]:
            obs = tk.Label(frame, text=f"Obs: {atv['observacao']}", font=("Arial", 10, "italic"),
                           bg="#eaf6fe", fg="#505050")
            obs.pack(side="left", padx=(0,6))

        # Botões editar/remover (apenas texto)
        btn_edit = tk.Button(frame, text="Editar", font=("Arial",10), width=8, cursor="hand2", bg="#f0f5ff", fg="#1a237e",
                             relief="flat", activebackground="#c2cfff",
                             command=lambda:self.popup_edit_atividade(atv, dia, periodo))
        btn_edit.pack(side="left", padx=(8,1))
        btn_edit.bind("<Enter>", lambda e: btn_edit.config(bg="#d0e8ff"))
        btn_edit.bind("<Leave>", lambda e: btn_edit.config(bg="#f0f5ff"))

        btn_del = tk.Button(frame, text="Excluir", font=("Arial",10), width=8, cursor="hand2", bg="#fff0f0", fg="#b71c1c",
                            relief="flat", activebackground="#ffc1c1",
                            command=lambda:self.remover_atividade(atv["id"], dia))
        btn_del.pack(side="left", padx=(1,4))
        btn_del.bind("<Enter>", lambda e: btn_del.config(bg="#ffd6d6"))
        btn_del.bind("<Leave>", lambda e: btn_del.config(bg="#fff0f0"))

        # Botão registrar realização ao final da linha
        if atv["realizada"]:
            icon = "✅"
            txt = f"Realizada em {atv['data_realizada']}" if atv["data_realizada"] else "Realizada"
            btn_real = tk.Button(frame, text=f"{icon} {txt}", font=("Arial", 9), bg="#eaf6fe", relief="flat",
                                 fg="#157c2b", state="disabled", disabledforeground="#157c2b")
            btn_real.pack(side="right", padx=(7,0))
        else:
            btn_real = tk.Button(frame, text="🕓 Registrar realização", font=("Arial", 9, "bold"),
                                 bg="#d7f5ec", fg="#137a61", relief="groove",
                                 command=lambda:self.registrar_realizacao(atv, dia),
                                 cursor="hand2", activebackground="#99f0d7")
            btn_real.pack(side="right", padx=(7,0))
            # Tooltip simples
            btn_real.bind("<Enter>", lambda e: self._show_tooltip(btn_real, "Clique para registrar quando realizar a atividade"))
            btn_real.bind("<Leave>", lambda e: self._hide_tooltip())

    def _show_tooltip(self, widget, text):
        self.tooltip = tk.Toplevel(widget)
        self.tooltip.wm_overrideredirect(True)
        x = widget.winfo_rootx() + 40
        y = widget.winfo_rooty() + 20
        self.tooltip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1,
                 font=("Arial", 9)).pack(ipadx=4, ipady=1)

    def _hide_tooltip(self):
        if hasattr(self, "tooltip"):
            self.tooltip.destroy()
            del self.tooltip

    def popup_add_atividade(self, dia, periodo):
        self.popup_atividade(dia, periodo)

    def popup_edit_atividade(self, atv, dia, periodo):
        self.popup_atividade(dia, periodo, atv)

    def popup_atividade(self, dia, periodo, atv=None):
        popup = tk.Toplevel(self)
        popup.title("Editar atividade" if atv else "Adicionar atividade")
        popup.configure(bg="#fafdfe")
        popup.resizable(False, False)

        # Disciplina
        tk.Label(popup, text="Disciplina:", font=("Arial", 11), bg="#fafdfe").grid(row=0, column=0, padx=7, pady=7, sticky="e")
        combo_disc = ttk.Combobox(popup, values=[d[1] for d in self.disciplinas], state="readonly", width=18)
        combo_disc.grid(row=0, column=1, padx=7, pady=7)
        if atv:
            try:
                idx = [d[1] for d in self.disciplinas].index(atv["disciplina"])
                combo_disc.current(idx)
            except ValueError:
                combo_disc.current(0)
        else:
            combo_disc.current(0)
        # Atividade
        tk.Label(popup, text="Atividade:", font=("Arial", 11), bg="#fafdfe").grid(row=1, column=0, padx=7, pady=7, sticky="e")
        combo_ativ = ttk.Combobox(popup, values=TIPOS_ATIVIDADE, state="readonly", width=18)
        combo_ativ.grid(row=1, column=1, padx=7, pady=7)
        if atv and atv["atividade"] in TIPOS_ATIVIDADE:
            combo_ativ.current(TIPOS_ATIVIDADE.index(atv["atividade"]))
        else:
            combo_ativ.current(0)

        # Observação
        tk.Label(popup, text="Observação:", font=("Arial", 11), bg="#fafdfe").grid(row=2, column=0, padx=7, pady=7, sticky="e")
        entry_obs = tk.Entry(popup, width=24)
        entry_obs.grid(row=2, column=1, padx=7, pady=7, sticky="w")
        if atv:
            entry_obs.insert(0, atv["observacao"])

        def salvar():
            disciplina_nome = combo_disc.get()
            atividade = combo_ativ.get()
            observacao = entry_obs.get().strip()
            disciplina_id = next((d[0] for d in self.disciplinas if d[1] == disciplina_nome), None)
            if not disciplina_id:
                messagebox.showerror("Erro", "Disciplina não encontrada.")
                return
            conn = get_conn()
            c = conn.cursor()
            if atv:
                c.execute("""
                    UPDATE cronograma SET disciplina_id=?, atividade=?, observacao=?
                    WHERE id=?
                """, (disciplina_id, atividade, observacao, atv["id"]))
            else:
                c.execute("""
                    INSERT INTO cronograma 
                    (dia_semana, periodo, disciplina_id, atividade, observacao, realizada, data_realizada)
                    VALUES (?, ?, ?, ?, ?, 0, NULL)
                """, (dia, periodo, disciplina_id, atividade, observacao))
            conn.commit()
            conn.close()
            popup.destroy()
            self._build_day_view(dia)
            self._update_motivational_box()

        tk.Button(popup, text="Salvar", command=salvar, bg="#65d6ce", fg="#fff",
                  font=("Arial", 11, "bold"), width=10, cursor="hand2", activebackground="#35b3a9").grid(row=3, column=0, columnspan=2, pady=12)

        popup.grab_set()  # Modal

    def remover_atividade(self, atividade_id, dia):
        if messagebox.askyesno("Remover", "Deseja realmente remover esta atividade?"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM cronograma WHERE id=?", (atividade_id,))
            conn.commit()
            conn.close()
            self._build_day_view(dia)
            self._update_motivational_box()

    def registrar_realizacao(self, atv, dia):
        # Pop-up para confirmar realização
        popup = tk.Toplevel(self)
        popup.title("Registrar Realização")
        popup.configure(bg="#fafdfe")
        popup.resizable(False, False)

        tk.Label(popup, text="Deseja registrar esta atividade como realizada?", font=("Arial", 11, "bold"),
                 bg="#fafdfe", fg="#137a61").pack(padx=14, pady=(12,6))
        data_label = tk.Label(popup, text=f"Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}", bg="#fafdfe", font=("Arial", 10, "italic"))
        data_label.pack(padx=8, pady=(2, 2))
        tk.Label(popup, text="(Opcional) Observação sobre a realização:", font=("Arial", 10), bg="#fafdfe").pack(padx=8, pady=(10,2))
        entry_obs = tk.Entry(popup, width=32)
        entry_obs.pack(padx=8, pady=(0,10))

        def confirmar():
            observacao = entry_obs.get().strip()
            data_realizada = datetime.now().strftime('%d/%m/%Y %H:%M')
            conn = get_conn()
            c = conn.cursor()
            c.execute("UPDATE cronograma SET realizada=1, data_realizada=?, observacao=? WHERE id=?",
                      (data_realizada, observacao if observacao else atv["observacao"], atv["id"]))
            conn.commit()
            conn.close()
            popup.destroy()
            self._build_day_view(dia)
            self._update_motivational_box()

        tk.Button(popup, text="Registrar", command=confirmar, bg="#65d6ce", fg="#fff",
                  font=("Arial", 11, "bold"), width=12, cursor="hand2", activebackground="#35b3a9").pack(pady=(8,14))

        popup.grab_set()  # Modal

    def _get_motivational_message(self, realizadas, total, dia):
        if total == 0:
            return "Programe-se! Adicione ao menos uma atividade para começar a semana com foco. 🚀"
        if realizadas == total:
            return "Parabéns! Você realizou todas as atividades de hoje! 🏆"
        if realizadas > 0:
            return "Ótimo! Já realizou parte das atividades. Continue firme para finalizar tudo hoje!"
        return "Cada passo conta. Foque em uma atividade por vez e avance no seu objetivo!"

    def _update_motivational_box(self):
        # Mostra um incentivo geral se o usuário estiver indo bem na semana
        total, realizadas = 0, 0
        for dia in DIAS:
            for periodo in PERIODOS:
                atividades = self.get_atividades(dia, periodo)
                total += len(atividades)
                realizadas += sum(1 for atv in atividades if atv["realizada"])
        if hasattr(self, "motivational_box"):
            self.motivational_box.destroy()
        if total == 0:
            return
        percent_real = int((realizadas/total)*100) if total else 0
        msg = ""
        if percent_real == 100:
            msg = "Incrível! Você realizou 100% das atividades da semana! 🎉"
        elif percent_real >= 70:
            msg = "Muito bom! Você realizou mais de 70% das atividades, continue assim! 🚀"
        elif percent_real >= 40:
            msg = "Você já está quase na metade das atividades. Força!"
        else:
            msg = "Cada pequena conquista conta. Avance no seu ritmo!"
        self.motivational_box = tk.LabelFrame(self, text="Motivação da Semana", bg="#e1fbe1", fg="#157c2b", font=("Arial", 10, "bold"))
        self.motivational_box.pack(fill="x", padx=18, pady=(0, 12))
        tk.Label(self.motivational_box, text=msg, bg="#e1fbe1", fg="#157c2b", font=("Arial", 11, "italic")).pack(anchor="w", padx=8, pady=(2, 8))

# Teste isolado
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Cronograma Semanal")
    CronogramaFrame(root).pack(fill="both", expand=True, padx=20, pady=20)
    root.mainloop()