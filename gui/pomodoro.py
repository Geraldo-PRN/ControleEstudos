import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import platform

def beep(times=1):
    try:
        if platform.system() == "Windows":
            import winsound
            for _ in range(times):
                winsound.Beep(1000, 350)
        else:
            for _ in range(times):
                print('\a', end='', flush=True)
    except Exception:
        pass

class PomodoroTimer:
    def __init__(
        self,
        update_timer,
        update_status,
        on_cycle_end,
        get_study_time,
        get_short_break,
        get_long_break,
        get_cycles_until_long
    ):
        self.update_timer = update_timer
        self.update_status = update_status
        self.on_cycle_end = on_cycle_end
        self.get_study_time = get_study_time
        self.get_short_break = get_short_break
        self.get_long_break = get_long_break
        self.get_cycles_until_long = get_cycles_until_long
        self.timer_thread = None
        self.timer_running = False
        self.paused = False
        self.current_mode = "focus"
        self.cycles_done = 0

    def start(self):
        if self.timer_running:
            return
        try:
            self.study_minutes = int(self.get_study_time())
            self.short_break = int(self.get_short_break())
            self.long_break = int(self.get_long_break())
            self.cycles_until_long = int(self.get_cycles_until_long())
        except Exception:
            messagebox.showwarning("Pomodoro", "Informe tempos válidos.")
            return
        self.cycles_done = 0
        self.timer_running = True
        self.paused = False
        self.current_mode = "focus"
        self._run_focus()

    def _run_focus(self):
        self.update_status("Foco! 🎯")
        self._start_timer(self.study_minutes * 60, self._focus_finished)

    def _focus_finished(self):
        self.cycles_done += 1
        self.on_cycle_end(self.cycles_done)
        beep(1)
        messagebox.showinfo("Pomodoro", "Pomodoro finalizado! Hora da pausa.")
        if self.cycles_done % self.cycles_until_long == 0:
            self.current_mode = "long_break"
            self._run_long_break()
        else:
            self.current_mode = "short_break"
            self._run_short_break()

    def _run_short_break(self):
        self.update_status("Pausa Curta ⏸️")
        self._start_timer(self.short_break * 60, self._break_finished)

    def _run_long_break(self):
        self.update_status("Pausa Longa ✨")
        self._start_timer(self.long_break * 60, self._break_finished)

    def _break_finished(self):
        beep(2)
        messagebox.showinfo("Pomodoro", "Pausa encerrada! Hora de voltar ao foco.")
        self.update_status("Pronto para novo ciclo!")
        self.current_mode = "focus"
        if self.timer_running:
            self._run_focus()

    def _start_timer(self, total_seconds, finish_callback):
        def timer_func():
            t = total_seconds
            while t > 0 and self.timer_running:
                if not self.paused:
                    mins, secs = divmod(t, 60)
                    self.update_timer(f"{mins:02d}:{secs:02d}")
                    time.sleep(1)
                    t -= 1
                else:
                    time.sleep(0.1)
            if self.timer_running:
                self.update_timer("00:00")
                finish_callback()
        self.timer_thread = threading.Thread(target=timer_func, daemon=True)
        self.timer_thread.start()

    def pause(self):
        if self.timer_running:
            self.paused = True

    def resume(self):
        if self.timer_running:
            self.paused = False

    def stop(self):
        self.timer_running = False
        self.paused = False
        self.update_status("Parado")
        self.update_timer("00:00")

class PomodoroFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#f4fafd")
        self.cycles = 0
        self._build_ui()
        # Agora que as spinboxes existem, crie o PomodoroTimer!
        self.pomodoro = PomodoroTimer(
            update_timer=self.set_timer,
            update_status=self.set_status,
            on_cycle_end=self.on_cycle_end,
            get_study_time=lambda: self.spin_study.get(),
            get_short_break=lambda: self.spin_short_break.get(),
            get_long_break=lambda: self.spin_long_break.get(),
            get_cycles_until_long=lambda: self.spin_cycles.get()
        )
        self._bind_buttons()

    def _build_ui(self):
        tk.Label(self, text="Pomodoro", font=("Arial", 22, "bold"), fg="#25608a", bg="#f4fafd").pack(pady=(20,8))
        config = tk.Frame(self, bg="#f4fafd")
        config.pack(pady=(0,15))
        tk.Label(config, text="Foco (min):", font=("Arial", 11), bg="#f4fafd").grid(row=0, column=0, padx=5)
        self.spin_study = ttk.Spinbox(config, from_=10, to=90, width=4, font=("Arial", 11))
        self.spin_study.set(25)
        self.spin_study.grid(row=0, column=1, padx=2)
        tk.Label(config, text="Pausa curta (min):", font=("Arial", 11), bg="#f4fafd").grid(row=0, column=2, padx=5)
        self.spin_short_break = ttk.Spinbox(config, from_=3, to=30, width=4, font=("Arial", 11))
        self.spin_short_break.set(5)
        self.spin_short_break.grid(row=0, column=3, padx=2)
        tk.Label(config, text="Pausa longa (min):", font=("Arial", 11), bg="#f4fafd").grid(row=0, column=4, padx=5)
        self.spin_long_break = ttk.Spinbox(config, from_=10, to=60, width=4, font=("Arial", 11))
        self.spin_long_break.set(20)
        self.spin_long_break.grid(row=0, column=5, padx=2)
        tk.Label(config, text="Ciclos até pausa longa:", font=("Arial", 11), bg="#f4fafd").grid(row=0, column=6, padx=5)
        self.spin_cycles = ttk.Spinbox(config, from_=2, to=10, width=4, font=("Arial", 11))
        self.spin_cycles.set(4)
        self.spin_cycles.grid(row=0, column=7, padx=2)
        self.label_timer = tk.Label(self, text="25:00", font=("Consolas", 58, "bold"), fg="#25608a", bg="#f4fafd")
        self.label_timer.pack(pady=(10,5))
        self.label_status = tk.Label(self, text="Pronto!", font=("Arial", 15), fg="#1c3144", bg="#f4fafd")
        self.label_status.pack(pady=(0,12))
        btns = tk.Frame(self, bg="#f4fafd")
        btns.pack(pady=(0,14))
        self.btn_start = tk.Button(btns, text="Iniciar", width=10, font=("Arial", 12, "bold"),
                                   bg="#65d6ce", fg="#fff", relief="flat", cursor="hand2")
        self.btn_start.pack(side="left", padx=7)
        self.btn_pause = tk.Button(btns, text="Pausar", width=8, font=("Arial", 12),
                                   bg="#ffc93c", fg="#174a6a", relief="flat", cursor="hand2")
        self.btn_pause.pack(side="left", padx=7)
        self.btn_resume = tk.Button(btns, text="Retomar", width=8, font=("Arial", 12),
                                    bg="#a3de83", fg="#174a6a", relief="flat", cursor="hand2")
        self.btn_resume.pack(side="left", padx=7)
        self.btn_stop = tk.Button(btns, text="Parar", width=8, font=("Arial", 12),
                                  bg="#fc5185", fg="#fff", relief="flat", cursor="hand2")
        self.btn_stop.pack(side="left", padx=7)
        self.label_cycles = tk.Label(self, text="Ciclos completos hoje: 0", font=("Arial", 12), fg="#154b7c", bg="#f4fafd")
        self.label_cycles.pack(pady=(2,10))

    def _bind_buttons(self):
        self.btn_start.config(command=self.pomodoro.start)
        self.btn_pause.config(command=self.pomodoro.pause)
        self.btn_resume.config(command=self.pomodoro.resume)
        self.btn_stop.config(command=self.pomodoro.stop)

    def set_timer(self, text):
        self.label_timer.config(text=text)

    def set_status(self, text):
        self.label_status.config(text=text)

    def on_cycle_end(self, total_cycles):
        self.cycles = total_cycles
        self.label_cycles.config(text=f"Ciclos completos hoje: {self.cycles}")