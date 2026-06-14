"""
SysOptimizer v4
- Performance tab: per-core CPU graphs, memory composition, network I/O, disk I/O
- Processes tab: full sortable/filterable process table  (columns centered)
- Optimizer tab: bloat disabler, startup manager, RAM flush, power plans
- Light/Dark mode toggle — no CTK mode switch (no flash/glitch)
- Zoom (Ctrl +/−/0, Ctrl+scroll)
"""

import customtkinter as ctk
import psutil
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import platform
import subprocess
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# THEME
# ═══════════════════════════════════════════════════════════════════════════════

DARK = {
    "bg_deep":        "#090D18",
    "bg_card":        "#101622",
    "bg_row":         "#182030",
    "bg_row2":        "#131B28",
    "bg_graph":       "#0C1220",
    "fg_main":        "#E4EAF4",
    "fg_dim":         "#6E7E9E",
    "fg_bright":      "#FFFFFF",
    "accent":         "#00C8F0",
    "accent2":        "#FF6B35",
    "accent3":        "#3DDB50",
    "accent4":        "#A855F7",
    "danger":         "#FF3B5C",
    "warn":           "#FFB300",
    "ring_track":     "#1A2840",
    "spark_cpu_fill": "#003A4A",
    "spark_ram_fill": "#451E00",
    "sel":            "#00506A",
    "border":         "#1A7A96",
    "safe_fg":        "#394A60",
    "high_fg":        "#FFB300",
    "toggle_bg":      "#182030",
    "sep":            "#1C2A3E",
    "mem_in_use":     "#4A90D9",
    "mem_modified":   "#FF8C42",
    "mem_standby":    "#3A5A7A",
    "mem_free":       "#1A2840",
    "net_send":       "#3DDB50",
    "net_recv":       "#00C8F0",
    "disk_read":      "#A855F7",
    "disk_write":     "#FF6B35",
}

LIGHT = {
    "bg_deep":        "#DDE3ED",
    "bg_card":        "#F4F7FC",
    "bg_row":         "#E2EAF5",
    "bg_row2":        "#EDF2FA",
    "bg_graph":       "#EBF1FA",
    "fg_main":        "#0F1E35",
    "fg_dim":         "#4A5A78",
    "fg_bright":      "#000000",
    "accent":         "#006FA8",
    "accent2":        "#C04800",
    "accent3":        "#1A7A2A",
    "accent4":        "#6D28C8",
    "danger":         "#CC1A36",
    "warn":           "#885500",
    "ring_track":     "#B8CCDE",
    "spark_cpu_fill": "#C8E4F0",
    "spark_ram_fill": "#FFD0B0",
    "sel":            "#90CCE8",
    "border":         "#0080B0",
    "safe_fg":        "#8098B0",
    "high_fg":        "#885500",
    "toggle_bg":      "#CDD8E8",
    "sep":            "#C0CEDF",
    "mem_in_use":     "#2060A8",
    "mem_modified":   "#C04800",
    "mem_standby":    "#4070A0",
    "mem_free":       "#B0C4D8",
    "net_send":       "#1A7A2A",
    "net_recv":       "#006FA8",
    "disk_read":      "#6D28C8",
    "disk_write":     "#C04800",
}

T = dict(DARK)

# ═══════════════════════════════════════════════════════════════════════════════
# SAFE PROCESS LIST
# ═══════════════════════════════════════════════════════════════════════════════

SAFE_PROCESSES = {
    "system", "system idle process", "registry", "smss.exe", "csrss.exe",
    "wininit.exe", "winlogon.exe", "lsass.exe", "lsaiso.exe", "services.exe",
    "svchost.exe", "dwm.exe", "explorer.exe", "taskhostw.exe", "sihost.exe",
    "fontdrvhost.exe", "audiodg.exe", "ctfmon.exe", "dllhost.exe",
    "runtimebroker.exe", "startmenuexperiencehost.exe", "searchhost.exe",
    "searchindexer.exe", "spoolsv.exe", "wuauclt.exe", "msiexec.exe",
    "antimalware service executable", "msmpeng.exe", "securityhealthservice.exe",
    "python.exe", "python3.exe", "optimizer.exe", "sysoptimizer.exe",
}

# ═══════════════════════════════════════════════════════════════════════════════
# ZOOM
# ═══════════════════════════════════════════════════════════════════════════════

ZOOM_LEVELS  = [9, 10, 11, 12, 13, 14, 15, 16, 18, 20]
DEFAULT_ZOOM = 4
_zoom_idx    = DEFAULT_ZOOM

def zf(base=13):
    return max(8, int(base * ZOOM_LEVELS[_zoom_idx] / 13))

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def bytes_to_human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"

def bps_to_human(n):
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} GB/s"

def color_for_pct(pct):
    if pct < 50: return T["accent3"]
    if pct < 75: return T["warn"]
    return T["danger"]

def run_ps(cmd, capture=True):
    """Run a PowerShell command silently (no console window). Returns (returncode, stdout)."""
    try:
        # CREATE_NO_WINDOW (0x08000000) suppresses the console popup on Windows
        CREATE_NO_WINDOW = 0x08000000
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-WindowStyle", "Hidden",
             "-ExecutionPolicy", "Bypass", "-Command", cmd],
            capture_output=capture, text=True, timeout=15,
            creationflags=CREATE_NO_WINDOW
        )
        return r.returncode, (r.stdout or "").strip()
    except Exception as e:
        return -1, str(e)

def get_processes():
    procs = []
    for p in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_info", "status", "username"]):
        try:
            info = p.info
            mem = info["memory_info"].rss if info["memory_info"] else 0
            procs.append({
                "pid":    info["pid"],
                "name":   info["name"] or "Unknown",
                "cpu":    info["cpu_percent"] or 0.0,
                "mem":    mem,
                "status": info["status"] or "",
                "user":   (info["username"] or "").split("\\")[-1],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return procs

# ═══════════════════════════════════════════════════════════════════════════════
# GRAPH CANVAS  (reusable scrolling line chart)
# ═══════════════════════════════════════════════════════════════════════════════

class GraphCanvas(tk.Canvas):
    def __init__(self, parent, series: list, history=60,
                 show_grid=True, y_label="", **kw):
        super().__init__(parent, bg=T["bg_graph"], highlightthickness=0, **kw)
        self.series    = series
        self.history   = history
        self.show_grid = show_grid
        self.y_label   = y_label
        self.data      = {s["key"]: [0.0] * history for s in series}
        self.bind("<Configure>", lambda e: self._draw())

    def push(self, key, value):
        self.data[key].append(max(0.0, value))
        if len(self.data[key]) > self.history:
            self.data[key].pop(0)
        self._draw()

    def push_multi(self, updates: dict):
        for key, val in updates.items():
            self.data[key].append(max(0.0, val))
            if len(self.data[key]) > self.history:
                self.data[key].pop(0)
        self._draw()

    def repaint(self):
        self.configure(bg=T["bg_graph"])
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        if self.show_grid:
            for i in range(1, 4):
                y = h * i // 4
                self.create_line(0, y, w, y, fill=T["sep"], width=1)
            for i in range(1, 6):
                x = w * i // 6
                self.create_line(x, 0, x, h, fill=T["sep"], width=1)
        if self.y_label:
            self.create_text(4, 4, text="100%", anchor="nw",
                             fill=T["fg_dim"], font=("Consolas", 7))
            self.create_text(4, h // 2, text=" 50%", anchor="w",
                             fill=T["fg_dim"], font=("Consolas", 7))
        for s in self.series:
            key      = s["key"]
            col      = T[key]
            fill_col = T.get(s.get("fill_key", ""), T["bg_graph"])
            vals = self.data[key]
            n = len(vals)
            if n < 2:
                continue
            max_val = max(max(vals), 1.0)
            if s.get("pct", True):
                max_val = 100.0
            xs = [i / (n - 1) * w for i in range(n)]
            ys = [h - (v / max_val) * h * 0.94 - 2 for v in vals]
            pts = []
            for x, y in zip(xs, ys):
                pts += [x, y]
            self.create_polygon([0, h] + pts + [w, h],
                                fill=fill_col, outline="")
            self.create_line(pts, fill=col, width=1.8, smooth=True)
        self.create_rectangle(0, 0, w - 1, h - 1,
                               outline=T["sep"], width=1)


# ═══════════════════════════════════════════════════════════════════════════════
# RING METER
# ═══════════════════════════════════════════════════════════════════════════════

class RingMeter(tk.Canvas):
    def __init__(self, parent, label, size=128, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=T["bg_card"], highlightthickness=0, **kw)
        self.size   = size
        self.label  = label
        self._pct   = 0.0
        self._target= 0.0
        self._draw()

    def set_value(self, pct):
        self._target = max(0.0, min(100.0, pct))
        self._animate()

    def _animate(self):
        diff = self._target - self._pct
        if abs(diff) > 0.4:
            self._pct += diff * 0.20
            self._draw()
            self.after(16, self._animate)
        else:
            self._pct = self._target
            self._draw()

    def repaint(self):
        self.configure(bg=T["bg_card"])
        self._draw()

    def _draw(self):
        self.delete("all")
        s, p = self.size, self._pct
        pad = 14
        x0, y0, x1, y1 = pad, pad, s - pad, s - pad
        self.create_arc(x0, y0, x1, y1, start=90, extent=360,
                        outline=T["ring_track"], width=12, style="arc")
        col   = color_for_pct(p)
        angle = -p / 100 * 360
        if abs(angle) > 1:
            self.create_arc(x0, y0, x1, y1, start=90, extent=angle,
                            outline=col, width=12, style="arc")
            self.create_arc(x0+3, y0+3, x1-3, y1-3, start=90, extent=angle,
                            outline=col, width=4, style="arc")
        cx, cy = s // 2, s // 2
        self.create_text(cx, cy - 10, text=f"{p:.0f}%",
                         fill=T["fg_main"], font=("Consolas", zf(17), "bold"))
        self.create_text(cx, cy + 12, text=self.label,
                         fill=T["fg_dim"],  font=("Consolas", zf(9)))


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY COMPOSITION BAR
# ═══════════════════════════════════════════════════════════════════════════════

class MemCompositionBar(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, height=28, bg=T["bg_card"],
                         highlightthickness=0, **kw)
        self._segments = []
        self.bind("<Configure>", lambda e: self._draw())

    def set_segments(self, segments):
        self._segments = segments
        self._draw()

    def repaint(self):
        self.configure(bg=T["bg_card"])
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        x = 0
        for frac, ckey in self._segments:
            bw = int(frac * w)
            if bw > 0:
                self.create_rectangle(x, 2, x + bw, h - 2,
                                      fill=T[ckey], outline="")
                x += bw
        self.create_rectangle(0, 0, w - 1, h - 1,
                               outline=T["sep"], width=1)


# ═══════════════════════════════════════════════════════════════════════════════
# MINI CPU CORE GRAPH
# ═══════════════════════════════════════════════════════════════════════════════

class CoreGraph(tk.Canvas):
    HISTORY = 30

    def __init__(self, parent, core_idx, **kw):
        super().__init__(parent, bg=T["bg_graph"], highlightthickness=0, **kw)
        self.core_idx = core_idx
        self._data    = [0.0] * self.HISTORY
        self._lbl     = f"C{core_idx}"
        self.bind("<Configure>", lambda e: self._draw())

    def push(self, val):
        self._data.append(max(0.0, min(100.0, val)))
        if len(self._data) > self.HISTORY:
            self._data.pop(0)
        self._draw()

    def repaint(self):
        self.configure(bg=T["bg_graph"])
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        d = self._data
        n = len(d)
        if n < 2:
            return
        col      = color_for_pct(d[-1])
        fill_col = T["spark_cpu_fill"]
        xs = [i / (n - 1) * w for i in range(n)]
        ys = [h - (v / 100) * h * 0.92 - 1 for v in d]
        pts = []
        for x, y in zip(xs, ys):
            pts += [x, y]
        self.create_polygon([0, h] + pts + [w, h], fill=fill_col, outline="")
        self.create_line(pts, fill=col, width=1.5, smooth=True)
        self.create_text(3, h - 3, text=self._lbl,
                         anchor="sw", fill=T["fg_dim"], font=("Consolas", 7))
        self.create_text(w - 3, 3, text=f"{d[-1]:.0f}%",
                         anchor="ne", fill=T["fg_bright"], font=("Consolas", 7, "bold"))
        self.create_rectangle(0, 0, w - 1, h - 1, outline=T["sep"], width=1)


# ═══════════════════════════════════════════════════════════════════════════════
# PROCESS TABLE
# ═══════════════════════════════════════════════════════════════════════════════

class ProcessTable(ctk.CTkFrame):
    COLS     = ("PID", "Name", "CPU %", "Memory", "Status", "User")
    COL_W    = [64, 230, 78, 100, 88, 140]
    # "Name" stays left; all others centered
    COL_ANCHOR = {"PID": "center", "Name": "w", "CPU %": "center",
                  "Memory": "center", "Status": "center", "User": "center"}
    STYLE_NM = "Proc.Treeview"

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=T["bg_card"], corner_radius=12, **kw)
        self._sort_col     = "CPU %"
        self._sort_asc     = False
        self._procs        = []
        self._selected_pid = None
        self._build_ui()

    def _build_ui(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(12, 6))

        self._title_lbl = ctk.CTkLabel(hdr, text="RUNNING PROCESSES",
                     font=("Consolas", zf(11), "bold"), text_color=T["fg_dim"])
        self._title_lbl.pack(side="left")

        self._filter_var = ctk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())
        self._search = ctk.CTkEntry(hdr, textvariable=self._filter_var,
                              placeholder_text="Filter by name…",
                              width=200, height=30,
                              fg_color=T["bg_row"], border_color=T["border"],
                              font=("Consolas", zf(11)))
        self._search.pack(side="right")

        tree_frame = tk.Frame(self, bg=T["bg_card"])
        tree_frame.pack(fill="both", expand=True, padx=14, pady=(0, 4))

        self._style = ttk.Style()
        self._apply_tree_style()

        self.tree = ttk.Treeview(tree_frame, columns=self.COLS,
                                 show="headings", style=self.STYLE_NM,
                                 selectmode="browse")
        for col, w in zip(self.COLS, self.COL_W):
            self.tree.heading(col, text=col,
                              command=lambda c=col: self._sort_by(c))
            anchor = self.COL_ANCHOR.get(col, "center")
            self.tree.column(col, width=w, minwidth=40, anchor=anchor)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        act = ctk.CTkFrame(self, fg_color="transparent")
        act.pack(fill="x", padx=14, pady=(4, 12))

        self._lbl_sel = ctk.CTkLabel(act, text="No process selected",
                                     font=("Consolas", zf(10)), text_color=T["fg_dim"])
        self._lbl_sel.pack(side="left")

        self._btn_kill = ctk.CTkButton(act, text="⚡  Kill Selected",
                      width=140, height=34,
                      fg_color=T["danger"], hover_color="#CC1A36",
                      font=("Consolas", zf(11), "bold"),
                      command=self._kill_selected)
        self._btn_kill.pack(side="right", padx=4)

        self._btn_ref = ctk.CTkButton(act, text="↺  Refresh",
                      width=100, height=34,
                      fg_color=T["bg_row"], hover_color=T["bg_row2"],
                      font=("Consolas", zf(11)),
                      command=self.refresh)
        self._btn_ref.pack(side="right", padx=4)

    def _apply_tree_style(self):
        rh = max(22, int(zf(13) * 2.0))
        self._style.theme_use("default")
        self._style.configure(self.STYLE_NM,
            background=T["bg_row2"], foreground=T["fg_main"],
            fieldbackground=T["bg_row2"],
            rowheight=rh, font=("Segoe UI", zf(11)))
        self._style.configure(f"{self.STYLE_NM}.Heading",
            background=T["bg_row"], foreground=T["accent"],
            font=("Segoe UI", zf(11), "bold"), relief="flat")
        self._style.map(self.STYLE_NM,
            background=[("selected", T["sel"])],
            foreground=[("selected", T["fg_main"])])

    def repaint(self):
        self.configure(fg_color=T["bg_card"])
        self._apply_tree_style()
        self.tree.master.configure(bg=T["bg_card"])
        self._title_lbl.configure(text_color=T["fg_dim"],
                                  font=("Consolas", zf(11), "bold"))
        self._search.configure(fg_color=T["bg_row"], border_color=T["border"],
                               font=("Consolas", zf(11)))
        self._lbl_sel.configure(text_color=T["fg_dim"], font=("Consolas", zf(10)))
        self._btn_kill.configure(fg_color=T["danger"],
                                 font=("Consolas", zf(11), "bold"))
        self._btn_ref.configure(fg_color=T["bg_row"], hover_color=T["bg_row2"],
                                font=("Consolas", zf(11)))
        self._render(self._procs)

    def update_data(self, procs):
        self._procs = procs
        self._apply_filter()

    def _apply_filter(self):
        q = self._filter_var.get().lower()
        filtered = [p for p in self._procs
                    if q in p["name"].lower()] if q else self._procs
        self._render(filtered)

    def _sort_by(self, col):
        self._sort_asc = (not self._sort_asc) if self._sort_col == col else False
        self._sort_col = col
        self._apply_filter()

    def _render(self, procs):
        key_map = {
            "PID":    lambda p: p["pid"],
            "Name":   lambda p: p["name"].lower(),
            "CPU %":  lambda p: p["cpu"],
            "Memory": lambda p: p["mem"],
            "Status": lambda p: p["status"],
            "User":   lambda p: p["user"],
        }
        procs = sorted(procs,
                       key=key_map.get(self._sort_col, lambda p: p["cpu"]),
                       reverse=not self._sort_asc)
        sel = self._selected_pid
        self.tree.delete(*self.tree.get_children())
        for p in procs:
            safe = p["name"].lower() in SAFE_PROCESSES
            tag  = "safe" if safe else ("high" if p["cpu"] > 15 else "")
            self.tree.insert("", "end", iid=str(p["pid"]), tags=(tag,),
                             values=(p["pid"], p["name"],
                                     f'{p["cpu"]:.1f}',
                                     bytes_to_human(p["mem"]),
                                     p["status"], p["user"]))
        self.tree.tag_configure("safe", foreground=T["safe_fg"])
        self.tree.tag_configure("high", foreground=T["high_fg"])
        if sel and self.tree.exists(str(sel)):
            self.tree.selection_set(str(sel))

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if sel:
            self._selected_pid = int(sel[0])
            vals = self.tree.item(sel[0], "values")
            self._lbl_sel.configure(text=f"● [{vals[0]}]  {vals[1]}")
        else:
            self._selected_pid = None
            self._lbl_sel.configure(text="No process selected")

    def _kill_selected(self):
        if not self._selected_pid:
            messagebox.showwarning("SysOptimizer", "Select a process first.")
            return
        try:
            p = psutil.Process(self._selected_pid)
            if p.name().lower() in SAFE_PROCESSES:
                messagebox.showerror("Protected",
                    f'"{p.name()}" is a system process and cannot be killed.')
                return
            if not messagebox.askyesno("Confirm Kill",
                    f'Kill [{self._selected_pid}] {p.name()}?\n\n'
                    f'Unsaved data in that process will be lost.'):
                return
            p.kill()
            self._selected_pid = None
            self._lbl_sel.configure(text="✓ Process terminated.")
            self.refresh()
        except psutil.NoSuchProcess:
            messagebox.showinfo("SysOptimizer", "Process already ended.")
            self.refresh()
        except psutil.AccessDenied:
            messagebox.showerror("Access Denied",
                "Cannot kill — run as Administrator.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh(self):
        threading.Thread(target=self._bg_refresh, daemon=True).start()

    def _bg_refresh(self):
        procs = get_processes()
        self.after(0, lambda: self.update_data(procs))


# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE TAB
# ═══════════════════════════════════════════════════════════════════════════════

class PerformanceTab(ctk.CTkFrame):
    GRAPH_H   = 130
    CORE_H    = 68
    NET_HIST  = 60

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._num_cores = psutil.cpu_count(logical=True) or 1
        self._net_prev  = None
        self._disk_prev = None
        self._net_max   = 1.0
        self._disk_max  = 1.0
        self._build_ui()

    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=T["bg_card"],
                            corner_radius=10, **kw)

    def _build_ui(self):
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)
        self._build_cpu_section()
        self._build_memory_section()
        self._build_net_disk_section()

    def _build_cpu_section(self):
        card = self._card(self._scroll)
        card.pack(fill="x", padx=6, pady=(6, 4))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 0))
        self._lbl_cpu_hdr = ctk.CTkLabel(hdr, text="CPU",
                   font=("Consolas", zf(12), "bold"), text_color=T["accent"])
        self._lbl_cpu_hdr.pack(side="left")
        self._lbl_cpu_val = ctk.CTkLabel(hdr, text="0%  ·  0.00 GHz",
                   font=("Consolas", zf(11)), text_color=T["fg_main"])
        self._lbl_cpu_val.pack(side="left", padx=14)
        self._lbl_cpu_info = ctk.CTkLabel(hdr, text="",
                   font=("Consolas", zf(9)), text_color=T["fg_dim"])
        self._lbl_cpu_info.pack(side="right", padx=4)

        self._cpu_big = GraphCanvas(card,
                                    series=[{"key": "accent",
                                             "fill_key": "spark_cpu_fill",
                                             "pct": True}],
                                    history=60, show_grid=True, y_label="%")
        self._cpu_big.pack(fill="x", padx=14, pady=(4, 8),
                           ipady=self.GRAPH_H // 2)

        cores_lbl = ctk.CTkLabel(card, text="PER-CORE",
                   font=("Consolas", zf(9), "bold"), text_color=T["fg_dim"])
        cores_lbl.pack(anchor="w", padx=14)

        self._core_grid = ctk.CTkFrame(card, fg_color="transparent")
        self._core_grid.pack(fill="x", padx=14, pady=(2, 12))
        self._core_graphs = []
        cols = min(8, max(4, self._num_cores // 2))
        for i in range(self._num_cores):
            cg = CoreGraph(self._core_grid, i, width=68, height=self.CORE_H)
            row_i = i // cols
            col_i = i % cols
            cg.grid(row=row_i, column=col_i, padx=2, pady=2, sticky="nsew")
            self._core_grid.columnconfigure(col_i, weight=1)
            self._core_graphs.append(cg)

        self._cpu_card = card
        self._cores_lbl = cores_lbl

    def _build_memory_section(self):
        card = self._card(self._scroll)
        card.pack(fill="x", padx=6, pady=4)

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 0))
        self._lbl_mem_hdr = ctk.CTkLabel(hdr, text="MEMORY",
                   font=("Consolas", zf(12), "bold"), text_color=T["accent2"])
        self._lbl_mem_hdr.pack(side="left")
        self._lbl_mem_val = ctk.CTkLabel(hdr, text="",
                   font=("Consolas", zf(11)), text_color=T["fg_main"])
        self._lbl_mem_val.pack(side="left", padx=14)
        self._lbl_mem_total = ctk.CTkLabel(hdr, text="",
                   font=("Consolas", zf(9)), text_color=T["fg_dim"])
        self._lbl_mem_total.pack(side="right", padx=4)

        self._mem_graph = GraphCanvas(card,
                                      series=[{"key": "accent2",
                                               "fill_key": "spark_ram_fill",
                                               "pct": True}],
                                      history=60, show_grid=True, y_label="%")
        self._mem_graph.pack(fill="x", padx=14, pady=(4, 6),
                             ipady=self.GRAPH_H // 2)

        bar_lbl = ctk.CTkLabel(card, text="COMPOSITION  (In use · Modified · Standby · Free)",
                   font=("Consolas", zf(8)), text_color=T["fg_dim"])
        bar_lbl.pack(anchor="w", padx=14)
        self._mem_comp_bar = MemCompositionBar(card)
        self._mem_comp_bar.pack(fill="x", padx=14, pady=(2, 4))

        legend = ctk.CTkFrame(card, fg_color="transparent")
        legend.pack(fill="x", padx=14, pady=(0, 4))
        self._mem_legend_labels = {}
        keys = [("mem_in_use", "In use"), ("mem_modified", "Modified"),
                ("mem_standby", "Standby"), ("mem_free", "Free")]
        for ck, nm in keys:
            dot = tk.Canvas(legend, width=10, height=10,
                            bg=T["bg_card"], highlightthickness=0)
            dot.create_rectangle(1, 1, 9, 9, fill=T[ck], outline="")
            dot.pack(side="left", padx=(0, 2))
            lbl = ctk.CTkLabel(legend, text=nm + " –",
                               font=("Consolas", zf(9)), text_color=T["fg_dim"])
            lbl.pack(side="left", padx=(0, 10))
            self._mem_legend_labels[ck] = (dot, lbl)

        stats_row = ctk.CTkFrame(card, fg_color="transparent")
        stats_row.pack(fill="x", padx=14, pady=(4, 12))
        self._mem_stats = {}
        for key in ("In use", "Available", "Committed", "Cached",
                    "Speed", "Slots", "Form factor"):
            col_f = ctk.CTkFrame(stats_row, fg_color="transparent")
            col_f.pack(side="left", padx=14)
            ctk.CTkLabel(col_f, text=key,
                         font=("Consolas", zf(8)), text_color=T["fg_dim"]).pack(anchor="w")
            vl = ctk.CTkLabel(col_f, text="–",
                              font=("Consolas", zf(11), "bold"), text_color=T["fg_main"])
            vl.pack(anchor="w")
            self._mem_stats[key] = vl

        self._mem_card = card
        self._bar_lbl = bar_lbl

    def _build_net_disk_section(self):
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=4)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        net_card = self._card(row)
        net_card.grid(row=0, column=0, padx=(0, 4), sticky="nsew")

        net_hdr = ctk.CTkFrame(net_card, fg_color="transparent")
        net_hdr.pack(fill="x", padx=14, pady=(10, 0))
        self._lbl_net_hdr = ctk.CTkLabel(net_hdr, text="NETWORK",
                   font=("Consolas", zf(12), "bold"), text_color=T["net_send"])
        self._lbl_net_hdr.pack(side="left")
        self._lbl_net_iface = ctk.CTkLabel(net_hdr, text="",
                   font=("Consolas", zf(9)), text_color=T["fg_dim"])
        self._lbl_net_iface.pack(side="right", padx=4)

        self._net_graph = GraphCanvas(net_card,
            series=[
                {"key": "net_send", "fill_key": "spark_cpu_fill",
                 "label": "Send", "pct": False},
                {"key": "net_recv", "fill_key": "spark_ram_fill",
                 "label": "Recv", "pct": False},
            ],
            history=self.NET_HIST, show_grid=True, y_label="")
        self._net_graph.pack(fill="x", padx=14, pady=(4, 6),
                             ipady=self.GRAPH_H // 2)

        net_stats = ctk.CTkFrame(net_card, fg_color="transparent")
        net_stats.pack(fill="x", padx=14, pady=(0, 12))
        self._net_stats = {}
        for k, col in [("Send", "net_send"), ("Recv", "net_recv"),
                       ("Total Sent", "fg_dim"), ("Total Recv", "fg_dim")]:
            cf = ctk.CTkFrame(net_stats, fg_color="transparent")
            cf.pack(side="left", padx=12)
            ctk.CTkLabel(cf, text=k, font=("Consolas", zf(8)),
                         text_color=T[col]).pack(anchor="w")
            vl = ctk.CTkLabel(cf, text="–",
                              font=("Consolas", zf(10), "bold"),
                              text_color=T["fg_main"])
            vl.pack(anchor="w")
            self._net_stats[k] = (vl, col)

        disk_card = self._card(row)
        disk_card.grid(row=0, column=1, padx=(4, 0), sticky="nsew")

        disk_hdr = ctk.CTkFrame(disk_card, fg_color="transparent")
        disk_hdr.pack(fill="x", padx=14, pady=(10, 0))
        self._lbl_disk_hdr = ctk.CTkLabel(disk_hdr, text="DISK",
                   font=("Consolas", zf(12), "bold"), text_color=T["disk_read"])
        self._lbl_disk_hdr.pack(side="left")
        self._lbl_disk_info = ctk.CTkLabel(disk_hdr, text="",
                   font=("Consolas", zf(9)), text_color=T["fg_dim"])
        self._lbl_disk_info.pack(side="right", padx=4)

        self._disk_graph = GraphCanvas(disk_card,
            series=[
                {"key": "disk_read",  "fill_key": "spark_cpu_fill",
                 "label": "Read",  "pct": False},
                {"key": "disk_write", "fill_key": "spark_ram_fill",
                 "label": "Write", "pct": False},
            ],
            history=self.NET_HIST, show_grid=True, y_label="")
        self._disk_graph.pack(fill="x", padx=14, pady=(4, 6),
                              ipady=self.GRAPH_H // 2)

        disk_stats = ctk.CTkFrame(disk_card, fg_color="transparent")
        disk_stats.pack(fill="x", padx=14, pady=(0, 12))
        self._disk_stats = {}
        for k, col in [("Read", "disk_read"), ("Write", "disk_write"),
                       ("Active time", "fg_dim"), ("Avg resp", "fg_dim")]:
            cf = ctk.CTkFrame(disk_stats, fg_color="transparent")
            cf.pack(side="left", padx=12)
            ctk.CTkLabel(cf, text=k, font=("Consolas", zf(8)),
                         text_color=T[col]).pack(anchor="w")
            vl = ctk.CTkLabel(cf, text="–",
                              font=("Consolas", zf(10), "bold"),
                              text_color=T["fg_main"])
            vl.pack(anchor="w")
            self._disk_stats[k] = (vl, col)

        self._net_card  = net_card
        self._disk_card = disk_card

    # ── Update methods ────────────────────────────────────────────────────────

    def update_cpu(self, cpu_total, per_core, freq):
        self._cpu_big.push("accent", cpu_total)
        freq_str = f"{freq.current/1000:.2f} GHz  ·  max {freq.max/1000:.2f} GHz" if freq else "N/A"
        self._lbl_cpu_val.configure(
            text=f"{cpu_total:.1f}%  ·  {freq_str if freq else 'N/A'}")
        cores_t = psutil.cpu_count(logical=True) or 1
        cores_p = psutil.cpu_count(logical=False) or 1
        self._lbl_cpu_info.configure(
            text=f"{cores_p} cores  {cores_t} logical  ·  {platform.processor()[:40]}")
        for i, (cg, v) in enumerate(zip(self._core_graphs, per_core)):
            cg.push(v)

    def update_memory(self, ram, swap):
        total = ram.total or 1
        in_use_f   = max(0.0, min(1.0, ram.used / total))
        standby_f  = getattr(ram, "cached", 0) / total
        free_f     = ram.available / total
        modified_f = max(0.0, 1.0 - in_use_f - standby_f - free_f)

        self._mem_graph.push("accent2", ram.percent)
        self._mem_comp_bar.set_segments([
            (in_use_f,   "mem_in_use"),
            (modified_f, "mem_modified"),
            (standby_f,  "mem_standby"),
            (free_f,     "mem_free"),
        ])
        self._lbl_mem_val.configure(
            text=f"{bytes_to_human(ram.used)} / {bytes_to_human(ram.total)}"
                 f"  ({ram.percent:.0f}%)")
        self._lbl_mem_total.configure(
            text=f"Swap: {bytes_to_human(swap.used)} / {bytes_to_human(swap.total)}")

        self._mem_stats["In use"].configure(text=bytes_to_human(ram.used))
        self._mem_stats["Available"].configure(text=bytes_to_human(ram.available))
        self._mem_stats["Committed"].configure(
            text=f"{bytes_to_human(ram.used)}/{bytes_to_human(ram.total)}")
        self._mem_stats["Cached"].configure(
            text=bytes_to_human(getattr(ram, "cached", 0)))
        self._mem_stats["Speed"].configure(text="–")
        self._mem_stats["Slots"].configure(text="–")
        self._mem_stats["Form factor"].configure(text="–")

        for ck, (dot, lbl) in self._mem_legend_labels.items():
            dot.configure(bg=T["bg_card"])
            dot.delete("all")
            dot.create_rectangle(1, 1, 9, 9, fill=T[ck], outline="")

    def update_network(self, counters):
        now = (counters.bytes_sent, counters.bytes_recv)
        if self._net_prev is not None:
            sent_rate = max(0, now[0] - self._net_prev[0]) / 2.0
            recv_rate = max(0, now[1] - self._net_prev[1]) / 2.0
            self._net_graph.push_multi({
                "net_send": sent_rate,
                "net_recv": recv_rate,
            })
            self._net_stats["Send"][0].configure(text=bps_to_human(sent_rate))
            self._net_stats["Recv"][0].configure(text=bps_to_human(recv_rate))
        self._net_stats["Total Sent"][0].configure(
            text=bytes_to_human(counters.bytes_sent))
        self._net_stats["Total Recv"][0].configure(
            text=bytes_to_human(counters.bytes_recv))
        self._net_prev = now

    def update_disk(self, disk_io):
        now = (disk_io.read_bytes, disk_io.write_bytes)
        if self._disk_prev is not None:
            read_rate  = max(0, now[0] - self._disk_prev[0]) / 2.0
            write_rate = max(0, now[1] - self._disk_prev[1]) / 2.0
            self._disk_graph.push_multi({
                "disk_read":  read_rate,
                "disk_write": write_rate,
            })
            self._disk_stats["Read"][0].configure(text=bps_to_human(read_rate))
            self._disk_stats["Write"][0].configure(text=bps_to_human(write_rate))
        self._disk_stats["Active time"][0].configure(text="–")
        self._disk_stats["Avg resp"][0].configure(text="–")
        self._disk_prev = now

    def repaint(self):
        for w in (self._cpu_card, self._mem_card,
                  self._net_card, self._disk_card):
            w.configure(fg_color=T["bg_card"])

        self._lbl_cpu_hdr.configure(text_color=T["accent"],
                                     font=("Consolas", zf(12), "bold"))
        self._lbl_cpu_val.configure(text_color=T["fg_main"],
                                     font=("Consolas", zf(11)))
        self._lbl_cpu_info.configure(text_color=T["fg_dim"],
                                      font=("Consolas", zf(9)))
        self._lbl_mem_hdr.configure(text_color=T["accent2"],
                                     font=("Consolas", zf(12), "bold"))
        self._lbl_mem_val.configure(text_color=T["fg_main"],
                                     font=("Consolas", zf(11)))
        self._lbl_mem_total.configure(text_color=T["fg_dim"],
                                       font=("Consolas", zf(9)))
        self._lbl_net_hdr.configure(text_color=T["net_send"],
                                     font=("Consolas", zf(12), "bold"))
        self._lbl_disk_hdr.configure(text_color=T["disk_read"],
                                      font=("Consolas", zf(12), "bold"))

        for g in (self._cpu_big, self._mem_graph,
                  self._net_graph, self._disk_graph):
            g.repaint()
        for cg in self._core_graphs:
            cg.repaint()
        self._mem_comp_bar.repaint()

        for stats in (self._mem_stats,):
            for v in stats.values():
                v.configure(text_color=T["fg_main"],
                            font=("Consolas", zf(11), "bold"))
        for d in (self._net_stats, self._disk_stats):
            for vl, col in d.values():
                vl.configure(text_color=T["fg_main"],
                              font=("Consolas", zf(10), "bold"))


# ═══════════════════════════════════════════════════════════════════════════════
# OPTIMIZER TAB
# ═══════════════════════════════════════════════════════════════════════════════

# Known bloat: (display_name, service_name_or_None, task_path_or_None, safe_to_disable)
BLOAT_ITEMS = [
    # display,                        service,                          task,                                               note
    ("Killer Network Service",        "KillerNetworkService",           None,                                               "Intel Killer suite – network QoS"),
    ("Killer Analytics Service",      "KillerAnalyticsService",         None,                                               "Intel Killer – analytics/telemetry"),
    ("Killer APS",                    None,                             "\\KillerNetworkingLLC\\KillerAPS",                 "Killer app scheduler (delayed start)"),
    ("Intel Driver & Support Asst.",  "DSAService",                     None,                                               "Driver update background service"),
    ("Intel Driver Update",           None,                             "\\Intel\\Intel Driver and Support Assistant",      "Driver update scheduled task"),
    ("Phone Link / Mobile",           None,                             "\\Microsoft\\Windows\\MobilePC\\HotStart",         "Microsoft Phone Link launcher"),
    ("Phone Link Service",            "PhoneExperienceHost",            None,                                               "Phone Link background service"),
    ("Search Indexer",                "WSearch",                        None,                                               "Windows Search indexing (high disk I/O)"),
    ("Xbox Game Bar",                 "XblGameSave",                    None,                                               "Xbox Game Bar save sync"),
    ("Xbox Game Bar Task",            None,                             "\\Microsoft\\XblGameSave\\XblGameSaveTask",        "Xbox save task"),
    ("AcerSense Helper",              None,                             "\\Acer\\AcerSense",                                "AcerSense background task (fan UI kept)"),
    ("QuickPanel",                    None,                             "\\Acer\\QuickPanel",                               "Acer QuickPanel overlay"),
    ("QuickPanel OSD",                "AcerQuickPanelOSD",              None,                                               "Acer OSD service"),
    ("Acersense Service",             "AcerSenseService",               None,                                               "AcerSense service (re-enable for fan ctrl)"),
]

POWER_PLANS = [
    ("🔇  Silent / Power Saver",     "a1841308-3541-4fab-bc81-f71556f20b4a"),
    ("⚖  Balanced (recommended)",    "381b4222-f694-41f0-9685-ff5bb260df2e"),
    ("⚡  High Performance",          "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),
]

class OptimizerTab(ctk.CTkFrame):
    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._vars   = {}   # display_name -> BooleanVar (enabled state)
        self._status = {}   # display_name -> StringVar (status label)
        self._all_widgets = []  # for repaint
        self._build_ui()
        threading.Thread(target=self._load_states, daemon=True).start()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=T["bg_card"], corner_radius=10, **kw)

    def _section_header(self, parent, text, accent_key="accent"):
        lbl = ctk.CTkLabel(parent, text=text,
                           font=("Consolas", zf(11), "bold"),
                           text_color=T[accent_key])
        lbl.pack(anchor="w", padx=14, pady=(12, 4))
        self._all_widgets.append(("section_lbl", lbl, accent_key))
        return lbl

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll

        self._build_power_section(scroll)
        self._build_ram_section(scroll)
        self._build_bloat_section(scroll)
        self._build_startup_section(scroll)

    # ── Power Plans ───────────────────────────────────────────────────────────

    def _build_power_section(self, parent):
        card = self._card(parent)
        card.pack(fill="x", padx=6, pady=(6, 4))
        self._all_widgets.append(("card", card))

        hdr = ctk.CTkLabel(card, text="⚡  POWER PLAN",
                           font=("Consolas", zf(11), "bold"),
                           text_color=T["accent"])
        hdr.pack(anchor="w", padx=14, pady=(12, 2))
        self._all_widgets.append(("lbl", hdr, "accent"))

        sub = ctk.CTkLabel(card, text="Controls CPU throttling and fan behaviour. Silent = quiet fans, lower power.",
                           font=("Consolas", zf(9)), text_color=T["fg_dim"])
        sub.pack(anchor="w", padx=14, pady=(0, 8))
        self._all_widgets.append(("lbl", sub, "fg_dim"))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 12))
        self._power_btns = []
        self._power_status = ctk.StringVar(value="")
        for label, guid in POWER_PLANS:
            b = ctk.CTkButton(btn_row, text=label, height=36,
                              fg_color=T["bg_row"], hover_color=T["bg_row2"],
                              text_color=T["fg_main"],
                              font=("Consolas", zf(10)),
                              command=lambda g=guid, lb=label: self._set_power(g, lb))
            b.pack(side="left", padx=(0, 8))
            self._power_btns.append(b)
        self._lbl_power_status = ctk.CTkLabel(card, textvariable=self._power_status,
                                               font=("Consolas", zf(9)),
                                               text_color=T["accent3"])
        self._lbl_power_status.pack(anchor="w", padx=14, pady=(0, 4))
        self._all_widgets.append(("lbl", self._lbl_power_status, "accent3"))

        # Show current plan
        threading.Thread(target=self._refresh_power_label, daemon=True).start()

    def _set_power(self, guid, label):
        def _do():
            rc, out = run_ps(f"powercfg /setactive {guid}")
            if rc == 0:
                self._power_status.set(f"✓ Active: {label.split('  ',1)[-1]}")
            else:
                self._power_status.set(f"✗ Failed (run as Admin?): {out[:60]}")
        threading.Thread(target=_do, daemon=True).start()

    def _refresh_power_label(self):
        rc, out = run_ps("powercfg /getactivescheme")
        if rc == 0 and out:
            # Extract plan name from output like: "Power Scheme GUID: ... (Balanced)"
            import re
            m = re.search(r'\((.+)\)', out)
            name = m.group(1) if m else out[:40]
            self._power_status.set(f"Current: {name}")

    # ── RAM Flush ─────────────────────────────────────────────────────────────

    def _build_ram_section(self, parent):
        card = self._card(parent)
        card.pack(fill="x", padx=6, pady=4)
        self._all_widgets.append(("card", card))

        hdr = ctk.CTkLabel(card, text="🧹  RAM WORKING SET FLUSH",
                           font=("Consolas", zf(11), "bold"),
                           text_color=T["accent4"])
        hdr.pack(anchor="w", padx=14, pady=(12, 2))
        self._all_widgets.append(("lbl", hdr, "accent4"))

        sub = ctk.CTkLabel(card,
            text="Trims working sets of all user processes — reclaims RAM held by idle apps.\n"
                 "Safe, instant, and reversible (Windows re-pages as needed). Requires Admin.",
            font=("Consolas", zf(9)), text_color=T["fg_dim"], justify="left")
        sub.pack(anchor="w", padx=14, pady=(0, 8))
        self._all_widgets.append(("lbl", sub, "fg_dim"))

        act_row = ctk.CTkFrame(card, fg_color="transparent")
        act_row.pack(fill="x", padx=14, pady=(0, 12))

        self._ram_status = ctk.StringVar(value="")
        btn = ctk.CTkButton(act_row, text="⚡  Flush RAM Now", height=36, width=180,
                            fg_color=T["accent4"], hover_color=T["accent"],
                            text_color=T["fg_bright"], font=("Consolas", zf(10), "bold"),
                            command=self._flush_ram)
        btn.pack(side="left")
        self._ram_btn = btn
        self._all_widgets.append(("btn_accent4", btn))

        self._lbl_ram_status = ctk.CTkLabel(act_row, textvariable=self._ram_status,
                                             font=("Consolas", zf(9)),
                                             text_color=T["accent3"], padx=14)
        self._lbl_ram_status.pack(side="left")
        self._all_widgets.append(("lbl", self._lbl_ram_status, "accent3"))

    def _flush_ram(self):
        self._ram_status.set("Flushing…")
        self._ram_btn.configure(state="disabled")
        def _do():
            before = psutil.virtual_memory().used
            # Use PowerShell + EmptyWorkingSet via .NET for each user process
            ps_script = """
$before = (Get-Counter '\\Memory\\Available MBytes').CounterSamples[0].CookedValue
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WS {
    [DllImport("psapi.dll")] public static extern bool EmptyWorkingSet(IntPtr h);
}
"@
$procs = Get-Process | Where-Object {$_.SessionId -gt 0}
$ok = 0
foreach ($p in $procs) {
    try { [WS]::EmptyWorkingSet($p.Handle) | Out-Null; $ok++ } catch {}
}
$after = (Get-Counter '\\Memory\\Available MBytes').CounterSamples[0].CookedValue
Write-Output "$ok processes trimmed. Available before: ${before}MB  after: ${after}MB"
"""
            rc, out = run_ps(ps_script)
            after = psutil.virtual_memory().used
            freed = max(0, before - after)
            if rc == 0 and out:
                msg = out.split('\n')[-1].strip() or f"Freed ~{bytes_to_human(freed)}"
            else:
                msg = f"Freed ~{bytes_to_human(freed)} (run as Admin for best results)"
            self.after(0, lambda: self._ram_status.set(f"✓ {msg}"))
            self.after(0, lambda: self._ram_btn.configure(state="normal"))
        threading.Thread(target=_do, daemon=True).start()

    # ── Bloat Services & Tasks ────────────────────────────────────────────────

    def _build_bloat_section(self, parent):
        card = self._card(parent)
        card.pack(fill="x", padx=6, pady=4)
        self._all_widgets.append(("card", card))

        hdr = ctk.CTkLabel(card, text="🚫  BACKGROUND BLOAT",
                           font=("Consolas", zf(11), "bold"),
                           text_color=T["danger"])
        hdr.pack(anchor="w", padx=14, pady=(12, 2))
        self._all_widgets.append(("lbl", hdr, "danger"))

        sub = ctk.CTkLabel(card,
            text="Toggle services and scheduled tasks. Disabled items won't auto-start.\n"
                 "Re-enable anytime. Requires Administrator for services.",
            font=("Consolas", zf(9)), text_color=T["fg_dim"], justify="left")
        sub.pack(anchor="w", padx=14, pady=(0, 6))
        self._all_widgets.append(("lbl", sub, "fg_dim"))

        # Column headers
        col_hdr = ctk.CTkFrame(card, fg_color="transparent")
        col_hdr.pack(fill="x", padx=14, pady=(0, 2))
        for txt, anchor, expand in [
            ("Service / Task", "w", True),
            ("Note", "w", True),
            ("Status", "center", False),
            ("", "center", False),
        ]:
            lbl = ctk.CTkLabel(col_hdr, text=txt,
                               font=("Consolas", zf(8), "bold"),
                               text_color=T["fg_dim"],
                               anchor=anchor,
                               width=0 if expand else 70)
            lbl.pack(side="left", expand=expand, fill="x" if expand else "none")
            self._all_widgets.append(("lbl", lbl, "fg_dim"))

        sep = tk.Frame(card, bg=T["sep"], height=1)
        sep.pack(fill="x", padx=14, pady=(0, 4))
        self._bloat_sep = sep

        self._bloat_rows = []
        for display, svc, task, note in BLOAT_ITEMS:
            self._add_bloat_row(card, display, svc, task, note)

        # All on / all off buttons
        act = ctk.CTkFrame(card, fg_color="transparent")
        act.pack(fill="x", padx=14, pady=(8, 12))
        b_off = ctk.CTkButton(act, text="🚫  Disable All", height=32, width=140,
                              fg_color=T["danger"], hover_color="#AA1030",
                              text_color=T["fg_bright"], font=("Consolas", zf(10), "bold"),
                              command=lambda: self._bulk_bloat(enable=False))
        b_off.pack(side="left", padx=(0, 8))
        b_on = ctk.CTkButton(act, text="✓  Re-enable All", height=32, width=140,
                             fg_color=T["accent3"], hover_color="#1A6020",
                             text_color=T["fg_bright"], font=("Consolas", zf(10), "bold"),
                             command=lambda: self._bulk_bloat(enable=True))
        b_on.pack(side="left")
        self._bloat_bulk_btns = [b_off, b_on]
        self._all_widgets.append(("btn_danger", b_off))
        self._all_widgets.append(("btn_accent3", b_on))

    def _add_bloat_row(self, parent, display, svc, task, note):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=1)

        name_lbl = ctk.CTkLabel(row, text=display,
                                font=("Consolas", zf(10)),
                                text_color=T["fg_main"], anchor="w", width=200)
        name_lbl.pack(side="left")

        note_lbl = ctk.CTkLabel(row, text=note,
                                font=("Consolas", zf(8)),
                                text_color=T["fg_dim"], anchor="w")
        note_lbl.pack(side="left", expand=True, fill="x", padx=8)

        st_var = ctk.StringVar(value="…")
        st_lbl = ctk.CTkLabel(row, textvariable=st_var,
                              font=("Consolas", zf(9)),
                              text_color=T["fg_dim"], width=70, anchor="center")
        st_lbl.pack(side="left", padx=4)

        btn = ctk.CTkButton(row, text="Toggle", width=80, height=26,
                            fg_color=T["bg_row"], hover_color=T["bg_row2"],
                            text_color=T["fg_main"], font=("Consolas", zf(9)),
                            command=lambda d=display, s=svc, t=task, sv=st_var, b=None:
                                self._toggle_bloat(d, s, t, sv))
        btn.pack(side="left", padx=2)

        self._status[display] = st_var
        self._bloat_rows.append((row, name_lbl, note_lbl, st_lbl, btn))
        self._all_widgets.append(("bloat_row", row, name_lbl, note_lbl, st_lbl, btn))

    def _load_states(self):
        """Query each item's current state in a background thread."""
        for display, svc, task, _ in BLOAT_ITEMS:
            state = self._query_state(svc, task)
            if display in self._status:
                sv = self._status[display]
                self.after(0, lambda sv=sv, s=state: sv.set(s))

    def _query_state(self, svc, task):
        if svc:
            rc, out = run_ps(f"(Get-Service -Name '{svc}' -ErrorAction SilentlyContinue).StartType")
            if rc == 0 and out:
                return out.strip()
            return "N/A"
        elif task:
            rc, out = run_ps(f"(Get-ScheduledTask -TaskPath '*' -TaskName '*' | "
                             f"Where-Object {{$_.TaskPath+$_.TaskName -like '*{task.split(chr(92))[-1]}*'}} | "
                             f"Select-Object -First 1).State")
            if rc == 0 and out:
                return out.strip()
            return "N/A"
        return "N/A"

    def _toggle_bloat(self, display, svc, task, st_var):
        current = st_var.get()
        # Determine if currently enabled
        enabled = current.lower() not in ("disabled", "ready_disabled", "n/a")
        # If unknown/loading, default to disable
        will_disable = enabled or current in ("…", "Running", "Automatic", "Manual")
        st_var.set("…working…")
        def _do():
            if svc:
                if will_disable:
                    run_ps(f"Stop-Service -Name '{svc}' -Force -ErrorAction SilentlyContinue; "
                           f"Set-Service -Name '{svc}' -StartupType Disabled")
                else:
                    run_ps(f"Set-Service -Name '{svc}' -StartupType Manual; "
                           f"Start-Service -Name '{svc}' -ErrorAction SilentlyContinue")
            elif task:
                tname = task.split("\\")[-1]
                if will_disable:
                    run_ps(f"Disable-ScheduledTask -TaskName '{tname}' -ErrorAction SilentlyContinue")
                else:
                    run_ps(f"Enable-ScheduledTask -TaskName '{tname}' -ErrorAction SilentlyContinue")
            new_state = self._query_state(svc, task)
            self.after(0, lambda: st_var.set(new_state))
        threading.Thread(target=_do, daemon=True).start()

    def _bulk_bloat(self, enable: bool):
        def _do():
            for display, svc, task, _ in BLOAT_ITEMS:
                if svc:
                    if enable:
                        run_ps(f"Set-Service -Name '{svc}' -StartupType Manual -ErrorAction SilentlyContinue")
                    else:
                        run_ps(f"Stop-Service -Name '{svc}' -Force -ErrorAction SilentlyContinue; "
                               f"Set-Service -Name '{svc}' -StartupType Disabled -ErrorAction SilentlyContinue")
                elif task:
                    tname = task.split("\\")[-1]
                    action = "Enable" if enable else "Disable"
                    run_ps(f"{action}-ScheduledTask -TaskName '{tname}' -ErrorAction SilentlyContinue")
            # Refresh all states
            self.after(200, lambda: threading.Thread(
                target=self._load_states, daemon=True).start())
        threading.Thread(target=_do, daemon=True).start()

    # ── Startup Manager ───────────────────────────────────────────────────────

    def _build_startup_section(self, parent):
        card = self._card(parent)
        card.pack(fill="x", padx=6, pady=(4, 10))
        self._all_widgets.append(("card", card))

        hdr = ctk.CTkLabel(card, text="🚀  STARTUP PROGRAMS",
                           font=("Consolas", zf(11), "bold"),
                           text_color=T["warn"])
        hdr.pack(anchor="w", padx=14, pady=(12, 2))
        self._all_widgets.append(("lbl", hdr, "warn"))

        sub = ctk.CTkLabel(card,
            text="Programs registered to launch at login (registry + common Task Scheduler paths).",
            font=("Consolas", zf(9)), text_color=T["fg_dim"], justify="left")
        sub.pack(anchor="w", padx=14, pady=(0, 6))
        self._all_widgets.append(("lbl", sub, "fg_dim"))

        ref_btn = ctk.CTkButton(card, text="↺  Scan Startup Items", height=30, width=180,
                                fg_color=T["bg_row"], hover_color=T["bg_row2"],
                                text_color=T["fg_main"], font=("Consolas", zf(10)),
                                command=self._scan_startup)
        ref_btn.pack(anchor="w", padx=14, pady=(0, 6))
        self._all_widgets.append(("btn_row", ref_btn))

        self._startup_frame = ctk.CTkScrollableFrame(card, fg_color="transparent", height=200)
        self._startup_frame.pack(fill="x", padx=14, pady=(0, 12))

        self._startup_placeholder = ctk.CTkLabel(
            self._startup_frame,
            text="Click 'Scan Startup Items' to load…",
            font=("Consolas", zf(9)), text_color=T["fg_dim"])
        self._startup_placeholder.pack(padx=8, pady=8)

    def _scan_startup(self):
        for w in self._startup_frame.winfo_children():
            w.destroy()
        loading = ctk.CTkLabel(self._startup_frame, text="Scanning…",
                               font=("Consolas", zf(9)), text_color=T["fg_dim"])
        loading.pack()
        threading.Thread(target=self._do_scan_startup, daemon=True).start()

    def _do_scan_startup(self):
        ps = """
$items = @()
$regPaths = @(
  'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
  'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
  'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Run'
)
foreach ($rp in $regPaths) {
  if (Test-Path $rp) {
    $vals = Get-ItemProperty $rp -ErrorAction SilentlyContinue
    $vals.PSObject.Properties | Where-Object {$_.Name -notlike 'PS*'} | ForEach-Object {
      $items += [PSCustomObject]@{Name=$_.Name; Source='Registry'; Value=$_.Value; Enabled=$true}
    }
  }
}
# Startup folder
$startupFolders = @(
  [Environment]::GetFolderPath('Startup'),
  [Environment]::GetFolderPath('CommonStartup')
)
foreach ($sf in $startupFolders) {
  if (Test-Path $sf) {
    Get-ChildItem $sf -File | ForEach-Object {
      $items += [PSCustomObject]@{Name=$_.BaseName; Source='Startup Folder'; Value=$_.FullName; Enabled=$true}
    }
  }
}
$items | ConvertTo-Json -Compress
"""
        rc, out = run_ps(ps)
        import json, re
        items = []
        if rc == 0 and out:
            try:
                # out might have extra text before JSON
                m = re.search(r'(\[.*\]|\{.*\})', out, re.DOTALL)
                raw = m.group(1) if m else out
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                items = parsed or []
            except Exception:
                items = []
        self.after(0, lambda: self._show_startup_items(items))

    def _show_startup_items(self, items):
        for w in self._startup_frame.winfo_children():
            w.destroy()
        if not items:
            ctk.CTkLabel(self._startup_frame,
                         text="No startup items found (or run as Admin for full list).",
                         font=("Consolas", zf(9)), text_color=T["fg_dim"]).pack(pady=8)
            return
        for item in items:
            name = str(item.get("Name", "?"))[:40]
            src  = str(item.get("Source", ""))
            val  = str(item.get("Value", ""))[:60]

            row = ctk.CTkFrame(self._startup_frame, fg_color=T["bg_row"],
                               corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)

            ctk.CTkLabel(row, text=name,
                         font=("Consolas", zf(10), "bold"),
                         text_color=T["fg_main"], anchor="w", width=180
                         ).pack(side="left", padx=8, pady=4)
            ctk.CTkLabel(row, text=src,
                         font=("Consolas", zf(8)),
                         text_color=T["accent"], anchor="w", width=100
                         ).pack(side="left")
            ctk.CTkLabel(row, text=val,
                         font=("Consolas", zf(8)),
                         text_color=T["fg_dim"], anchor="w"
                         ).pack(side="left", expand=True, fill="x", padx=4)

    # ── Repaint ───────────────────────────────────────────────────────────────

    def repaint(self):
        self._scroll.configure(fg_color="transparent")
        for entry in self._all_widgets:
            kind = entry[0]
            if kind == "card":
                entry[1].configure(fg_color=T["bg_card"])
            elif kind == "lbl":
                _, w, col = entry
                w.configure(text_color=T[col], font=("Consolas", zf(9)))
            elif kind == "section_lbl":
                _, w, col = entry
                w.configure(text_color=T[col], font=("Consolas", zf(11), "bold"))
            elif kind == "btn_row":
                entry[1].configure(fg_color=T["bg_row"], hover_color=T["bg_row2"],
                                   text_color=T["fg_main"], font=("Consolas", zf(10)))
            elif kind == "btn_accent4":
                entry[1].configure(fg_color=T["accent4"], text_color=T["fg_bright"],
                                   font=("Consolas", zf(10), "bold"))
            elif kind == "btn_danger":
                entry[1].configure(fg_color=T["danger"], text_color=T["fg_bright"],
                                   font=("Consolas", zf(10), "bold"))
            elif kind == "btn_accent3":
                entry[1].configure(fg_color=T["accent3"], text_color=T["fg_bright"],
                                   font=("Consolas", zf(10), "bold"))
            elif kind == "bloat_row":
                _, row, name_lbl, note_lbl, st_lbl, btn = entry
                name_lbl.configure(text_color=T["fg_main"], font=("Consolas", zf(10)))
                note_lbl.configure(text_color=T["fg_dim"], font=("Consolas", zf(8)))
                st_lbl.configure(text_color=T["fg_dim"], font=("Consolas", zf(9)))
                btn.configure(fg_color=T["bg_row"], hover_color=T["bg_row2"],
                              text_color=T["fg_main"], font=("Consolas", zf(9)))
        for b in self._power_btns:
            b.configure(fg_color=T["bg_row"], hover_color=T["bg_row2"],
                        text_color=T["fg_main"], font=("Consolas", zf(10)))
        # Startup items
        for row in self._startup_frame.winfo_children():
            if isinstance(row, ctk.CTkFrame):
                row.configure(fg_color=T["bg_row"])
                for w in row.winfo_children():
                    if isinstance(w, ctk.CTkLabel):
                        w.configure(font=("Consolas", zf(9)))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

class SysOptimizer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SysOptimizer")
        self.geometry("1200x860")
        self.minsize(1000, 700)
        self.configure(fg_color=T["bg_deep"])
        self._is_dark    = True
        self._running    = True
        self._active_tab = "performance"

        # Prevent CTK from doing its own appearance switches (causes flash)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._build_ui()
        self._start_polling()

        self.bind("<Control-equal>",      lambda e: self._zoom(+1))
        self.bind("<Control-plus>",       lambda e: self._zoom(+1))
        self.bind("<Control-minus>",      lambda e: self._zoom(-1))
        self.bind("<Control-0>",          lambda e: self._zoom(0))
        self.bind("<Control-MouseWheel>", self._on_ctrl_scroll)

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_titlebar()
        self._build_tabs()
        self._build_statusbar()

    def _build_titlebar(self):
        self._tb = ctk.CTkFrame(self, fg_color=T["bg_card"],
                                height=56, corner_radius=0)
        self._tb.pack(fill="x")
        self._tb.pack_propagate(False)

        self._lbl_title = ctk.CTkLabel(self._tb, text="⚡  SYSOPTIMIZER",
                     font=("Consolas", zf(16), "bold"),
                     text_color=T["accent"])
        self._lbl_title.pack(side="left", padx=18, pady=10)

        self._lbl_sys = ctk.CTkLabel(
            self._tb,
            text=f"{platform.node()}  ·  {platform.system()} {platform.release()}",
            font=("Consolas", zf(10)), text_color=T["fg_dim"])
        self._lbl_sys.pack(side="left", padx=8)

        right_bar = ctk.CTkFrame(self._tb, fg_color="transparent")
        right_bar.pack(side="right", padx=10)

        self._theme_btn = ctk.CTkButton(
            right_bar, text="☀  Light",
            width=90, height=30,
            fg_color=T["toggle_bg"], hover_color=T["bg_row"],
            text_color=T["fg_dim"], font=("Consolas", zf(10)),
            command=self._toggle_theme)
        self._theme_btn.pack(side="right", padx=6, pady=12)

        self._zoom_frame = ctk.CTkFrame(right_bar, fg_color=T["bg_row"],
                                        corner_radius=8)
        self._zoom_frame.pack(side="right", padx=4, pady=12)
        self._btn_zoom_out = ctk.CTkButton(
            self._zoom_frame, text="−", width=30, height=30,
            fg_color="transparent", hover_color=T["bg_row2"],
            font=("Consolas", zf(14), "bold"), text_color=T["fg_main"],
            command=lambda: self._zoom(-1))
        self._btn_zoom_out.pack(side="left")
        self._lbl_zoom = ctk.CTkLabel(
            self._zoom_frame, text=f"{ZOOM_LEVELS[_zoom_idx]}pt",
            width=42, font=("Consolas", zf(10)), text_color=T["fg_dim"])
        self._lbl_zoom.pack(side="left")
        self._btn_zoom_in = ctk.CTkButton(
            self._zoom_frame, text="+", width=30, height=30,
            fg_color="transparent", hover_color=T["bg_row2"],
            font=("Consolas", zf(14), "bold"), text_color=T["fg_main"],
            command=lambda: self._zoom(+1))
        self._btn_zoom_in.pack(side="left")

        self._lbl_time = ctk.CTkLabel(
            right_bar, text="",
            font=("Consolas", zf(10)), text_color=T["fg_dim"])
        self._lbl_time.pack(side="right", padx=10)

    def _build_tabs(self):
        self._tab_bar = ctk.CTkFrame(self, fg_color=T["bg_card"],
                                      height=40, corner_radius=0)
        self._tab_bar.pack(fill="x")
        self._tab_bar.pack_propagate(False)

        sep = tk.Frame(self, bg=T["sep"], height=1)
        sep.pack(fill="x")
        self._sep = sep

        self._tab_btns = {}
        tabs = [
            ("performance", "📊  Performance"),
            ("processes",   "⚙  Processes"),
            ("optimizer",   "🚀  Optimizer"),
        ]
        for tab_id, label in tabs:
            active = (tab_id == "performance")
            btn = ctk.CTkButton(
                self._tab_bar, text=label,
                width=160, height=38, corner_radius=0,
                fg_color=T["accent"] if active else T["bg_card"],
                hover_color=T["bg_row"],
                text_color=T["bg_deep"] if active else T["fg_dim"],
                font=("Consolas", zf(11), "bold"),
                command=lambda t=tab_id: self._switch_tab(t))
            btn.pack(side="left", padx=0)
            self._tab_btns[tab_id] = btn

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(fill="both", expand=True, padx=14, pady=8)

        self.perf_tab = PerformanceTab(self._content)
        self.perf_tab.pack(fill="both", expand=True)

        self._procs_frame = ctk.CTkFrame(self._content, fg_color="transparent")
        self.proc_sidebar = self._build_proc_sidebar(self._procs_frame)
        self.proc_table   = ProcessTable(self._procs_frame)
        self.proc_table.pack(fill="both", expand=True)

        self.opt_tab = OptimizerTab(self._content)

        self._switch_tab("performance")

    def _build_proc_sidebar(self, parent):
        sidebar = ctk.CTkFrame(parent, fg_color="transparent", width=260)
        sidebar.pack(side="left", fill="y", padx=(0, 10))
        sidebar.pack_propagate(False)

        self._disk_card_p = ctk.CTkFrame(sidebar, fg_color=T["bg_card"],
                                          corner_radius=10)
        self._disk_card_p.pack(fill="x", pady=(0, 8))
        self._lbl_disk_p = ctk.CTkLabel(
            self._disk_card_p, text="DISK USAGE",
            font=("Consolas", zf(10), "bold"), text_color=T["fg_dim"])
        self._lbl_disk_p.pack(anchor="w", padx=14, pady=(10, 6))
        self._disk_inner_p = ctk.CTkFrame(self._disk_card_p, fg_color="transparent")
        self._disk_inner_p.pack(fill="x", padx=14, pady=(0, 10))

        self._qa_card = ctk.CTkFrame(sidebar, fg_color=T["bg_card"], corner_radius=10)
        self._qa_card.pack(fill="x")
        self._lbl_qa = ctk.CTkLabel(
            self._qa_card, text="QUICK ACTIONS",
            font=("Consolas", zf(10), "bold"), text_color=T["fg_dim"])
        self._lbl_qa.pack(anchor="w", padx=14, pady=(10, 6))

        self._qa_btns = []
        for txt, cmd in [
            ("🗑   Empty Recycle Bin",  self._empty_recycle),
            ("💀  Kill High-CPU Tasks", self._kill_high_cpu),
            ("📋  Export Report",        self._export_report),
        ]:
            b = ctk.CTkButton(self._qa_card, text=txt, height=36,
                              fg_color=T["bg_row"], hover_color=T["bg_row2"],
                              text_color=T["fg_main"], font=("Consolas", zf(10)),
                              command=cmd, anchor="w")
            b.pack(fill="x", padx=14, pady=3)
            self._qa_btns.append(b)
        ctk.CTkFrame(self._qa_card, height=8, fg_color="transparent").pack()
        return sidebar

    def _build_statusbar(self):
        self._sb = ctk.CTkFrame(self, fg_color=T["bg_card"],
                                 height=30, corner_radius=0)
        self._sb.pack(fill="x", side="bottom")
        self._sb.pack_propagate(False)
        self._lbl_status = ctk.CTkLabel(
            self._sb, text="Ready",
            font=("Consolas", zf(9)), text_color=T["fg_dim"])
        self._lbl_status.pack(side="left", padx=14, pady=5)
        self._lbl_hint = ctk.CTkLabel(
            self._sb, text="Ctrl +/−  zoom  ·  Ctrl+0  reset",
            font=("Consolas", zf(9)), text_color=T["fg_dim"])
        self._lbl_hint.pack(side="left", padx=14)
        self._lbl_proc_count = ctk.CTkLabel(
            self._sb, text="",
            font=("Consolas", zf(9)), text_color=T["fg_dim"])
        self._lbl_proc_count.pack(side="right", padx=14, pady=5)

    # ── Tab switching ─────────────────────────────────────────────────────────

    def _switch_tab(self, tab_id):
        self._active_tab = tab_id
        self.perf_tab.pack_forget()
        self._procs_frame.pack_forget()
        self.opt_tab.pack_forget()

        if tab_id == "performance":
            self.perf_tab.pack(fill="both", expand=True)
        elif tab_id == "processes":
            self._procs_frame.pack(fill="both", expand=True)
        else:
            self.opt_tab.pack(fill="both", expand=True)

        for tid, btn in self._tab_btns.items():
            active = (tid == tab_id)
            btn.configure(
                fg_color=T["accent"] if active else T["bg_card"],
                text_color=T["bg_deep"] if active else T["fg_dim"])

    # ── Zoom ──────────────────────────────────────────────────────────────────

    def _on_ctrl_scroll(self, event):
        self._zoom(+1 if event.delta > 0 else -1)

    def _zoom(self, delta):
        global _zoom_idx
        if delta == 0:
            _zoom_idx = DEFAULT_ZOOM
        else:
            _zoom_idx = max(0, min(len(ZOOM_LEVELS) - 1, _zoom_idx + delta))
        self._repaint_all()

    # ── Theme (no CTK mode switch — avoids flash) ─────────────────────────────

    def _toggle_theme(self):
        self._is_dark = not self._is_dark
        T.update(DARK if self._is_dark else LIGHT)
        # Do NOT call ctk.set_appearance_mode — it destroys and rebuilds widgets
        self._repaint_all()

    # ── Full repaint ──────────────────────────────────────────────────────────

    def _repaint_all(self):
        self.configure(fg_color=T["bg_deep"])
        self._tb.configure(fg_color=T["bg_card"])
        self._tab_bar.configure(fg_color=T["bg_card"])
        self._sep.configure(bg=T["sep"])
        self._lbl_title.configure(text_color=T["accent"],
                                   font=("Consolas", zf(16), "bold"))
        self._lbl_sys.configure(text_color=T["fg_dim"],
                                 font=("Consolas", zf(10)))
        self._lbl_time.configure(text_color=T["fg_dim"],
                                  font=("Consolas", zf(10)))

        icon = "🌙  Dark" if not self._is_dark else "☀  Light"
        self._theme_btn.configure(text=icon, fg_color=T["toggle_bg"],
                                   hover_color=T["bg_row"], text_color=T["fg_dim"],
                                   font=("Consolas", zf(10)))

        # Zoom frame + buttons — fully repainted
        self._zoom_frame.configure(fg_color=T["bg_row"])
        self._lbl_zoom.configure(text=f"{ZOOM_LEVELS[_zoom_idx]}pt",
                                  font=("Consolas", zf(10)),
                                  text_color=T["fg_dim"])
        for btn in (self._btn_zoom_in, self._btn_zoom_out):
            btn.configure(fg_color="transparent",
                          hover_color=T["bg_row2"],
                          text_color=T["fg_main"],
                          font=("Consolas", zf(14), "bold"))

        # Tab buttons
        for tid, btn in self._tab_btns.items():
            active = (tid == self._active_tab)
            btn.configure(
                fg_color=T["accent"] if active else T["bg_card"],
                text_color=T["bg_deep"] if active else T["fg_dim"],
                font=("Consolas", zf(11), "bold"))

        # Status bar
        self._sb.configure(fg_color=T["bg_card"])
        for w in (self._lbl_status, self._lbl_hint, self._lbl_proc_count):
            w.configure(text_color=T["fg_dim"], font=("Consolas", zf(9)))

        # Tab contents
        self.perf_tab.repaint()
        self.proc_table.repaint()
        self.opt_tab.repaint()

        # Sidebar
        self._disk_card_p.configure(fg_color=T["bg_card"])
        self._lbl_disk_p.configure(text_color=T["fg_dim"],
                                    font=("Consolas", zf(10), "bold"))
        self._qa_card.configure(fg_color=T["bg_card"])
        self._lbl_qa.configure(text_color=T["fg_dim"],
                                font=("Consolas", zf(10), "bold"))
        for b in self._qa_btns:
            b.configure(fg_color=T["bg_row"], hover_color=T["bg_row2"],
                        text_color=T["fg_main"], font=("Consolas", zf(10)))
        self._update_disk_sidebar()

    # ── Polling ───────────────────────────────────────────────────────────────

    def _start_polling(self):
        self.proc_table.refresh()
        self._poll_perf()
        self._poll_procs()

    def _poll_perf(self):
        if not self._running:
            return
        threading.Thread(target=self._fetch_perf, daemon=True).start()

    def _fetch_perf(self):
        cpu_total  = psutil.cpu_percent(interval=1.0)
        per_core   = psutil.cpu_percent(interval=None, percpu=True)
        ram        = psutil.virtual_memory()
        swap       = psutil.swap_memory()
        freq       = psutil.cpu_freq()
        try:
            net = psutil.net_io_counters()
        except Exception:
            net = None
        try:
            disk_io = psutil.disk_io_counters()
        except Exception:
            disk_io = None
        self.after(0, lambda: self._update_perf(
            cpu_total, per_core, ram, swap, freq, net, disk_io))
        self.after(2000, self._poll_perf)

    def _update_perf(self, cpu_total, per_core, ram, swap, freq, net, disk_io):
        self._lbl_time.configure(
            text=datetime.now().strftime("%H:%M:%S  %d %b %Y"))
        self.perf_tab.update_cpu(cpu_total, per_core or [], freq)
        self.perf_tab.update_memory(ram, swap)
        if net:
            self.perf_tab.update_network(net)
        if disk_io:
            self.perf_tab.update_disk(disk_io)
        self._update_disk_sidebar()
        self._lbl_status.configure(
            text=f"Updated: {datetime.now().strftime('%H:%M:%S')}")

    def _update_disk_sidebar(self):
        for w in self._disk_inner_p.winfo_children():
            w.destroy()
        try:
            parts = psutil.disk_partitions(all=False)
        except Exception:
            return
        for part in parts:
            try:
                u = psutil.disk_usage(part.mountpoint)
            except (PermissionError, OSError):
                continue
            row = ctk.CTkFrame(self._disk_inner_p, fg_color="transparent")
            row.pack(fill="x", pady=4)
            dev = part.device.replace(":\\", ":").strip()
            ctk.CTkLabel(row, text=dev,
                         font=("Consolas", zf(10), "bold"),
                         text_color=T["fg_main"],
                         width=32, anchor="w").pack(side="left")
            bar = ctk.CTkProgressBar(row, height=9,
                                     progress_color=color_for_pct(u.percent),
                                     fg_color=T["bg_row"], width=110)
            bar.set(u.percent / 100)
            bar.pack(side="left", padx=8)
            ctk.CTkLabel(row,
                         text=f"{u.percent:.0f}%  ·  {bytes_to_human(u.free)} free",
                         font=("Consolas", zf(9)), text_color=T["fg_dim"]
                         ).pack(side="left")

    def _poll_procs(self):
        if not self._running:
            return
        threading.Thread(target=self._fetch_procs, daemon=True).start()

    def _fetch_procs(self):
        procs = get_processes()
        self.after(0, lambda: self._deliver_procs(procs))
        self.after(5000, self._poll_procs)

    def _deliver_procs(self, procs):
        self.proc_table.update_data(procs)
        self._lbl_proc_count.configure(text=f"{len(procs)} processes")

    # ── Quick actions ─────────────────────────────────────────────────────────

    def _empty_recycle(self):
        if platform.system() == "Windows":
            try:
                import winshell
                winshell.recycle_bin().empty(confirm=False,
                                             show_progress=False, sound=False)
                messagebox.showinfo("SysOptimizer", "Recycle Bin emptied.")
            except ImportError:
                os.system('PowerShell.exe -Command "Clear-RecycleBin -Force" 2>nul')
                messagebox.showinfo("SysOptimizer", "Recycle Bin emptied.")
        else:
            messagebox.showinfo("SysOptimizer", "Only available on Windows.")

    def _kill_high_cpu(self):
        threshold = 25.0
        procs = get_processes()
        candidates = [p for p in procs
                      if p["cpu"] >= threshold
                      and p["name"].lower() not in SAFE_PROCESSES]
        if not candidates:
            messagebox.showinfo("SysOptimizer",
                f"No user processes above {threshold}% CPU.")
            return
        names = "\n".join(
            f'  [{p["pid"]}]  {p["name"]}  ({p["cpu"]:.1f}%)'
            for p in candidates[:10])
        if not messagebox.askyesno("Kill High-CPU Processes",
                f"Kill these {len(candidates)} processes?\n\n{names}\n"):
            return
        killed = failed = 0
        for pi in candidates:
            try:
                psutil.Process(pi["pid"]).kill()
                killed += 1
            except Exception:
                failed += 1
        messagebox.showinfo("Done",
            f"Killed: {killed}   Failed/Protected: {failed}")
        self.proc_table.refresh()

    def _export_report(self):
        procs = get_processes()
        cpu   = psutil.cpu_percent(interval=0.3)
        ram   = psutil.virtual_memory()
        swap  = psutil.swap_memory()
        freq  = psutil.cpu_freq()
        lines = [
            "=" * 64,
            "  SYSOPTIMIZER REPORT",
            f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Host      : {platform.node()}",
            f"  OS        : {platform.system()} {platform.release()}",
            "=" * 64, "",
            "SYSTEM METRICS",
            f"  CPU Usage  : {cpu:.1f}%",
            (f"  CPU Freq   : {freq.current/1000:.2f} GHz" if freq
             else "  CPU Freq   : N/A"),
            f"  RAM Total  : {bytes_to_human(ram.total)}",
            f"  RAM Used   : {bytes_to_human(ram.used)}  ({ram.percent:.1f}%)",
            f"  RAM Free   : {bytes_to_human(ram.available)}",
            f"  Swap Used  : {bytes_to_human(swap.used)}", "",
            "DISK USAGE",
        ]
        for part in psutil.disk_partitions(all=False):
            try:
                u = psutil.disk_usage(part.mountpoint)
                lines.append(
                    f"  {part.device:<20} {u.percent:.0f}% used  /  "
                    f"{bytes_to_human(u.free)} free")
            except Exception:
                pass
        lines += ["", f"TOP 20 PROCESSES  ({len(procs)} total)", "-" * 64]
        top = sorted(procs, key=lambda p: p["cpu"], reverse=True)[:20]
        lines.append(f"{'PID':>7}  {'Name':<32}  {'CPU%':>6}  {'Memory'}")
        for p in top:
            lines.append(
                f"{p['pid']:>7}  {p['name']:<32}  {p['cpu']:>5.1f}%  "
                f"{bytes_to_human(p['mem'])}")
        path = os.path.join(
            os.path.expanduser("~"), "Desktop",
            f"sysopt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        try:
            with open(path, "w") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("Report Saved", f"Saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def on_close(self):
        self._running = False
        self.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = SysOptimizer()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
