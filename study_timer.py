import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import math
import threading

# ----- Appearance & Theme -----
ctk.set_appearance_mode("dark")      # "light" or "dark"
ctk.set_default_color_theme("blue")  # "blue", "green", or "dark-blue"

class ModernStudyTimer:
    def __init__(self, master):
        self.master = master
        self.master.title("Modern Study Timer")
        self.master.geometry("450x650")
        self.master.resizable(False, False)

        self.running = False
        self.paused = False
        self.remaining_time = 0
        self.session_count = 0
        self.timer_thread = None

        self.create_widgets()

    def create_widgets(self):
        # ----- Main Frame (rounded corners) -----
        self.main_frame = ctk.CTkFrame(self.master, corner_radius=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ----- Title / Heading -----
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="Modern Study Timer",
            font=("Helvetica", 24, "bold")
        )
        title_label.pack(pady=(20, 10))

        # ----- Canvas for Timer & Progress Arc -----
        # We will draw both the static circular outline and the dynamic arc on the same canvas
        self.clock_canvas = tk.Canvas(
            self.main_frame,
            width=300,
            height=300,
            bg='#2a2d2e',        # background matches dark theme
            highlightthickness=0 # remove border highlight
        )
        self.clock_canvas.pack(pady=10)

        # 1) Draw background circle (for a subtle ring) 
        self.clock_canvas.create_oval(
            10, 10, 290, 290,
            outline='#3a7ebf',
            width=2
        )

        # 2) Create the progress arc (initially 0 extent)
        self.progress_arc = self.clock_canvas.create_arc(
            10, 10, 290, 290,
            start=90,           # start from top (12 o'clock)
            extent=0,           # how wide the arc is
            fill='',
            outline='#1f6aa5',  # can change color if desired
            width=10,
            style=tk.ARC
        )

        # 3) Create a text item in the center for the timer display
        self.timer_var = tk.StringVar(value="25:00")
        self.timer_display = self.clock_canvas.create_text(
            150, 150,
            text="25:00",
            font=("Helvetica", 40, "bold"),
            fill='white'
        )

        # ----- Session Counter -----
        self.session_var = tk.StringVar(value="Session: 0")
        self.session_label = ctk.CTkLabel(self.main_frame, textvariable=self.session_var, font=("Helvetica", 16))
        self.session_label.pack(pady=(10, 5))

        # ----- Buttons Frame -----
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(pady=20)

        # Start Button
        self.start_button = ctk.CTkButton(button_frame, text="Start", command=self.start_timer, width=80)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)

        # Pause/Resume Button
        self.pause_button = ctk.CTkButton(button_frame, text="Pause", command=self.pause_timer, state=tk.DISABLED, width=80)
        self.pause_button.grid(row=0, column=1, padx=5, pady=5)

        # Reset Button
        self.reset_button = ctk.CTkButton(button_frame, text="Reset", command=self.reset_timer, width=80)
        self.reset_button.grid(row=0, column=2, padx=5, pady=5)

        # ----- Mode Selection -----
        mode_frame = ctk.CTkFrame(self.main_frame)
        mode_frame.pack(pady=10)

        self.mode_var = ctk.StringVar(value="pomodoro")

        pomodoro_radio = ctk.CTkRadioButton(mode_frame, text="Pomodoro", variable=self.mode_var, value="pomodoro")
        pomodoro_radio.pack(side=tk.LEFT, padx=10)

        custom_radio = ctk.CTkRadioButton(mode_frame, text="Custom", variable=self.mode_var, value="custom")
        custom_radio.pack(side=tk.LEFT, padx=10)

        # ----- Custom Time Entry -----
        custom_frame = ctk.CTkFrame(self.main_frame)
        custom_frame.pack(pady=(5, 20))

        ctk.CTkLabel(custom_frame, text="Custom Time (minutes):", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.custom_entry = ctk.CTkEntry(custom_frame, width=60, corner_radius=6)
        self.custom_entry.pack(side=tk.LEFT, padx=5)
        self.custom_entry.insert(0, "25")

    # ----- Timer Methods -----

    def start_timer(self):
        if not self.running:
            self.running = True
            self.paused = False
            self.start_button.configure(state=tk.DISABLED)
            self.pause_button.configure(state=tk.NORMAL)

            if self.mode_var.get() == "pomodoro":
                self.pomodoro_cycle()
            else:
                try:
                    custom_time = int(self.custom_entry.get())
                    self.countdown(custom_time * 60)
                except ValueError:
                    messagebox.showerror("Invalid Input", "Please enter a valid number of minutes.")
                    self.reset_timer()

    def pomodoro_cycle(self):
        """
        Pomodoro cycle logic:
          - 4 study sessions of 25 minutes, each followed by a 5-minute break.
          - After 4 sessions, a longer 15-minute break, then repeat.
        """
        if self.session_count < 4:
            self.countdown(25 * 60)  # 25 minutes study
            if self.running:
                self.session_count += 1
                self.session_var.set(f"Session: {self.session_count}")
                if self.session_count < 4:
                    self.countdown(5 * 60)  # 5 minutes break
        else:
            self.countdown(15 * 60)  # 15 minutes long break
            self.session_count = 0
            self.session_var.set(f"Session: {self.session_count}")

        # Repeat cycle if still running
        if self.running:
            self.pomodoro_cycle()

    def countdown(self, seconds):
        self.remaining_time = seconds
        total_time = seconds

        def count():
            if self.running and not self.paused:
                if self.remaining_time > 0:
                    mins, secs = divmod(self.remaining_time, 60)
                    time_str = f"{mins:02d}:{secs:02d}"
                    self.clock_canvas.itemconfig(self.timer_display, text=time_str)

                    # update progress arc
                    progress = (total_time - self.remaining_time) / total_time
                    self.update_progress_arc(progress)

                    self.remaining_time -= 1
                    self.master.after(1000, count)
                else:
                    self.timer_finished()

        # Run the countdown in a separate thread
        self.timer_thread = threading.Thread(target=count)
        self.timer_thread.start()

    def update_progress_arc(self, progress):
        """Update the arc extent based on fraction of elapsed time."""
        angle = int(360 * progress)
        self.clock_canvas.itemconfig(self.progress_arc, extent=angle)

    def pause_timer(self):
        if self.running:
            if self.paused:
                self.paused = False
                self.pause_button.configure(text="Pause")
            else:
                self.paused = True
                self.pause_button.configure(text="Resume")

    def reset_timer(self):
        self.running = False
        self.paused = False
        self.remaining_time = 0
        self.session_count = 0

        # Reset display
        self.clock_canvas.itemconfig(self.timer_display, text="25:00")
        self.session_var.set("Session: 0")
        self.update_progress_arc(0)

        # Reset buttons
        self.start_button.configure(state=tk.NORMAL)
        self.pause_button.configure(state=tk.DISABLED, text="Pause")

    def timer_finished(self):
        """Called when countdown reaches zero."""
        self.reset_timer()
        messagebox.showinfo("Timer Finished", "Time's up! Take a break or start a new session.")

# ----- Run the App -----
if __name__ == "__main__":
    root = ctk.CTk()
    app = ModernStudyTimer(root)
    root.mainloop()
