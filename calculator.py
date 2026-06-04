"""
╔══════════════════════════════════════════════════════════╗
║        NEON QUANTUM CALCULATOR  — AI POWERED             ║
║   Pure Python · No pip installs · Built-in stdlib only   ║
╚══════════════════════════════════════════════════════════╝

HOW TO RUN:
  python neon_calculator.py

REQUIREMENTS:
  • Python 3.8+  (tkinter ships with Python on Windows/Mac/Linux)
  • Internet connection (for AI feature & email OTP)

SETUP (edit the CONFIG section below):
  • SMTP_EMAIL    → your Gmail address
  • SMTP_PASSWORD → your Gmail App Password
                    (Google Account → Security → App Passwords)
  • OPENAI_KEY    → your OpenAI API key
"""

# ── ONLY BUILT-IN STANDARD LIBRARY ──────────────────────────────────────────
import tkinter as tk
from tkinter import ttk, messagebox, font
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import random
import string
import json
import math
import urllib.request
import urllib.error
import threading
import time
import re

# ═══════════════════════════ USER CONFIG ════════════════════════════════════
SMTP_EMAIL    = "your_gmail@gmail.com"       # ← change this
SMTP_PASSWORD = "your_app_password"           # ← change this (Gmail App Password)
OPENAI_KEY    = "your_openai_api_key_here"   # ← change this
# ════════════════════════════════════════════════════════════════════════════

# ── COLOUR PALETTE (Neon Blue + Black) ───────────────────────────────────────
C = {
    "bg":           "#000814",
    "bg2":          "#000d1a",
    "panel":        "#001a33",
    "neon":         "#00d4ff",
    "neon2":        "#0099cc",
    "neon_dim":     "#004466",
    "accent":       "#00ffcc",
    "accent2":      "#00b38a",
    "text":         "#e0f7ff",
    "text_dim":     "#5588aa",
    "danger":       "#ff3366",
    "warn":         "#ffaa00",
    "border":       "#003355",
    "entry_bg":     "#001122",
    "btn_op":       "#003366",
    "btn_num":      "#001f3f",
    "btn_eq":       "#005599",
    "btn_clr":      "#4d0019",
    "btn_ai":       "#003322",
    "glow":         "#00aadd",
}

# ── OTP STORE ─────────────────────────────────────────────────────────────────
_otp_store = {}   # email → {otp, expires}

# ═════════════════════════════════════════════════════════════════════════════
#  UTILITIES
# ═════════════════════════════════════════════════════════════════════════════

def send_otp_email(to_email: str) -> str:
    otp = "".join(random.choices(string.digits, k=6))
    _otp_store[to_email] = {"otp": otp, "expires": time.time() + 300}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🔐 Neon Quantum Calculator — Your OTP"
    msg["From"]    = SMTP_EMAIL
    msg["To"]      = to_email

    html = f"""
    <div style="background:#000814;padding:30px;font-family:monospace;color:#e0f7ff;
                border:2px solid #00d4ff;border-radius:12px;max-width:480px;margin:auto;">
      <h2 style="color:#00d4ff;letter-spacing:3px;text-align:center;">
        ⚡ NEON QUANTUM CALCULATOR
      </h2>
      <p style="color:#5588aa;text-align:center;">Your one-time password</p>
      <div style="background:#001a33;border:1px solid #00d4ff;border-radius:8px;
                  text-align:center;padding:20px;margin:20px 0;">
        <span style="font-size:36px;letter-spacing:12px;color:#00ffcc;
                     font-weight:bold;">{otp}</span>
      </div>
      <p style="color:#5588aa;text-align:center;font-size:12px;">
        Valid for 5 minutes. Do not share this code.
      </p>
    </div>"""

    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(SMTP_EMAIL, SMTP_PASSWORD)
        s.sendmail(SMTP_EMAIL, to_email, msg.as_string())
    return otp


def verify_otp(email: str, code: str) -> bool:
    entry = _otp_store.get(email)
    if not entry:
        return False
    if time.time() > entry["expires"]:
        del _otp_store[email]
        return False
    return entry["otp"] == code.strip()


def ask_openai(prompt: str) -> str:
    payload = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system",
             "content": ("You are a brilliant math assistant inside a neon "
                         "quantum calculator. Solve expressions, explain steps, "
                         "handle unit conversions, statistics, and equations. "
                         "Be concise and precise. Use plain text, no markdown.")},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 500,
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {OPENAI_KEY}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode())
    return data["choices"][0]["message"]["content"].strip()


def safe_eval(expr: str) -> str:
    """Safe math evaluator using only stdlib."""
    allowed = {
        "abs": abs, "round": round, "pow": pow,
        "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
        "tan": math.tan, "log": math.log, "log10": math.log10,
        "log2": math.log2, "exp": math.exp, "pi": math.pi,
        "e": math.e, "ceil": math.ceil, "floor": math.floor,
        "factorial": math.factorial, "radians": math.radians,
        "degrees": math.degrees,
    }
    cleaned = expr.replace("^", "**").replace("×", "*").replace("÷", "/")
    return str(eval(cleaned, {"__builtins__": {}}, allowed))  # noqa: S307


# ═════════════════════════════════════════════════════════════════════════════
#  LOGIN WINDOW
# ═════════════════════════════════════════════════════════════════════════════

class LoginWindow:
    def __init__(self, root: tk.Tk, on_success):
        self.root      = root
        self.on_success = on_success
        self.email_val  = tk.StringVar()
        self.otp_val    = tk.StringVar()
        self.otp_sent   = False
        self._build()

    # ── layout ────────────────────────────────────────────────────────────────
    def _build(self):
        self.root.title("Neon Quantum — Login")
        self.root.configure(bg=C["bg"])
        self.root.geometry("480x600")
        self.root.resizable(False, False)

        # animated scanline canvas (pure tk)
        self.canvas = tk.Canvas(self.root, width=480, height=600,
                                bg=C["bg"], highlightthickness=0)
        self.canvas.place(x=0, y=0)
        self._draw_grid()
        self._scanline_y = 0
        self._animate_scanline()

        # ── card ──────────────────────────────────────────────────────────────
        card = tk.Frame(self.root, bg=C["panel"],
                        highlightbackground=C["neon"], highlightthickness=2,
                        bd=0)
        card.place(relx=0.5, rely=0.5, anchor="center", width=380, height=460)

        # logo
        tk.Label(card, text="⚡", font=("Courier", 40), bg=C["panel"],
                 fg=C["neon"]).pack(pady=(28, 0))
        tk.Label(card, text="N E O N   Q U A N T U M", font=("Courier", 14, "bold"),
                 bg=C["panel"], fg=C["neon"]).pack()
        tk.Label(card, text="CALCULATOR", font=("Courier", 11),
                 bg=C["panel"], fg=C["text_dim"]).pack()

        _sep(card)

        # email
        _lbl(card, "EMAIL ADDRESS")
        self.email_entry = _entry(card, self.email_val)

        # status label
        self.status = tk.Label(card, text="", font=("Courier", 9),
                               bg=C["panel"], fg=C["warn"], wraplength=300)
        self.status.pack(pady=2)

        # send OTP button
        self.btn_send = _btn(card, "SEND OTP  →",
                             lambda: self._thread(self._send_otp),
                             C["btn_op"], C["neon"])
        self.btn_send.pack(pady=(4, 0), ipadx=10, ipady=6)

        _sep(card)

        # OTP
        _lbl(card, "ONE-TIME PASSWORD")
        self.otp_entry = _entry(card, self.otp_val)

        # verify button
        _btn(card, "VERIFY & ENTER  ⚡",
             self._verify,
             C["btn_eq"], C["accent"]).pack(pady=(8, 0), ipadx=10, ipady=8)

        tk.Label(card, text="OTP is valid for 5 minutes",
                 font=("Courier", 8), bg=C["panel"],
                 fg=C["text_dim"]).pack(pady=(4, 0))

    # ── grid background ───────────────────────────────────────────────────────
    def _draw_grid(self):
        for x in range(0, 481, 30):
            self.canvas.create_line(x, 0, x, 600, fill="#001833", width=1)
        for y in range(0, 601, 30):
            self.canvas.create_line(0, y, 480, y, fill="#001833", width=1)

    def _animate_scanline(self):
        self.canvas.delete("scan")
        self.canvas.create_line(0, self._scanline_y, 480, self._scanline_y,
                                fill="#00d4ff", width=1, tags="scan",
                                stipple="gray25")
        self._scanline_y = (self._scanline_y + 3) % 600
        self.root.after(30, self._animate_scanline)

    # ── actions ───────────────────────────────────────────────────────────────
    def _thread(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def _send_otp(self):
        email = self.email_val.get().strip()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self._set_status("⚠ Enter a valid email address", C["danger"])
            return
        self._set_status("Sending OTP…", C["warn"])
        try:
            send_otp_email(email)
            self._set_status(f"✓ OTP sent to {email}", C["accent"])
            self.otp_sent = True
        except Exception as exc:
            self._set_status(f"✗ Email failed: {exc}", C["danger"])

    def _verify(self):
        if not self.otp_sent:
            self._set_status("⚠ Send OTP first", C["warn"])
            return
        email = self.email_val.get().strip()
        code  = self.otp_val.get().strip()
        if verify_otp(email, code):
            self._set_status("✓ Verified!", C["accent"])
            self.root.after(500, self.on_success)
        else:
            self._set_status("✗ Invalid or expired OTP", C["danger"])

    def _set_status(self, msg, color):
        self.root.after(0, lambda: self.status.config(text=msg, fg=color))


# ═════════════════════════════════════════════════════════════════════════════
#  CALCULATOR WINDOW
# ═════════════════════════════════════════════════════════════════════════════

class CalculatorWindow:
    def __init__(self, root: tk.Tk):
        self.root       = root
        self.expr       = ""
        self.history    = []
        self.ai_thread  = None
        self._build()

    # ── main layout ──────────────────────────────────────────────────────────
    def _build(self):
        self.root.title("⚡ Neon Quantum Calculator")
        self.root.configure(bg=C["bg"])
        self.root.geometry("760x700")
        self.root.resizable(False, False)

        # background grid
        bg_canvas = tk.Canvas(self.root, width=760, height=700,
                              bg=C["bg"], highlightthickness=0)
        bg_canvas.place(x=0, y=0)
        for x in range(0, 761, 38):
            bg_canvas.create_line(x, 0, x, 700, fill="#001020", width=1)
        for y in range(0, 701, 38):
            bg_canvas.create_line(0, y, 760, y, fill="#001020", width=1)

        # ── left panel (calculator) ───────────────────────────────────────────
        left = tk.Frame(self.root, bg=C["panel"],
                        highlightbackground=C["neon"], highlightthickness=2)
        left.place(x=10, y=10, width=420, height=680)

        tk.Label(left, text="⚡ QUANTUM CALC", font=("Courier", 13, "bold"),
                 bg=C["panel"], fg=C["neon"]).pack(pady=(10, 4))

        # display
        disp_frame = tk.Frame(left, bg=C["neon_dim"],
                              highlightbackground=C["neon"],
                              highlightthickness=1)
        disp_frame.pack(fill="x", padx=10, pady=4)

        self.expr_var  = tk.StringVar(value="0")
        self.result_var = tk.StringVar(value="")

        tk.Label(disp_frame, textvariable=self.expr_var,
                 font=("Courier", 16), bg=C["entry_bg"],
                 fg=C["text_dim"], anchor="e",
                 wraplength=380).pack(fill="x", padx=6, pady=(6, 0))
        tk.Label(disp_frame, textvariable=self.result_var,
                 font=("Courier", 28, "bold"), bg=C["entry_bg"],
                 fg=C["neon"], anchor="e").pack(fill="x", padx=6, pady=(0, 6))

        # memory / mode row
        mem_row = tk.Frame(left, bg=C["panel"])
        mem_row.pack(fill="x", padx=10, pady=2)
        for label, cmd in [("MC", self._mc), ("MR", self._mr),
                            ("M+", self._mp), ("M-", self._mm)]:
            tk.Button(mem_row, text=label, font=("Courier", 9),
                      bg=C["bg2"], fg=C["text_dim"], activebackground=C["neon_dim"],
                      activeforeground=C["neon"], relief="flat",
                      bd=0, cursor="hand2",
                      command=cmd).pack(side="left", expand=True,
                                        fill="x", padx=2, ipady=4)
        self._memory = 0

        # buttons grid
        btns = tk.Frame(left, bg=C["panel"])
        btns.pack(padx=10, pady=4, fill="both", expand=True)

        layout = [
            [("C",    C["btn_clr"],  C["danger"],  self._clear),
             ("⌫",   C["btn_clr"],  C["warn"],    self._backspace),
             ("%",    C["btn_op"],   C["neon"],    lambda: self._op("%")),
             ("÷",    C["btn_op"],   C["neon"],    lambda: self._op("/"))],

            [("7",    C["btn_num"],  C["text"],    lambda: self._num("7")),
             ("8",    C["btn_num"],  C["text"],    lambda: self._num("8")),
             ("9",    C["btn_num"],  C["text"],    lambda: self._num("9")),
             ("×",    C["btn_op"],   C["neon"],    lambda: self._op("*"))],

            [("4",    C["btn_num"],  C["text"],    lambda: self._num("4")),
             ("5",    C["btn_num"],  C["text"],    lambda: self._num("5")),
             ("6",    C["btn_num"],  C["text"],    lambda: self._num("6")),
             ("−",    C["btn_op"],   C["neon"],    lambda: self._op("-"))],

            [("1",    C["btn_num"],  C["text"],    lambda: self._num("1")),
             ("2",    C["btn_num"],  C["text"],    lambda: self._num("2")),
             ("3",    C["btn_num"],  C["text"],    lambda: self._num("3")),
             ("+",    C["btn_op"],   C["neon"],    lambda: self._op("+"))],

            [("±",    C["btn_num"],  C["text_dim"],self._negate),
             ("0",    C["btn_num"],  C["text"],    lambda: self._num("0")),
             (".",    C["btn_num"],  C["text"],    lambda: self._num(".")),
             ("=",    C["btn_eq"],   C["accent"],  self._equals)],
        ]

        for r, row in enumerate(layout):
            for c, (lbl, bg, fg, cmd) in enumerate(row):
                b = tk.Button(btns, text=lbl, font=("Courier", 18, "bold"),
                              bg=bg, fg=fg, activebackground=C["neon_dim"],
                              activeforeground=C["accent"],
                              relief="flat", bd=0, cursor="hand2",
                              command=cmd)
                b.grid(row=r, column=c, padx=3, pady=3,
                       sticky="nsew", ipady=14)
                b.bind("<Enter>", lambda e, w=b, bg=bg: w.config(
                    bg=C["neon_dim"] if bg != C["btn_eq"] else C["glow"]))
                b.bind("<Leave>", lambda e, w=b, bg=bg: w.config(bg=bg))

            btns.rowconfigure(r, weight=1)
        for c in range(4):
            btns.columnconfigure(c, weight=1)

        # scientific row
        sci = tk.Frame(left, bg=C["panel"])
        sci.pack(padx=10, pady=(0, 6), fill="x")
        sci_btns = [("sin", "sin("), ("cos", "cos("), ("tan", "tan("),
                    ("√",   "sqrt("), ("log", "log10("), ("π",  "pi"),
                    ("e",   "e"),    ("x²",  "**2"),     ("(",  "("),
                    (")",   ")")]
        for i, (lbl, val) in enumerate(sci_btns):
            b = tk.Button(sci, text=lbl, font=("Courier", 9),
                          bg=C["bg2"], fg=C["neon2"],
                          activebackground=C["neon_dim"],
                          activeforeground=C["neon"],
                          relief="flat", bd=0, cursor="hand2",
                          command=lambda v=val: self._insert(v))
            b.grid(row=i // 5, column=i % 5, padx=2, pady=2,
                   sticky="ew", ipady=4)
        for c in range(5):
            sci.columnconfigure(c, weight=1)

        # keyboard bind
        self.root.bind("<Key>", self._key)

        # ── right panel (AI + history) ────────────────────────────────────────
        right = tk.Frame(self.root, bg=C["panel"],
                         highlightbackground=C["accent2"], highlightthickness=2)
        right.place(x=440, y=10, width=310, height=680)

        tk.Label(right, text="🤖 AI ASSISTANT",
                 font=("Courier", 12, "bold"),
                 bg=C["panel"], fg=C["accent"]).pack(pady=(10, 4))

        # AI input
        self.ai_var = tk.StringVar()
        ai_entry = tk.Entry(right, textvariable=self.ai_var,
                            font=("Courier", 11),
                            bg=C["entry_bg"], fg=C["text"],
                            insertbackground=C["neon"],
                            relief="flat",
                            highlightbackground=C["accent2"],
                            highlightthickness=1)
        ai_entry.pack(fill="x", padx=10, pady=4, ipady=8)
        ai_entry.bind("<Return>", lambda e: self._ai_ask())

        _btn(right, "ASK AI  🤖", self._ai_ask,
             C["btn_ai"], C["accent"]).pack(ipady=6, padx=10, fill="x")

        # AI output
        self.ai_out = tk.Text(right, font=("Courier", 10),
                              bg=C["entry_bg"], fg=C["accent"],
                              insertbackground=C["neon"],
                              relief="flat", wrap="word",
                              state="disabled",
                              highlightbackground=C["neon_dim"],
                              highlightthickness=1)
        self.ai_out.pack(fill="both", expand=True, padx=10, pady=6)

        # typing indicator
        self.ai_status = tk.Label(right, text="",
                                  font=("Courier", 8),
                                  bg=C["panel"], fg=C["text_dim"])
        self.ai_status.pack()

        # history
        tk.Label(right, text="── HISTORY ──",
                 font=("Courier", 9),
                 bg=C["panel"], fg=C["text_dim"]).pack(pady=(4, 0))

        self.hist_box = tk.Listbox(right, font=("Courier", 9),
                                   bg=C["bg2"], fg=C["neon2"],
                                   selectbackground=C["neon_dim"],
                                   relief="flat", bd=0, height=8)
        self.hist_box.pack(fill="x", padx=10, pady=(0, 6))
        self.hist_box.bind("<Double-Button-1>", self._recall_history)

    # ── calculator logic ──────────────────────────────────────────────────────
    def _num(self, n):
        if self.expr in ("Error", "0"):
            self.expr = ""
        self.expr += n
        self._refresh()

    def _op(self, op):
        self.expr += op
        self._refresh()

    def _insert(self, val):
        if self.expr in ("Error", "0"):
            self.expr = ""
        self.expr += val
        self._refresh()

    def _backspace(self):
        self.expr = self.expr[:-1] or "0"
        self._refresh()

    def _clear(self):
        self.expr = ""
        self.result_var.set("")
        self._refresh()

    def _negate(self):
        if self.expr and self.expr != "0":
            self.expr = f"-({self.expr})"
        self._refresh()

    def _equals(self):
        try:
            res = safe_eval(self.expr)
            self._add_history(f"{self.expr} = {res}")
            self.result_var.set(res)
            self.expr = res
            self._refresh()
        except Exception:
            self.result_var.set("")
            self.expr = "Error"
            self._refresh()

    def _refresh(self):
        self.expr_var.set(self.expr or "0")

    def _key(self, event):
        k = event.char
        if k in "0123456789.":   self._num(k)
        elif k in "+-*/%":       self._op(k)
        elif k == "(":            self._insert("(")
        elif k == ")":            self._insert(")")
        elif event.keysym == "Return":     self._equals()
        elif event.keysym == "BackSpace":  self._backspace()
        elif event.keysym == "Escape":     self._clear()

    # ── memory ────────────────────────────────────────────────────────────────
    def _mc(self): self._memory = 0
    def _mr(self):
        self.expr = str(self._memory)
        self._refresh()
    def _mp(self):
        try: self._memory += float(safe_eval(self.expr))
        except: pass
    def _mm(self):
        try: self._memory -= float(safe_eval(self.expr))
        except: pass

    # ── history ───────────────────────────────────────────────────────────────
    def _add_history(self, entry):
        self.history.append(entry)
        self.hist_box.insert(0, entry)
        if self.hist_box.size() > 50:
            self.hist_box.delete("end")

    def _recall_history(self, event):
        sel = self.hist_box.curselection()
        if not sel:
            return
        item = self.hist_box.get(sel[0])
        result = item.split("=")[-1].strip()
        self.expr = result
        self._refresh()

    # ── AI feature ───────────────────────────────────────────────────────────
    def _ai_ask(self):
        q = self.ai_var.get().strip()
        if not q:
            q = f"Solve this expression and explain step-by-step: {self.expr}"
        self._set_ai_out("⏳ Thinking…")
        self.ai_status.config(text="Connecting to OpenAI…", fg=C["warn"])
        threading.Thread(target=self._ai_worker, args=(q,), daemon=True).start()

    def _ai_worker(self, prompt):
        try:
            answer = ask_openai(prompt)
            self.root.after(0, lambda: self._set_ai_out(answer))
            self.root.after(0, lambda: self.ai_status.config(
                text="✓ AI responded", fg=C["accent"]))
        except Exception as e:
            self.root.after(0, lambda: self._set_ai_out(f"[Error] {e}"))
            self.root.after(0, lambda: self.ai_status.config(
                text="✗ AI error", fg=C["danger"]))

    def _set_ai_out(self, text):
        self.ai_out.config(state="normal")
        self.ai_out.delete("1.0", "end")
        self.ai_out.insert("end", text)
        self.ai_out.config(state="disabled")


# ═════════════════════════════════════════════════════════════════════════════
#  WIDGET HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _lbl(parent, text):
    tk.Label(parent, text=text, font=("Courier", 9),
             bg=C["panel"], fg=C["text_dim"],
             anchor="w").pack(fill="x", padx=24, pady=(6, 1))

def _entry(parent, var):
    e = tk.Entry(parent, textvariable=var,
                 font=("Courier", 13),
                 bg=C["entry_bg"], fg=C["text"],
                 insertbackground=C["neon"],
                 relief="flat",
                 highlightbackground=C["neon"],
                 highlightthickness=1)
    e.pack(fill="x", padx=24, ipady=8)
    return e

def _btn(parent, text, cmd, bg, fg):
    b = tk.Button(parent, text=text,
                  font=("Courier", 11, "bold"),
                  bg=bg, fg=fg,
                  activebackground=C["neon_dim"],
                  activeforeground=C["accent"],
                  relief="flat", bd=0, cursor="hand2",
                  command=cmd)
    b.bind("<Enter>", lambda e, w=b: w.config(bg=C["neon_dim"]))
    b.bind("<Leave>", lambda e, w=b, c=bg: w.config(bg=c))
    return b

def _sep(parent):
    tk.Frame(parent, height=1, bg=C["neon_dim"]).pack(
        fill="x", padx=20, pady=10)


# ═════════════════════════════════════════════════════════════════════════════
#  APPLICATION ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()
    root.withdraw()

    dlg = tk.Toplevel(root)
    dlg.title("Enter OpenAI API Key")
    dlg.configure(bg=C["bg"])
    dlg.resizable(False, False)
    dlg.grab_set()

    cv = tk.Canvas(dlg, width=460, height=320, bg=C["bg"], highlightthickness=0)
    cv.place(x=0, y=0)
    for x in range(0, 461, 30):
        cv.create_line(x, 0, x, 320, fill="#001833")
    for y in range(0, 321, 30):
        cv.create_line(0, y, 460, y, fill="#001833")

    card = tk.Frame(dlg, bg=C["panel"],
                    highlightbackground=C["neon"], highlightthickness=2)
    card.place(relx=0.5, rely=0.5, anchor="center", width=400, height=260)

    tk.Label(card, text="NEON QUANTUM CALCULATOR",
             font=("Courier", 12, "bold"), bg=C["panel"], fg=C["neon"]).pack(pady=(18, 2))
    tk.Label(card, text="Enter your OpenAI API key to enable AI features",
             font=("Courier", 9), bg=C["panel"], fg=C["text_dim"]).pack()
    tk.Frame(card, height=1, bg=C["neon_dim"]).pack(fill="x", padx=20, pady=10)
    tk.Label(card, text="OPENAI API KEY", font=("Courier", 9),
             bg=C["panel"], fg=C["text_dim"], anchor="w").pack(fill="x", padx=20)

    key_var = tk.StringVar()
    key_entry = tk.Entry(card, textvariable=key_var, font=("Courier", 11),
                         bg=C["entry_bg"], fg=C["accent"],
                         insertbackground=C["neon"], relief="flat",
                         highlightbackground=C["neon"], highlightthickness=1,
                         show="*")
    key_entry.pack(fill="x", padx=20, ipady=8, pady=(2, 4))
    key_entry.focus_set()

    status = tk.Label(card, text="", font=("Courier", 9), bg=C["panel"], fg=C["warn"])
    status.pack()

    def show_hide():
        key_entry.config(show="" if key_entry.cget("show") == "*" else "*")

    tk.Button(card, text="Show / Hide Key", font=("Courier", 8),
              bg=C["bg2"], fg=C["text_dim"], relief="flat", bd=0,
              cursor="hand2", command=show_hide).pack(pady=(0, 4))

    def launch():
        global OPENAI_KEY
        k = key_var.get().strip()
        if k.startswith("sk-") and len(k) > 20:
            OPENAI_KEY = k
        elif k != "":
            status.config(text="Key should start with sk-   (close to skip AI)", fg=C["warn"])
            return
        dlg.destroy()
        root.deiconify()
        CalculatorWindow(root)
        _center(root, 760, 700)

    _btn(card, "LAUNCH CALCULATOR", launch, C["btn_eq"], C["accent"]).pack(
        pady=(2, 0), ipadx=10, ipady=7)
    tk.Label(card, text="Leave blank + press Enter to skip (AI disabled)",
             font=("Courier", 8), bg=C["panel"], fg=C["text_dim"]).pack(pady=(3, 0))

    dlg.bind("<Return>", lambda e: launch())
    dlg.protocol("WM_DELETE_WINDOW", launch)
    _center(dlg, 460, 320)
    root.mainloop()


def _center(win, w, h):
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x  = (sw - w) // 2
    y  = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


if __name__ == "__main__":
    main()