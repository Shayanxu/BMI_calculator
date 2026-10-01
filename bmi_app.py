"""Desktop BMI calculator built with tkinter."""

import os
import sys
import tkinter as tk
from tkinter import messagebox

import bmi_core as core

WINDOW_TITLE = "BMI calculator"
WINDOW_WIDTH = 500
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bmi_history.json")

# Theme
BG = "#121212"
CARD = "#1f1f1f"
FIELD = "#2b2b2b"
BUTTON = "#333333"
BUTTON_ACTIVE = "#444444"
ACCENT = "#6c5ce7"
ACCENT_ACTIVE = "#5849c4"
TEXT = "white"
MUTED = "#aaaaaa"
DIM = "#888888"
ERROR = "#ff5555"
DANGER = "#ff6b6b"
FONT = "Arial"

RESULT_PLACEHOLDER = "Your BMI\n--"
GUIDE_TEXT = "Underweight < 18.5 | Normal 18.5-24.9\nOverweight 25-29.9 | Obese ≥ 30"

# The colour bar shows BMI values from BAR_MIN to BAR_MAX, split by the category limits.
BAR_MIN, BAR_MAX = 10, 40
_edges = [BAR_MIN] + [category.upper for category in core.CATEGORIES[:-1]] + [BAR_MAX]
BAR_SEGMENTS = list(zip(_edges[:-1], _edges[1:], [category.color for category in core.CATEGORIES]))


class BMIApp:
    def __init__(self, root):
        self.root = root
        self.history = core.load_history(HISTORY_FILE)
        self.current_bmi = None

        self._configure_window()
        self._build_header()
        self._build_card()
        self._build_history()
        self._build_footer()
        self._bind_events()

        self.refresh_history()
        self._fit_window_to_content()

    # ---------- building the interface ----------

    def _configure_window(self):
        self.root.title(WINDOW_TITLE)
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

    def _label(self, parent, text, size, bold=False, bg=BG, fg=TEXT, **options):
        font = (FONT, size, "bold") if bold else (FONT, size)
        return tk.Label(parent, text=text, font=font, bg=bg, fg=fg, **options)

    def _entry(self, parent):
        entry = tk.Entry(
            parent, font=(FONT, 15), justify="center", bg=FIELD, fg=TEXT,
            insertbackground=TEXT, relief="flat",
        )
        entry.pack(fill="x", pady=(6, 12), ipady=8)
        return entry

    def _button(self, parent, text, command, size, bg=BUTTON, fg=TEXT,
                active=BUTTON_ACTIVE, padx=25, pady=8):
        return tk.Button(
            parent, text=text, command=command, font=(FONT, size, "bold"),
            bg=bg, fg=fg, activebackground=active, activeforeground=fg,
            relief="flat", cursor="hand2", padx=padx, pady=pady,
        )

    def _build_header(self):
        self._label(self.root, "BMI calculator", 24, bold=True).pack(pady=(20, 2))
        self._label(self.root, "Check your Body mass index", 11, fg=MUTED).pack(pady=(0, 12))

    def _build_card(self):
        card = tk.Frame(self.root, bg=CARD, padx=30, pady=15)
        card.pack(padx=30, fill="both")

        self._label(card, "Weight (kg)", 12, bold=True, bg=CARD).pack(anchor="w")
        self.weight_entry = self._entry(card)

        self._label(card, "Height (cm)", 12, bold=True, bg=CARD).pack(anchor="w")
        self.height_entry = self._entry(card)

        self.result_label = self._label(card, RESULT_PLACEHOLDER, 18, bold=True, bg=CARD, height=4)
        self.result_label.pack(pady=8)

        self.bar = tk.Canvas(card, height=26, bg=CARD, highlightthickness=0)
        self.bar.pack(fill="x", pady=(0, 6))
        self.bar.bind("<Configure>", self.draw_bar)

        self.range_label = self._label(card, "", 10, bg=CARD, fg=MUTED, height=1)
        self.range_label.pack(pady=(0, 6))

        self._button(card, "CALCULATE", self.calculate, 13, bg=ACCENT,
                     active=ACCENT_ACTIVE, padx=30, pady=12).pack(pady=(10, 5))
        self._button(card, "RESET", self.reset, 10).pack(pady=5)

    def _build_history(self):
        self._label(self.root, "BMI HISTORY", 14, bold=True).pack(pady=(12, 6))

        frame = tk.Frame(self.root, bg=BG)
        frame.pack(padx=30, fill="x")

        scrollbar = tk.Scrollbar(
            frame, orient="vertical", bg=BUTTON, troughcolor=BG,
            activebackground=BUTTON_ACTIVE, relief="flat", bd=0,
        )
        self.history_list = tk.Listbox(
            frame, height=6, bg=CARD, fg=TEXT, font=(FONT, 10), relief="flat",
            highlightthickness=0, exportselection=False, activestyle="none",
            selectbackground=ACCENT, selectforeground=TEXT, yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self.history_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.history_list.pack(side="left", fill="x", expand=True)

    def _build_footer(self):
        row = tk.Frame(self.root, bg=BG)
        row.pack(pady=8)

        self._button(row, "TREND CHART", self.show_trend, 9,
                     padx=15, pady=7).pack(side="left", padx=4)
        self._button(row, "DELETE SELECTED", self.delete_selected, 9,
                     padx=15, pady=7).pack(side="left", padx=4)
        self._button(row, "CLEAR HISTORY", self.clear_history, 9, fg=DANGER,
                     padx=15, pady=7).pack(side="left", padx=4)

        self._label(self.root, GUIDE_TEXT, 9, fg=DIM, justify="center").pack(pady=8)

    def _bind_events(self):
        self.root.bind("<Return>", lambda event: self.calculate())
        self.weight_entry.focus()

    def _fit_window_to_content(self):
        """Size the window to fit its content, but never taller than the screen."""
        self.root.update_idletasks()
        height = min(self.root.winfo_reqheight(), self.root.winfo_screenheight() - 80)
        self.root.geometry(f"{WINDOW_WIDTH}x{height}")

    # ---------- drawing ----------

    def draw_bar(self, event=None):
        """Draw the coloured BMI scale and, if there is a result, a marker on it."""
        self.bar.delete("all")
        width = self.bar.winfo_width()

        def to_x(value):
            return (value - BAR_MIN) / (BAR_MAX - BAR_MIN) * width

        for start, end, color in BAR_SEGMENTS:
            self.bar.create_rectangle(to_x(start), 14, to_x(end), 24, fill=color, outline=color)

        if self.current_bmi is not None:
            x = to_x(min(max(self.current_bmi, BAR_MIN), BAR_MAX))
            x = min(max(x, 6), width - 6)
            self.bar.create_polygon(x - 6, 1, x + 6, 1, x, 12, fill=TEXT, outline=TEXT)

    def refresh_history(self):
        self.history_list.delete(0, tk.END)
        for record in self.history:
            self.history_list.insert(tk.END, core.describe_record(record))

    # ---------- actions ----------

    def calculate(self):
        try:
            weight = core.parse_number(self.weight_entry.get())
            height = core.parse_number(self.height_entry.get())
        except ValueError:
            self._show_error("please enter numbers only!")
            return

        try:
            record = core.make_record(weight, height)
        except ValueError as error:
            self._show_error(str(error))
            return

        category = core.classify(record["bmi"])
        low, high = core.healthy_weight_range(height)

        self.history.append(record)
        self._save()

        self.result_label.config(
            text=f'Your BMI\n{record["bmi"]:.1f}\n\n{category.name}', fg=category.color
        )
        self.range_label.config(text=f"Healthy weight for your height: {low:.1f} - {high:.1f} kg")
        self.current_bmi = record["bmi"]
        self.draw_bar()
        self.refresh_history()

    def reset(self):
        self.weight_entry.delete(0, tk.END)
        self.height_entry.delete(0, tk.END)

        self.result_label.config(text=RESULT_PLACEHOLDER, fg=TEXT)
        self.range_label.config(text="")
        self.current_bmi = None
        self.draw_bar()

        self.weight_entry.focus()

    def delete_selected(self):
        selection = self.history_list.curselection()
        if not selection:
            return

        del self.history[selection[0]]
        self._save()
        self.refresh_history()

    def clear_history(self):
        self.history.clear()
        self._save()
        self.refresh_history()

    def show_trend(self):
        """Open a window with a chart of the BMI history (needs matplotlib)."""
        if not self.history:
            messagebox.showinfo("No data yet", "Calculate at least one BMI to see the chart.")
            return

        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import bmi_chart
        except ImportError:
            messagebox.showinfo(
                "Chart unavailable",
                "The trend chart needs matplotlib.\n\nInstall it with:\npip install matplotlib",
            )
            return

        window = tk.Toplevel(self.root)
        window.title("BMI trend")
        window.configure(bg=CARD)
        window.geometry("640x420")

        canvas = FigureCanvasTkAgg(bmi_chart.build_figure(self.history), master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---------- helpers ----------

    def _show_error(self, message):
        self.result_label.config(text=message, fg=ERROR)
        self.range_label.config(text="")
        self.current_bmi = None
        self.draw_bar()

    def _save(self):
        try:
            core.save_history(HISTORY_FILE, self.history)
        except OSError as error:
            print(f"Could not save history: {error}", file=sys.stderr)


def main():
    root = tk.Tk()
    BMIApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
