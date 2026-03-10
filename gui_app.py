"""
ArgoCD Log Analyzer — Windows Desktop Application
A polished GUI tool for DevOps / Application engineers to analyze
ArgoCD, Pod, and Application logs using the Bosch LLM.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import math
import re

# Ensure imports work from any working directory or frozen exe
if getattr(sys, "frozen", False):
    _app_dir = os.path.dirname(sys.executable)
else:
    _app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _app_dir)

from analyzer import analyze_log, detect_log_type

# ── ArgoCD Color Palette ──────────────────────────────────────────────
C = {
    "bg":         "#0d1117",
    "bg2":        "#101820",
    "card":       "#161b22",
    "card_hi":    "#1c2330",
    "input":      "#0d1117",
    "fg":         "#c9d1d9",
    "fg_dim":     "#8b949e",
    "fg_bright":  "#f0f6fc",
    "accent":     "#0dadea",
    "accent_dim": "#0a8abb",
    "green":      "#18be94",
    "green_dim":  "#14a37f",
    "border":     "#30363d",
    "border_hi":  "#3d444d",
    "btn_fg":     "#0d1117",
    "warn":       "#f4c030",
    "err":        "#e96d76",
    "purple":     "#a371f7",
    "orange":     "#d29922",
    "sidebar":    "#0c111a",
}

FONT       = ("Segoe UI", 10)
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_SUB   = ("Segoe UI", 11)
FONT_MONO  = ("Cascadia Code", 9)
FONT_SM    = ("Segoe UI", 9)
FONT_XS    = ("Segoe UI", 8)
FONT_H2    = ("Segoe UI", 12, "bold")
FONT_BIG   = ("Segoe UI", 22, "bold")


# ── Custom Widgets ────────────────────────────────────────────────────

class AccentCard(tk.Frame):
    """A card with a coloured left accent bar."""
    def __init__(self, parent, accent_color=None, **kw):
        super().__init__(parent, bg=C["card"], **kw)
        accent_color = accent_color or C["accent"]
        self._bar = tk.Frame(self, bg=accent_color, width=4)
        self._bar.pack(side="left", fill="y")
        self.inner = tk.Frame(self, bg=C["card"])
        self.inner.pack(side="left", fill="both", expand=True, padx=14, pady=12)


class HoverButton(tk.Canvas):
    """A flat button with smooth hover color transition."""
    def __init__(self, parent, text="", command=None, bg_normal=None,
                 bg_hover=None, fg=None, font=None, width=160, height=38, **kw):
        super().__init__(parent, width=width, height=height,
                         bg=C["bg"], highlightthickness=0, **kw)
        self._bg_n = bg_normal or C["accent"]
        self._bg_h = bg_hover or C["green"]
        self._fg = fg or C["btn_fg"]
        self._font = font or ("Segoe UI", 11, "bold")
        self._cmd = command
        self._text = text
        self._bw = width
        self._bh = height
        self._enabled = True

        self._draw(self._bg_n)
        self.bind("<Enter>",      lambda _: self._on_enter())
        self.bind("<Leave>",      lambda _: self._on_leave())
        self.bind("<Button-1>",   lambda _: self._on_click())

    def _draw(self, bg):
        self.delete("all")
        r = 6
        w, h = self._bw, self._bh
        self.create_arc(0, 0, r*2, r*2, start=90, extent=90, fill=bg, outline=bg)
        self.create_arc(w-r*2, 0, w, r*2, start=0, extent=90, fill=bg, outline=bg)
        self.create_arc(0, h-r*2, r*2, h, start=180, extent=90, fill=bg, outline=bg)
        self.create_arc(w-r*2, h-r*2, w, h, start=270, extent=90, fill=bg, outline=bg)
        self.create_rectangle(r, 0, w-r, h, fill=bg, outline=bg)
        self.create_rectangle(0, r, w, h-r, fill=bg, outline=bg)
        fg = self._fg if self._enabled else C["fg_dim"]
        self.create_text(w//2, h//2, text=self._text, fill=fg, font=self._font)

    def _on_enter(self):
        if self._enabled:
            self._draw(self._bg_h)

    def _on_leave(self):
        self._draw(self._bg_n if self._enabled else C["border"])

    def _on_click(self):
        if self._enabled and self._cmd:
            self._cmd()

    def set_enabled(self, val):
        self._enabled = val
        self._draw(self._bg_n if val else C["border"])

    def configure_bg(self, parent_bg):
        self.configure(bg=parent_bg)


class Spinner(tk.Canvas):
    """Animated arc spinner."""
    def __init__(self, parent, size=22, color=None, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=C["bg"], highlightthickness=0, **kw)
        self._size = size
        self._color = color or C["accent"]
        self._angle = 0
        self._running = False

    def start(self):
        self._running = True
        self._tick()

    def stop(self):
        self._running = False
        self.delete("all")

    def _tick(self):
        if not self._running:
            return
        self.delete("all")
        pad = 2
        self.create_arc(pad, pad, self._size - pad, self._size - pad,
                        start=self._angle, extent=80,
                        outline=self._color, width=3, style="arc")
        self._angle = (self._angle + 18) % 360
        self.after(40, self._tick)


class LogTypeBadge(tk.Canvas):
    """A rounded badge showing the detected log type."""
    def __init__(self, parent, **kw):
        super().__init__(parent, height=28, highlightthickness=0, **kw)
        self.configure(bg=C["card"])
        self._text_id = None

    def set_type(self, log_type: str):
        color_map = {
            "ArgoCD":            C["accent"],
            "Pod / Kubernetes":  C["green"],
            "Application":       C["purple"],
            "Unknown / Mixed":   C["orange"],
        }
        bg = color_map.get(log_type, C["border"])
        label = f"  {log_type}  "
        self.delete("all")
        # Measure text width
        tid = self.create_text(0, 0, text=label, font=("Segoe UI", 9, "bold"), anchor="nw")
        bbox = self.bbox(tid)
        self.delete(tid)
        tw = bbox[2] - bbox[0] + 16
        self.configure(width=tw)
        # Rounded rect
        r = 5
        self.create_arc(0, 0, r*2, r*2, start=90, extent=90, fill=bg, outline=bg)
        self.create_arc(tw-r*2, 0, tw, r*2, start=0, extent=90, fill=bg, outline=bg)
        self.create_arc(0, 28-r*2, r*2, 28, start=180, extent=90, fill=bg, outline=bg)
        self.create_arc(tw-r*2, 28-r*2, tw, 28, start=270, extent=90, fill=bg, outline=bg)
        self.create_rectangle(r, 0, tw-r, 28, fill=bg, outline=bg)
        self.create_rectangle(0, r, tw, 28-r, fill=bg, outline=bg)
        self.create_text(tw//2, 14, text=label, fill=C["btn_fg"],
                         font=("Segoe UI", 9, "bold"))

    def clear(self):
        self.delete("all")
        self.configure(width=0)


# ── Main Application ─────────────────────────────────────────────────

class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ArgoCD Log Analyzer")
        self.root.geometry("1080x820")
        self.root.minsize(860, 620)
        self.root.configure(bg=C["bg"])

        # State
        self._placeholder = True
        self._result_text = ""
        self._line_count = tk.StringVar(value="0 lines")

        self._setup_styles()
        self._build_sidebar()
        self._build_main()
        self._bind_keys()

    # ── Styles ────────────────────────────────────────────────────────
    def _setup_styles(self):
        s = ttk.Style()
        s.theme_use("clam")

        s.configure("Dark.TFrame",     background=C["bg"])
        s.configure("Card.TFrame",     background=C["card"])
        s.configure("Sidebar.TFrame",  background=C["sidebar"])

        s.configure("Title.TLabel",    background=C["bg"],      foreground=C["accent"],    font=FONT_TITLE)
        s.configure("Dark.TLabel",     background=C["bg"],      foreground=C["fg"],        font=FONT)
        s.configure("Card.TLabel",     background=C["card"],    foreground=C["fg"],        font=FONT)
        s.configure("Head.TLabel",     background=C["card"],    foreground=C["fg_bright"], font=FONT_H2)
        s.configure("Status.TLabel",   background=C["bg"],      foreground=C["fg_dim"],    font=FONT_SM)
        s.configure("Sidebar.TLabel",  background=C["sidebar"], foreground=C["fg_dim"],    font=FONT_SM)
        s.configure("SBHead.TLabel",   background=C["sidebar"], foreground=C["fg"],        font=FONT_BOLD)
        s.configure("SBAccent.TLabel", background=C["sidebar"], foreground=C["accent"],    font=FONT_BIG)

        s.configure("Sec.TButton",
                    background=C["card"], foreground=C["fg"],
                    font=FONT, padding=(12, 5))
        s.map("Sec.TButton",
              background=[("active", C["border"]), ("pressed", C["border_hi"])])

        s.configure("Dark.TCombobox",
                    fieldbackground=C["input"], background=C["border"],
                    foreground=C["fg"], font=FONT)

        s.configure("Accent.TSeparator", background=C["accent"])

    # ── Sidebar ───────────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = tk.Frame(self.root, bg=C["sidebar"], width=230)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        inner = tk.Frame(sb, bg=C["sidebar"])
        inner.pack(fill="both", expand=True, padx=18, pady=24)

        # ── Logo — larger canvas with glow effect
        logo_cv = tk.Canvas(inner, width=64, height=64,
                            bg=C["sidebar"], highlightthickness=0)
        logo_cv.pack(anchor="w", pady=(0, 6))
        # Outer glow ring
        logo_cv.create_oval(2, 2, 62, 62, outline=C["border"], width=1)
        # Main circle
        logo_cv.create_oval(6, 6, 58, 58, outline=C["accent"], width=2.5)
        # Sync arcs (ArgoCD style)
        logo_cv.create_arc(16, 16, 48, 48, start=20, extent=130,
                           outline=C["green"], width=2.5, style="arc")
        logo_cv.create_arc(16, 16, 48, 48, start=200, extent=130,
                           outline=C["accent"], width=2.5, style="arc")
        # Arrow heads on arcs
        logo_cv.create_polygon(42, 22, 48, 20, 44, 26, fill=C["green"], outline=C["green"])
        logo_cv.create_polygon(22, 42, 16, 44, 20, 38, fill=C["accent"], outline=C["accent"])
        # Center dot
        logo_cv.create_oval(28, 28, 36, 36, fill=C["accent"], outline=C["accent"])

        tk.Label(inner, text="ArgoCD", bg=C["sidebar"],
                 fg=C["fg_bright"], font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(inner, text="Log Analyzer", bg=C["sidebar"],
                 fg=C["accent"], font=("Segoe UI", 13)).pack(anchor="w", pady=(0, 2))
        tk.Label(inner, text="v2.0", bg=C["sidebar"],
                 fg=C["fg_dim"], font=FONT_XS).pack(anchor="w")

        # ── Divider with accent dot
        div1 = tk.Frame(inner, bg=C["sidebar"], height=20)
        div1.pack(fill="x", pady=(12, 0))
        tk.Frame(div1, bg=C["border"], height=1).place(relx=0, rely=0.5, relwidth=0.42)
        dot_cv = tk.Canvas(div1, width=8, height=8, bg=C["sidebar"], highlightthickness=0)
        dot_cv.place(relx=0.5, rely=0.5, anchor="center")
        dot_cv.create_oval(1, 1, 7, 7, fill=C["accent"], outline=C["accent"])
        tk.Frame(div1, bg=C["border"], height=1).place(relx=0.58, rely=0.5, relwidth=0.42)

        # ── Supported Log Types section
        tk.Label(inner, text="SUPPORTED LOG TYPES", bg=C["sidebar"],
                 fg=C["fg_dim"], font=FONT_XS).pack(anchor="w", pady=(14, 10))

        type_info = [
            ("\u2699\ufe0f  ArgoCD Logs",       C["accent"],  "Sync errors, health status,\ncontroller events"),
            ("\U0001f4e6  Pod / K8s Logs",       C["green"],   "CrashLoopBackOff, OOMKill,\nscheduling failures"),
            ("\U0001f4bb  Application Logs",     C["purple"],  "Exceptions, stack traces,\nconnection errors"),
        ]
        for label, color, desc in type_info:
            row = tk.Frame(inner, bg=C["sidebar"])
            row.pack(fill="x", pady=4)
            # Color indicator bar
            tk.Frame(row, bg=color, width=3).pack(side="left", fill="y", padx=(0, 8))
            text_frame = tk.Frame(row, bg=C["sidebar"])
            text_frame.pack(side="left", fill="x")
            tk.Label(text_frame, text=label, bg=C["sidebar"],
                     fg=C["fg"], font=("Segoe UI", 9, "bold"), anchor="w").pack(anchor="w")
            tk.Label(text_frame, text=desc, bg=C["sidebar"],
                     fg=C["fg_dim"], font=FONT_XS, anchor="w", justify="left").pack(anchor="w")

        # ── Divider
        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=(16, 12))

        # ── Analysis counter
        self._analysis_count = 0
        tk.Label(inner, text="SESSION STATS", bg=C["sidebar"],
                 fg=C["fg_dim"], font=FONT_XS).pack(anchor="w", pady=(0, 8))

        stats_frame = tk.Frame(inner, bg=C["card_hi"], padx=12, pady=10)
        stats_frame.pack(fill="x")

        stat_row1 = tk.Frame(stats_frame, bg=C["card_hi"])
        stat_row1.pack(fill="x", pady=(0, 4))
        tk.Label(stat_row1, text="Analyses Run", bg=C["card_hi"],
                 fg=C["fg_dim"], font=FONT_XS).pack(side="left")
        self._count_lbl = tk.Label(stat_row1, text="0", bg=C["card_hi"],
                                   fg=C["accent"], font=("Segoe UI", 11, "bold"))
        self._count_lbl.pack(side="right")

        stat_row2 = tk.Frame(stats_frame, bg=C["card_hi"])
        stat_row2.pack(fill="x")
        tk.Label(stat_row2, text="Model", bg=C["card_hi"],
                 fg=C["fg_dim"], font=FONT_XS).pack(side="left")
        tk.Label(stat_row2, text="GPT-4o-mini", bg=C["card_hi"],
                 fg=C["green"], font=("Segoe UI", 9, "bold")).pack(side="right")

        # Push footer to bottom
        tk.Frame(inner, bg=C["sidebar"]).pack(fill="both", expand=True)

        # ── Keyboard shortcuts
        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=(0, 10))
        tk.Label(inner, text="KEYBOARD SHORTCUTS", bg=C["sidebar"],
                 fg=C["fg_dim"], font=FONT_XS).pack(anchor="w", pady=(0, 6))
        shortcuts = [
            ("Ctrl + O",     "Open file"),
            ("Ctrl + Enter", "Analyze"),
            ("Ctrl + S",     "Save report"),
        ]
        for key, action in shortcuts:
            row = tk.Frame(inner, bg=C["sidebar"])
            row.pack(fill="x", pady=1)
            # Key badge
            key_lbl = tk.Label(row, text=f" {key} ", bg=C["border"],
                               fg=C["fg"], font=("Cascadia Code", 7))
            key_lbl.pack(side="left", padx=(0, 6))
            tk.Label(row, text=action, bg=C["sidebar"],
                     fg=C["fg_dim"], font=FONT_XS).pack(side="left")

        # ── Bottom branding
        tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=(10, 8))
        brand = tk.Frame(inner, bg=C["sidebar"])
        brand.pack(fill="x")
        tk.Label(brand, text="Powered by", bg=C["sidebar"],
                 fg=C["fg_dim"], font=FONT_XS).pack(side="left")
        tk.Label(brand, text="Bosch LLM", bg=C["sidebar"],
                 fg=C["accent"], font=("Segoe UI", 9, "bold")).pack(side="left", padx=(4, 0))

        # Accent line on right edge
        tk.Frame(sb, bg=C["accent"], width=2).pack(side="right", fill="y")

    # ── Main Content ──────────────────────────────────────────────────
    def _build_main(self):
        main = ttk.Frame(self.root, style="Dark.TFrame")
        main.pack(side="left", fill="both", expand=True)

        content = tk.Frame(main, bg=C["bg"])
        content.pack(fill="both", expand=True, padx=24, pady=20)

        # ── Header
        hdr = tk.Frame(content, bg=C["bg"])
        hdr.pack(fill="x", pady=(0, 16))

        tk.Label(hdr, text="\U0001f50d  Log Analyzer", bg=C["bg"],
                 fg=C["fg_bright"], font=FONT_TITLE).pack(side="left")

        # Status pill
        self.status_pill = tk.Label(hdr, text="  Ready  ", bg=C["green"],
                                    fg=C["btn_fg"], font=("Segoe UI", 9, "bold"))
        self.status_pill.pack(side="right", pady=4)

        # ── Input Card
        inp_card = AccentCard(content, accent_color=C["accent"])
        inp_card.pack(fill="x", pady=(0, 10))
        inner = inp_card.inner

        # Card header row
        inp_hdr = tk.Frame(inner, bg=C["card"])
        inp_hdr.pack(fill="x", pady=(0, 8))

        tk.Label(inp_hdr, text="\U0001f4cb  Log Input", bg=C["card"],
                 fg=C["fg_bright"], font=FONT_H2).pack(side="left")

        self.badge = LogTypeBadge(inp_hdr)
        self.badge.pack(side="right", padx=(8, 0))

        self._line_label = tk.Label(inp_hdr, textvariable=self._line_count,
                                    bg=C["card"], fg=C["fg_dim"], font=FONT_XS)
        self._line_label.pack(side="right", padx=(0, 8))

        # Controls row
        ctrl = tk.Frame(inner, bg=C["card"])
        ctrl.pack(fill="x", pady=(0, 8))

        tk.Label(ctrl, text="Log Type:", bg=C["card"],
                 fg=C["fg_dim"], font=FONT_SM).pack(side="left", padx=(0, 4))

        self.log_type = tk.StringVar(value="auto")
        cb = ttk.Combobox(ctrl, textvariable=self.log_type,
                          values=["auto", "argocd", "pod", "application"],
                          state="readonly", width=13, style="Dark.TCombobox")
        cb.pack(side="left", padx=(0, 12))

        ttk.Button(ctrl, text="\U0001f4c2 Browse", style="Sec.TButton",
                   command=self._browse).pack(side="left", padx=(0, 4))
        ttk.Button(ctrl, text="\U0001f5d1 Clear", style="Sec.TButton",
                   command=self._clear_input).pack(side="left")

        self.file_lbl = tk.StringVar()
        tk.Label(ctrl, textvariable=self.file_lbl, bg=C["card"],
                 fg=C["accent"], font=FONT_SM).pack(side="right")

        # Text input with subtle border
        txt_border = tk.Frame(inner, bg=C["border_hi"], padx=1, pady=1)
        txt_border.pack(fill="x")

        self.log_in = tk.Text(
            txt_border, height=10, bg=C["input"], fg=C["fg"],
            insertbackground=C["accent"], selectbackground=C["accent"],
            selectforeground=C["bg"], font=FONT_MONO,
            relief="flat", padx=10, pady=8, wrap="none",
            undo=True,
        )
        in_sb_y = ttk.Scrollbar(txt_border, orient="vertical", command=self.log_in.yview)
        in_sb_x = ttk.Scrollbar(txt_border, orient="horizontal", command=self.log_in.xview)
        self.log_in.configure(yscrollcommand=in_sb_y.set, xscrollcommand=in_sb_x.set)
        in_sb_y.pack(side="right", fill="y")
        in_sb_x.pack(side="bottom", fill="x")
        self.log_in.pack(fill="x", expand=True)

        self.log_in.insert("1.0", "Paste your ArgoCD / Pod / Application logs here...")
        self.log_in.configure(fg=C["fg_dim"])
        self.log_in.bind("<FocusIn>", self._on_focus)
        self.log_in.bind("<KeyRelease>", self._on_key_release)

        # ── Analyze Button Row
        btn_row = tk.Frame(content, bg=C["bg"])
        btn_row.pack(fill="x", pady=10)

        btn_center = tk.Frame(btn_row, bg=C["bg"])
        btn_center.pack()

        self.spinner = Spinner(btn_center, size=24)
        self.spinner.pack(side="left", padx=(0, 8))

        self.btn = HoverButton(
            btn_center, text="\U0001f50d  Analyze Logs",
            command=self._start,
            bg_normal=C["accent"], bg_hover=C["green"],
            width=200, height=42,
        )
        self.btn.configure_bg(C["bg"])
        self.btn.pack(side="left")

        self.progress = tk.StringVar()
        self.progress_lbl = tk.Label(btn_row, textvariable=self.progress,
                                     bg=C["bg"], fg=C["fg_dim"], font=FONT_SM)
        self.progress_lbl.pack(pady=(6, 0))

        # ── Results Card
        res_card = AccentCard(content, accent_color=C["green"])
        res_card.pack(fill="both", expand=True, pady=(0, 8))
        res_inner = res_card.inner

        res_hdr = tk.Frame(res_inner, bg=C["card"])
        res_hdr.pack(fill="x", pady=(0, 8))

        tk.Label(res_hdr, text="\U0001f4ca  Analysis Results", bg=C["card"],
                 fg=C["fg_bright"], font=FONT_H2).pack(side="left")

        self.save_btn = HoverButton(
            res_hdr, text="\U0001f4be  Save Report", command=self._save,
            bg_normal=C["card"], bg_hover=C["border_hi"],
            fg=C["fg"], font=FONT, width=140, height=32,
        )
        self.save_btn.configure_bg(C["card"])
        self.save_btn.set_enabled(False)
        self.save_btn.pack(side="right")

        res_border = tk.Frame(res_inner, bg=C["border"], padx=1, pady=1)
        res_border.pack(fill="both", expand=True)

        self.res_out = tk.Text(
            res_border, bg=C["input"], fg=C["fg"], font=FONT,
            relief="flat", padx=12, pady=10, wrap="word", state="disabled",
            spacing1=2, spacing3=2,
        )
        res_sb = ttk.Scrollbar(res_border, command=self.res_out.yview)
        self.res_out.configure(yscrollcommand=res_sb.set)
        res_sb.pack(side="right", fill="y")
        self.res_out.pack(side="left", fill="both", expand=True)

        # Configure result text tags for coloring
        self.res_out.tag_configure("heading",
                                   foreground=C["accent"], font=FONT_H2,
                                   spacing1=8, spacing3=4)
        self.res_out.tag_configure("subheading",
                                   foreground=C["green"], font=FONT_BOLD,
                                   spacing1=4, spacing3=2)
        self.res_out.tag_configure("bullet",
                                   foreground=C["fg"], font=FONT, lmargin1=20, lmargin2=30)
        self.res_out.tag_configure("code",
                                   foreground=C["warn"], font=FONT_MONO,
                                   background="#1a1f2b", lmargin1=30, lmargin2=30)
        self.res_out.tag_configure("separator",
                                   foreground=C["border"], font=FONT_SM)
        self.res_out.tag_configure("logtype",
                                   foreground=C["accent"], font=("Segoe UI", 12, "bold"),
                                   spacing1=4, spacing3=8)

        # ── Bottom status bar
        bar = tk.Frame(content, bg=C["bg"])
        bar.pack(fill="x")
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(bar, textvariable=self.status_var, bg=C["bg"],
                 fg=C["fg_dim"], font=FONT_XS).pack(side="left")

    # ── Key bindings ──────────────────────────────────────────────────
    def _bind_keys(self):
        self.root.bind("<Control-o>", lambda _: self._browse())
        self.root.bind("<Control-s>", lambda _: self._save())
        self.root.bind("<Control-Return>", lambda _: self._start())

    # ── Input helpers ─────────────────────────────────────────────────
    def _on_focus(self, _event=None):
        if self._placeholder:
            self.log_in.delete("1.0", "end")
            self.log_in.configure(fg=C["fg"])
            self._placeholder = False

    def _on_key_release(self, _event=None):
        text = self.log_in.get("1.0", "end-1c")
        lines = text.count("\n") + (1 if text else 0)
        self._line_count.set(f"{lines:,} lines")
        # Auto-detect badge
        if len(text) > 20:
            lt = detect_log_type(text)
            self.badge.set_type(lt)
        else:
            self.badge.clear()

    def _focus_input(self):
        self._on_focus()
        self.log_in.focus_set()

    def _browse(self):
        fp = filedialog.askopenfilename(
            title="Select Log File",
            filetypes=[("Log files", "*.log *.txt"), ("All files", "*.*")],
        )
        if not fp:
            return
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Cannot read file:\n{e}")
            return
        self._on_focus()
        self.log_in.delete("1.0", "end")
        self.log_in.insert("1.0", content)
        self.file_lbl.set(f"\U0001f4c4 {os.path.basename(fp)}")
        self.status_var.set(f"Loaded: {fp}")
        self._on_key_release()

    def _clear_input(self):
        self.log_in.delete("1.0", "end")
        self.log_in.insert("1.0", "Paste your ArgoCD / Pod / Application logs here...")
        self.log_in.configure(fg=C["fg_dim"])
        self._placeholder = True
        self.file_lbl.set("")
        self.badge.clear()
        self._line_count.set("0 lines")
        self.status_var.set("Ready")
        self._set_status_pill("Ready", C["green"])

    def _clear_all(self):
        self._clear_input()
        self.res_out.configure(state="normal")
        self.res_out.delete("1.0", "end")
        self.res_out.configure(state="disabled")
        self._result_text = ""
        self.save_btn.set_enabled(False)

    # ── Status pill ───────────────────────────────────────────────────
    def _set_status_pill(self, text, bg):
        self.status_pill.configure(text=f"  {text}  ", bg=bg)

    # ── Analysis ──────────────────────────────────────────────────────
    def _start(self):
        text = self.log_in.get("1.0", "end").strip()
        if not text or self._placeholder:
            messagebox.showwarning("No Input", "Paste log content or browse a file first.")
            return

        self.btn.set_enabled(False)
        self.spinner.start()
        self.progress.set("Analyzing logs with Bosch LLM \u2026")
        self._set_status_pill("Analyzing\u2026", C["warn"])
        self.status_var.set("Sending to LLM\u2026")

        threading.Thread(target=self._run, args=(text,), daemon=True).start()

    def _run(self, text):
        try:
            lt = self.log_type.get()
            result = analyze_log(text, None if lt == "auto" else lt)
            self._result_text = result
            self.root.after(0, self._show_ok, result)
        except Exception as exc:
            self.root.after(0, self._show_err, str(exc))

    def _show_ok(self, result):
        self.spinner.stop()
        self._analysis_count += 1
        self._count_lbl.configure(text=str(self._analysis_count))
        self.res_out.configure(state="normal")
        self.res_out.delete("1.0", "end")
        self._insert_colored(result)
        self.res_out.configure(state="disabled")
        self.btn.set_enabled(True)
        self.save_btn.set_enabled(True)
        self.progress.set("\u2705 Analysis complete!")
        self._set_status_pill("Done", C["green"])
        self.status_var.set("Analysis complete")

    def _show_err(self, msg):
        self.spinner.stop()
        self.res_out.configure(state="normal")
        self.res_out.delete("1.0", "end")
        self.res_out.insert("1.0", f"\u274c Error:\n\n{msg}")
        self.res_out.configure(state="disabled")
        self.btn.set_enabled(True)
        self.progress.set("")
        self._set_status_pill("Error", C["err"])
        self.status_var.set("Error occurred")

    def _insert_colored(self, text):
        """Insert result text with syntax highlighting using tags."""
        in_code = False
        for line in text.split("\n"):
            stripped = line.strip()

            # Code blocks
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                self.res_out.insert("end", line + "\n", "code")
                continue

            # Separator lines (===)
            if re.match(r"^[=\-]{4,}$", stripped):
                self.res_out.insert("end", line + "\n", "separator")
            # Log type detected line
            elif "LOG TYPE DETECTED" in line:
                self.res_out.insert("end", line + "\n", "logtype")
            # Main headings (## )
            elif stripped.startswith("## "):
                self.res_out.insert("end", "\n" + stripped[3:] + "\n", "heading")
            # Sub-headings with bold marker
            elif stripped.startswith("**") and stripped.endswith("**"):
                self.res_out.insert("end", stripped.strip("*") + "\n", "subheading")
            # Numbered items or bullets
            elif re.match(r"^\d+\.", stripped) or stripped.startswith("- "):
                self.res_out.insert("end", line + "\n", "bullet")
            # Everything else
            else:
                self.res_out.insert("end", line + "\n")

    # ── Save ──────────────────────────────────────────────────────────
    def _save(self):
        if not self._result_text:
            messagebox.showinfo("Nothing to save", "Run an analysis first.")
            return
        fp = filedialog.asksaveasfilename(
            title="Save Report", defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not fp:
            return
        try:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self._result_text)
            self.status_var.set(f"Saved: {fp}")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot save:\n{e}")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
