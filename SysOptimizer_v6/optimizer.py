"""
SysOptimizer v6
- Performance tab: graph-free live numeric dashboard (CPU, RAM, Net, Disk)
- CPU boost clock via WMI (one-time startup query)
- Processes tab: Type column, right-click context menu, priority setter, total CPU/RAM footer
- Optimizer tab: CTT Ultimate Performance fix, live-color bloat status, startup enable/disable
- Scroll fix: targets CTK _parent_canvas with 3× multiplier
- Light default, 20pt, opens on Optimizer
"""

import customtkinter as ctk
import psutil
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import re
import json
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
    "type_system":    "#394A60",
    "type_service":   "#1A7A96",
    "type_user":      "#E4EAF4",
}

LIGHT = {
    "bg_deep":        "#F0F2F5",
    "bg_card":        "#FFFFFF",
    "bg_row":         "#F5F6F8",
    "bg_row2":        "#ECEEF2",
    "bg_graph":       "#F8F9FB",
    "fg_main":        "#1A1D23",
    "fg_dim":         "#7A8494",
    "fg_bright":      "#FFFFFF",
    "accent":         "#3B6FD4",
    "accent2":        "#D45F3B",
    "accent3":        "#2E9E55",
    "accent4":        "#7C4FD4",
    "danger":         "#D43B4F",
    "warn":           "#B07A20",
    "ring_track":     "#DDE1E8",
    "spark_cpu_fill": "#DCE8FB",
    "spark_ram_fill": "#FBE6DC",
    "sel":            "#C4D5F5",
    "border":         "#3B6FD4",
    "safe_fg":        "#A8B4C4",
    "high_fg":        "#B07A20",
    "toggle_bg":      "#ECEEF2",
    "sep":            "#E4E7EC",
    "mem_in_use":     "#3B6FD4",
    "mem_modified":   "#D45F3B",
    "mem_standby":    "#7C4FD4",
    "mem_free":       "#DDE1E8",
    "net_send":       "#2E9E55",
    "net_recv":       "#3B6FD4",
    "disk_read":      "#7C4FD4",
    "disk_write":     "#D45F3B",
    "type_system":    "#A8B4C4",
    "type_service":   "#3B6FD4",
    "type_user":      "#1A1D23",
}

T = dict(LIGHT)

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
DEFAULT_ZOOM = 9   # index 9 → 20pt
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
    """Run a PowerShell command silently. Returns (returncode, stdout)."""
    try:
        CREATE_NO_WINDOW = 0x08000000
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-WindowStyle", "Hidden",
             "-ExecutionPolicy", "Bypass", "-Command", cmd],
            capture_output=capture, text=True, timeout=20,
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
            mem  = info["memory_info"].rss if info["memory_info"] else 0
            user = (info["username"] or "").split("\\")[-1]
            # Classify type
            nm_low = (info["name"] or "").lower()
            if nm_low in SAFE_PROCESSES or not user:
                ptype = "System"
            elif "svc" in nm_low or nm_low.endswith("svc.exe") or "service" in nm_low:
                ptype = "Service"
            else:
                ptype = "User"
            procs.append({
                "pid":    info["pid"],
                "name":   info["name"] or "Unknown",
                "cpu":    info["cpu_percent"] or 0.0,
                "mem":    mem,
                "status": info["status"] or "",
                "user":   user,
                "type":   ptype,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return procs

# ═══════════════════════════════════════════════════════════════════════════════
# PROCESS TABLE  (with Type col, right-click menu, priority, totals footer)
# ═══════════════════════════════════════════════════════════════════════════════

class ProcessTable(ctk.CTkFrame):
    COLS      = ("PID", "Name", "Type", "CPU %", "Memory", "Status", "User")
    COL_W     = [64, 210, 72, 72, 96, 84, 120]
    COL_ANCHOR= {"PID": "center", "Name": "w", "Type": "center",
                 "CPU %": "center", "Memory": "center",
                 "Status": "center", "User": "center"}
    STYLE_NM  = "Proc.Treeview"

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
        self.tree.bind("<Button-3>", self._on_right_click)

        # Right-click context menu
        self._menu = tk.Menu(self, tearoff=0, bg=T["bg_card"],
                             fg=T["fg_main"], activebackground=T["sel"],
                             activeforeground=T["fg_main"],
                             font=("Consolas", zf(10)))
        self._menu.add_command(label="⚡  Kill Process",      command=self._kill_selected)
        self._menu.add_separator()
        self._menu.add_command(label="▲  Priority: High",     command=lambda: self._set_priority("high"))
        self._menu.add_command(label="●  Priority: Normal",   command=lambda: self._set_priority("normal"))
        self._menu.add_command(label="▼  Priority: Low",      command=lambda: self._set_priority("low"))
        self._menu.add_separator()
        self._menu.add_command(label="🔍  Search Online",     command=self._search_online)

        # Action bar
        act = ctk.CTkFrame(self, fg_color="transparent")
        act.pack(fill="x", padx=14, pady=(0, 4))

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

        # Totals footer
        self._footer = ctk.CTkFrame(self, fg_color="transparent")
        self._footer.pack(fill="x", padx=14, pady=(0, 10))
        self._lbl_totals = ctk.CTkLabel(self._footer, text="",
                                        font=("Consolas", zf(9)),
                                        text_color=T["fg_dim"])
        self._lbl_totals.pack(side="left")

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
        self._lbl_totals.configure(text_color=T["fg_dim"], font=("Consolas", zf(9)))
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
            "Type":   lambda p: p["type"],
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
        total_cpu = 0.0
        total_mem = 0
        for p in procs:
            total_cpu += p["cpu"]
            total_mem += p["mem"]
            safe = p["name"].lower() in SAFE_PROCESSES
            if safe:
                tag = "sys"
            elif p["type"] == "Service":
                tag = "svc"
            elif p["cpu"] > 15:
                tag = "high"
            else:
                tag = ""
            self.tree.insert("", "end", iid=str(p["pid"]), tags=(tag,),
                             values=(p["pid"], p["name"], p["type"],
                                     f'{p["cpu"]:.1f}',
                                     bytes_to_human(p["mem"]),
                                     p["status"], p["user"]))
        self.tree.tag_configure("sys",  foreground=T["safe_fg"])
        self.tree.tag_configure("svc",  foreground=T["type_service"])
        self.tree.tag_configure("high", foreground=T["high_fg"])
        if sel and self.tree.exists(str(sel)):
            self.tree.selection_set(str(sel))
        # Update footer totals
        self._lbl_totals.configure(
            text=f"{len(procs)} processes  ·  CPU: {total_cpu:.1f}%  ·  RAM: {bytes_to_human(total_mem)}")

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if sel:
            self._selected_pid = int(sel[0])
            vals = self.tree.item(sel[0], "values")
            self._lbl_sel.configure(text=f"● [{vals[0]}]  {vals[1]}  [{vals[2]}]")
        else:
            self._selected_pid = None
            self._lbl_sel.configure(text="No process selected")

    def _on_right_click(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            self.tree.selection_set(row)
            self._on_select()
            try:
                self._menu.tk_popup(event.x_root, event.y_root)
            finally:
                self._menu.grab_release()

    def _set_priority(self, level):
        if not self._selected_pid:
            messagebox.showwarning("SysOptimizer", "Select a process first.")
            return
        priority_map = {
            "high":   psutil.HIGH_PRIORITY_CLASS if platform.system() == "Windows" else -10,
            "normal": psutil.NORMAL_PRIORITY_CLASS if platform.system() == "Windows" else 0,
            "low":    psutil.IDLE_PRIORITY_CLASS if platform.system() == "Windows" else 10,
        }
        try:
            p = psutil.Process(self._selected_pid)
            if platform.system() == "Windows":
                p.nice(priority_map[level])
            else:
                p.nice(priority_map[level])
            self._lbl_sel.configure(
                text=f"✓ Priority set to {level} for [{self._selected_pid}]")
        except psutil.AccessDenied:
            messagebox.showerror("Access Denied", "Run as Administrator to change priority.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _search_online(self):
        if not self._selected_pid:
            return
        try:
            p = psutil.Process(self._selected_pid)
            name = p.name()
            import webbrowser
            webbrowser.open(f"https://www.google.com/search?q={name}+process+windows")
        except Exception:
            pass

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
# PERFORMANCE TAB  — graph-free live numeric dashboard
# ═══════════════════════════════════════════════════════════════════════════════

class PerformanceTab(ctk.CTkFrame):
    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._num_cores   = psutil.cpu_count(logical=True) or 1
        self._net_prev    = None
        self._disk_prev   = None
        self._boost_mhz   = None   # fetched once from WMI
        self._all_widgets = []     # for repaint
        self._build_ui()
        # Fetch boost clock in background
        threading.Thread(target=self._fetch_boost_clock, daemon=True).start()

    def _fetch_boost_clock(self):
        rc, out = run_ps("(Get-WmiObject Win32_Processor).MaxClockSpeed")
        if rc == 0 and out.strip().isdigit():
            self._boost_mhz = int(out.strip())

    def _card(self, parent, title, accent_key="accent", **kw):
        f = ctk.CTkFrame(parent, fg_color=T["bg_card"], corner_radius=10, **kw)
        lbl = ctk.CTkLabel(f, text=title,
                           font=("Consolas", zf(11), "bold"),
                           text_color=T[accent_key])
        lbl.pack(anchor="w", padx=14, pady=(12, 6))
        self._all_widgets.append(("card_hdr", f, lbl, accent_key))
        return f

    def _stat_block(self, parent, label, col_key="fg_dim"):
        """Returns (value_label,). Call value_label.configure(text=...) to update."""
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side="left", padx=14, pady=(0, 14))
        lbl = ctk.CTkLabel(f, text=label,
                           font=("Consolas", zf(9)), text_color=T[col_key])
        lbl.pack(anchor="w")
        val = ctk.CTkLabel(f, text="–",
                           font=("Consolas", zf(14), "bold"),
                           text_color=T["fg_main"])
        val.pack(anchor="w")
        self._all_widgets.append(("stat", lbl, col_key, val))
        return val

    def _build_ui(self):
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)
        self._build_cpu_section()
        self._build_memory_section()
        self._build_net_disk_section()

    # ── CPU ──────────────────────────────────────────────────────────────────

    def _build_cpu_section(self):
        card = self._card(self._scroll, "CPU", "accent")
        card.pack(fill="x", padx=6, pady=(6, 4))

        # Top stat row
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=0)
        self._v_cpu_total  = self._stat_block(top, "Total Usage",  "accent")
        self._v_cpu_freq   = self._stat_block(top, "Current Freq", "fg_dim")
        self._v_cpu_boost  = self._stat_block(top, "Boost Clock",  "fg_dim")
        self._v_cpu_cores  = self._stat_block(top, "Cores / Logical", "fg_dim")

        # Per-core grid — numbers only, no canvas
        cores_hdr = ctk.CTkLabel(card, text="PER-CORE",
                   font=("Consolas", zf(9), "bold"), text_color=T["fg_dim"])
        cores_hdr.pack(anchor="w", padx=14, pady=(4, 2))
        self._all_widgets.append(("lbl", cores_hdr, "fg_dim"))

        self._core_grid = ctk.CTkFrame(card, fg_color="transparent")
        self._core_grid.pack(fill="x", padx=14, pady=(0, 14))
        self._core_vals = []
        cols = min(11, max(4, self._num_cores))
        for i in range(self._num_cores):
            cf = ctk.CTkFrame(self._core_grid, fg_color=T["bg_row"],
                              corner_radius=6, width=64, height=50)
            cf.grid(row=i // cols, column=i % cols, padx=3, pady=3, sticky="nsew")
            cf.pack_propagate(False)
            self._core_grid.columnconfigure(i % cols, weight=1)
            ctk.CTkLabel(cf, text=f"C{i}",
                         font=("Consolas", zf(8)), text_color=T["fg_dim"]
                         ).pack(pady=(4, 0))
            v = ctk.CTkLabel(cf, text="–%",
                             font=("Consolas", zf(10), "bold"),
                             text_color=T["fg_main"])
            v.pack()
            self._core_vals.append((cf, v))
        self._cpu_card = card
        self._cores_hdr = cores_hdr

    # ── Memory ───────────────────────────────────────────────────────────────

    def _build_memory_section(self):
        card = self._card(self._scroll, "MEMORY", "accent2")
        card.pack(fill="x", padx=6, pady=4)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x")
        self._v_mem_used   = self._stat_block(top, "In Use",    "accent2")
        self._v_mem_avail  = self._stat_block(top, "Available", "accent3")
        self._v_mem_pct    = self._stat_block(top, "Usage %",   "fg_dim")
        self._v_mem_total  = self._stat_block(top, "Total",     "fg_dim")
        self._v_swap_used  = self._stat_block(top, "Swap Used", "fg_dim")

        # Composition bar (simple tk.Canvas — kept for visual)
        bar_lbl = ctk.CTkLabel(card, text="COMPOSITION  (In use · Modified · Standby · Free)",
                   font=("Consolas", zf(8)), text_color=T["fg_dim"])
        bar_lbl.pack(anchor="w", padx=14)
        self._all_widgets.append(("lbl", bar_lbl, "fg_dim"))

        self._comp_canvas = tk.Canvas(card, height=18, bg=T["bg_card"],
                                      highlightthickness=0)
        self._comp_canvas.pack(fill="x", padx=14, pady=(2, 14))
        self._comp_segments = []
        self._mem_card = card
        self._bar_lbl  = bar_lbl

    def _draw_comp_bar(self, segments):
        """segments: list of (fraction, color_hex)"""
        c = self._comp_canvas
        c.delete("all")
        w = c.winfo_width()
        if w < 4:
            return
        h = 18
        x = 0
        for frac, col in segments:
            bw = int(frac * w)
            if bw > 0:
                c.create_rectangle(x, 2, x + bw, h - 2, fill=col, outline="")
                x += bw
        c.create_rectangle(0, 0, w - 1, h - 1, outline=T["sep"], width=1)

    # ── Network + Disk ────────────────────────────────────────────────────────

    def _build_net_disk_section(self):
        row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=4)
        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=1)

        net_card = self._card(row, "NETWORK", "net_send")
        net_card.grid(row=0, column=0, padx=(0, 4), sticky="nsew")
        net_top = ctk.CTkFrame(net_card, fg_color="transparent")
        net_top.pack(fill="x")
        self._v_net_send       = self._stat_block(net_top, "Send Rate",    "net_send")
        self._v_net_recv       = self._stat_block(net_top, "Recv Rate",    "net_recv")
        self._v_net_total_s    = self._stat_block(net_top, "Total Sent",   "fg_dim")
        self._v_net_total_r    = self._stat_block(net_top, "Total Recv",   "fg_dim")

        disk_card = self._card(row, "DISK", "disk_read")
        disk_card.grid(row=0, column=1, padx=(4, 0), sticky="nsew")
        disk_top = ctk.CTkFrame(disk_card, fg_color="transparent")
        disk_top.pack(fill="x")
        self._v_disk_read  = self._stat_block(disk_top, "Read Rate",  "disk_read")
        self._v_disk_write = self._stat_block(disk_top, "Write Rate", "disk_write")

        self._net_card  = net_card
        self._disk_card = disk_card

    # ── Update methods ────────────────────────────────────────────────────────

    def update_cpu(self, cpu_total, per_core, freq):
        col = color_for_pct(cpu_total)
        self._v_cpu_total.configure(text=f"{cpu_total:.1f}%", text_color=col)
        if freq:
            self._v_cpu_freq.configure(text=f"{freq.current/1000:.2f} GHz")
        else:
            self._v_cpu_freq.configure(text="N/A")
        if self._boost_mhz:
            self._v_cpu_boost.configure(text=f"{self._boost_mhz/1000:.2f} GHz")
        else:
            self._v_cpu_boost.configure(text="–")
        cores_p = psutil.cpu_count(logical=False) or 1
        cores_t = psutil.cpu_count(logical=True) or 1
        self._v_cpu_cores.configure(text=f"{cores_p} / {cores_t}")

        for i, (cf, v) in enumerate(zip(self._core_vals, per_core)):
            pct = per_core[i]
            c   = color_for_pct(pct)
            v.configure(text=f"{pct:.0f}%", text_color=c)
            cf.configure(fg_color=T["bg_row"])

    def update_memory(self, ram, swap):
        total = ram.total or 1
        in_use_f  = max(0.0, min(1.0, ram.used / total))
        standby_f = getattr(ram, "cached", 0) / total
        free_f    = ram.available / total
        mod_f     = max(0.0, 1.0 - in_use_f - standby_f - free_f)

        col = color_for_pct(ram.percent)
        self._v_mem_used.configure(text=bytes_to_human(ram.used),  text_color=col)
        self._v_mem_avail.configure(text=bytes_to_human(ram.available))
        self._v_mem_pct.configure(text=f"{ram.percent:.0f}%",      text_color=col)
        self._v_mem_total.configure(text=bytes_to_human(ram.total))
        self._v_swap_used.configure(text=bytes_to_human(swap.used))

        self._draw_comp_bar([
            (in_use_f,  T["mem_in_use"]),
            (mod_f,     T["mem_modified"]),
            (standby_f, T["mem_standby"]),
            (free_f,    T["mem_free"]),
        ])

    def update_network(self, counters):
        now = (counters.bytes_sent, counters.bytes_recv)
        if self._net_prev is not None:
            sent_rate = max(0, now[0] - self._net_prev[0]) / 2.5
            recv_rate = max(0, now[1] - self._net_prev[1]) / 2.5
            self._v_net_send.configure(text=bps_to_human(sent_rate))
            self._v_net_recv.configure(text=bps_to_human(recv_rate))
        self._v_net_total_s.configure(text=bytes_to_human(counters.bytes_sent))
        self._v_net_total_r.configure(text=bytes_to_human(counters.bytes_recv))
        self._net_prev = now

    def update_disk(self, disk_io):
        now = (disk_io.read_bytes, disk_io.write_bytes)
        if self._disk_prev is not None:
            read_rate  = max(0, now[0] - self._disk_prev[0]) / 2.5
            write_rate = max(0, now[1] - self._disk_prev[1]) / 2.5
            self._v_disk_read.configure(text=bps_to_human(read_rate))
            self._v_disk_write.configure(text=bps_to_human(write_rate))
        self._disk_prev = now

    def repaint(self):
        for entry in self._all_widgets:
            kind = entry[0]
            if kind == "card_hdr":
                _, card, lbl, acc = entry
                card.configure(fg_color=T["bg_card"])
                lbl.configure(text_color=T[acc], font=("Consolas", zf(11), "bold"))
            elif kind == "lbl":
                _, w, col = entry
                w.configure(text_color=T[col], font=("Consolas", zf(9)))
            elif kind == "stat":
                _, lbl, col, val = entry
                lbl.configure(text_color=T[col], font=("Consolas", zf(9)))
                val.configure(text_color=T["fg_main"], font=("Consolas", zf(14), "bold"))
        # Core cells
        for cf, v in self._core_vals:
            cf.configure(fg_color=T["bg_row"])
            v.configure(font=("Consolas", zf(10), "bold"))
        self._comp_canvas.configure(bg=T["bg_card"])
        self._draw_comp_bar([])


# ═══════════════════════════════════════════════════════════════════════════════
# OPTIMIZER TAB
# ═══════════════════════════════════════════════════════════════════════════════

BLOAT_ITEMS = [
    ("Killer Network Service",        "KillerNetworkService",          None,                                              "Intel Killer – network QoS"),
    ("Killer Analytics Service",      "KillerAnalyticsService",        None,                                              "Intel Killer – analytics/telemetry"),
    ("Killer APS",                    None,                            "\\KillerNetworkingLLC\\KillerAPS",                "Killer app scheduler"),
    ("Intel Driver & Support Asst.",  "DSAService",                    None,                                              "Driver update background service"),
    ("Intel Driver Update",           None,                            "\\Intel\\Intel Driver and Support Assistant",     "Driver update scheduled task"),
    ("Phone Link / Mobile",           None,                            "\\Microsoft\\Windows\\MobilePC\\HotStart",        "Microsoft Phone Link launcher"),
    ("Phone Link Service",            "PhoneExperienceHost",           None,                                              "Phone Link background service"),
    ("Search Indexer",                "WSearch",                       None,                                              "Windows Search indexing (high disk I/O)"),
    ("Xbox Game Bar",                 "XblGameSave",                   None,                                              "Xbox Game Bar save sync"),
    ("Xbox Game Bar Task",            None,                            "\\Microsoft\\XblGameSave\\XblGameSaveTask",       "Xbox save task"),
    ("Windows Error Reporting",       "WerSvc",                        None,                                              "Sends crash data to Microsoft"),
    ("Diagnostics Tracking",          "DiagTrack",                     None,                                              "Connected User Experiences & Telemetry"),
    ("WAP Push Message Routing",      "dmwappushservice",              None,                                              "Device mgmt WAP push router"),
    ("Remote Registry",               "RemoteRegistry",                None,                                              "Allows remote registry access"),
    ("AcerSense Helper",              None,                            "\\Acer\\AcerSense",                               "AcerSense background task"),
    ("QuickPanel",                    None,                            "\\Acer\\QuickPanel",                              "Acer QuickPanel overlay"),
    ("QuickPanel OSD",                "AcerQuickPanelOSD",             None,                                              "Acer OSD service"),
    ("Acersense Service",             "AcerSenseService",              None,                                              "AcerSense service"),
]

POWER_PLANS = [
    ("🔇  Silent / Power Saver",       "a1841308-3541-4fab-bc81-f71556f20b4a"),
    ("⚖  Balanced (recommended)",      "381b4222-f694-41f0-9685-ff5bb260df2e"),
    ("⚡  High Performance",            "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),
    ("🚀  Ultimate Performance (CTT)", "e9a42b02-d5df-448d-aa00-03f14749eb61"),
]

# Color for service status strings
def _status_color(s):
    sl = s.lower()
    if sl in ("running", "automatic", "manual"):
        return T["accent3"]
    if sl in ("disabled", "stopped"):
        return T["danger"]
    return T["fg_dim"]


class OptimizerTab(ctk.CTkFrame):
    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._vars        = {}
        self._status      = {}
        self._status_lbls = {}   # display_name -> CTkLabel (for live color)
        self._all_widgets = []
        self._build_ui()
        threading.Thread(target=self._load_states, daemon=True).start()

    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=T["bg_card"], corner_radius=10, **kw)

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

        sub = ctk.CTkLabel(card,
            text="Controls CPU throttling and fan behaviour. Silent = quiet fans, lower power.\n"
                 "Ultimate Performance (CTT) removes CPU micro-throttling for maximum responsiveness.",
            font=("Consolas", zf(9)), text_color=T["fg_dim"])
        sub.pack(anchor="w", padx=14, pady=(0, 8))
        self._all_widgets.append(("lbl", sub, "fg_dim"))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 8))
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
        self._lbl_power_status.pack(anchor="w", padx=14, pady=(0, 12))
        self._all_widgets.append(("lbl", self._lbl_power_status, "accent3"))

        threading.Thread(target=self._refresh_power_label, daemon=True).start()

    def _set_power(self, guid, label):
        def _do():
            is_ctt = (guid == "e9a42b02-d5df-448d-aa00-03f14749eb61")
            if is_ctt:
                # Check if already present, if not duplicate from High Performance
                ps = (
                    "$list = powercfg /list; "
                    "$exists = $list | Select-String 'e9a42b02-d5df-448d-aa00-03f14749eb61'; "
                    "if (-not $exists) { "
                    "  powercfg /duplicatescheme 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c "
                    "  e9a42b02-d5df-448d-aa00-03f14749eb61 | Out-Null "
                    "}; "
                    "powercfg /setactive e9a42b02-d5df-448d-aa00-03f14749eb61"
                )
                rc, out = run_ps(ps)
            else:
                rc, out = run_ps(f"powercfg /setactive {guid}")
            if rc == 0:
                self._power_status.set(f"✓ Active: {label.split('  ', 1)[-1]}")
            else:
                self._power_status.set(f"✗ Failed (run as Admin?): {out[:80]}")
        threading.Thread(target=_do, daemon=True).start()

    def _refresh_power_label(self):
        rc, out = run_ps("powercfg /getactivescheme")
        if rc == 0 and out:
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
            ps_script = r"""
$before = (Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue
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
$after = (Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue
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
            text="Toggle services and scheduled tasks. Status: green = running, red = stopped/disabled.\n"
                 "Re-enable anytime. Requires Administrator for services.",
            font=("Consolas", zf(9)), text_color=T["fg_dim"], justify="left")
        sub.pack(anchor="w", padx=14, pady=(0, 6))
        self._all_widgets.append(("lbl", sub, "fg_dim"))

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
                               text_color=T["fg_dim"], anchor=anchor,
                               width=0 if expand else 80)
            lbl.pack(side="left", expand=expand, fill="x" if expand else "none")
            self._all_widgets.append(("lbl", lbl, "fg_dim"))

        sep = tk.Frame(card, bg=T["sep"], height=1)
        sep.pack(fill="x", padx=14, pady=(0, 4))
        self._bloat_sep = sep

        self._bloat_rows = []
        for display, svc, task, note in BLOAT_ITEMS:
            self._add_bloat_row(card, display, svc, task, note)

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
        self._all_widgets.append(("btn_danger",  b_off))
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
                              text_color=T["fg_dim"], width=80, anchor="center")
        st_lbl.pack(side="left", padx=4)
        self._status_lbls[display] = (st_var, st_lbl)

        btn = ctk.CTkButton(row, text="Toggle", width=80, height=26,
                            fg_color=T["bg_row"], hover_color=T["bg_row2"],
                            text_color=T["fg_main"], font=("Consolas", zf(9)),
                            command=lambda d=display, s=svc, t=task, sv=st_var:
                                self._toggle_bloat(d, s, t, sv))
        btn.pack(side="left", padx=2)

        self._status[display] = st_var
        self._bloat_rows.append((row, name_lbl, note_lbl, st_lbl, btn))
        self._all_widgets.append(("bloat_row", row, name_lbl, note_lbl, st_lbl, btn))

    def _load_states(self):
        for display, svc, task, _ in BLOAT_ITEMS:
            state = self._query_state(svc, task)
            if display in self._status:
                sv = self._status[display]
                self.after(0, lambda sv=sv, d=display, s=state: self._set_status(sv, d, s))

    def _set_status(self, sv, display, state):
        sv.set(state)
        if display in self._status_lbls:
            _, lbl = self._status_lbls[display]
            lbl.configure(text_color=_status_color(state))

    def _query_state(self, svc, task):
        if svc:
            rc, out = run_ps(f"(Get-Service -Name '{svc}' -ErrorAction SilentlyContinue).StartType")
            if rc == 0 and out:
                return out.strip()
            return "N/A"
        elif task:
            rc, out = run_ps(
                f"(Get-ScheduledTask -TaskPath '*' -TaskName '*' | "
                f"Where-Object {{$_.TaskPath+$_.TaskName -like '*{task.split(chr(92))[-1]}*'}} | "
                f"Select-Object -First 1).State")
            if rc == 0 and out:
                return out.strip()
            return "N/A"
        return "N/A"

    def _toggle_bloat(self, display, svc, task, st_var):
        current = st_var.get()
        enabled = current.lower() not in ("disabled", "ready_disabled", "n/a")
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
            self.after(0, lambda: self._set_status(st_var, display, new_state))
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
            self.after(200, lambda: threading.Thread(
                target=self._load_states, daemon=True).start())
        threading.Thread(target=_do, daemon=True).start()

    # ── Startup Manager  (with enable/disable) ────────────────────────────────

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
            text="Programs registered to launch at login (registry + startup folders).\n"
                 "Disable renames the registry key with a 'disabled_' prefix — reversible.",
            font=("Consolas", zf(9)), text_color=T["fg_dim"], justify="left")
        sub.pack(anchor="w", padx=14, pady=(0, 6))
        self._all_widgets.append(("lbl", sub, "fg_dim"))

        ref_btn = ctk.CTkButton(card, text="↺  Scan Startup Items", height=30, width=180,
                                fg_color=T["bg_row"], hover_color=T["bg_row2"],
                                text_color=T["fg_main"], font=("Consolas", zf(10)),
                                command=self._scan_startup)
        ref_btn.pack(anchor="w", padx=14, pady=(0, 6))
        self._all_widgets.append(("btn_row", ref_btn))

        self._startup_frame = ctk.CTkScrollableFrame(card, fg_color="transparent", height=220)
        self._startup_frame.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkLabel(self._startup_frame,
                     text="Click 'Scan Startup Items' to load…",
                     font=("Consolas", zf(9)), text_color=T["fg_dim"]).pack(padx=8, pady=8)

    def _scan_startup(self):
        for w in self._startup_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self._startup_frame, text="Scanning…",
                     font=("Consolas", zf(9)), text_color=T["fg_dim"]).pack()
        threading.Thread(target=self._do_scan_startup, daemon=True).start()

    def _do_scan_startup(self):
        ps = r"""
$items = @()
$regPaths = @(
  'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run',
  'HKLM:\Software\Microsoft\Windows\CurrentVersion\Run',
  'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run'
)
foreach ($rp in $regPaths) {
  if (Test-Path $rp) {
    $vals = Get-ItemProperty $rp -ErrorAction SilentlyContinue
    $vals.PSObject.Properties | Where-Object {$_.Name -notlike 'PS*'} | ForEach-Object {
      $enabled = $true
      $displayName = $_.Name
      if ($_.Name -like 'disabled_*') { $enabled = $false; $displayName = $_.Name.Substring(9) }
      $items += [PSCustomObject]@{Name=$displayName; RegName=$_.Name; Source='Registry'; RegPath=$rp; Value=$_.Value; Enabled=$enabled}
    }
  }
}
$startupFolders = @(
  [Environment]::GetFolderPath('Startup'),
  [Environment]::GetFolderPath('CommonStartup')
)
foreach ($sf in $startupFolders) {
  if (Test-Path $sf) {
    Get-ChildItem $sf -File | ForEach-Object {
      $items += [PSCustomObject]@{Name=$_.BaseName; RegName=''; Source='Startup Folder'; RegPath=$sf; Value=$_.FullName; Enabled=$true}
    }
  }
}
$items | ConvertTo-Json -Compress
"""
        rc, out = run_ps(ps)
        items = []
        if rc == 0 and out:
            try:
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
            name     = str(item.get("Name", "?"))[:40]
            reg_name = str(item.get("RegName", ""))
            reg_path = str(item.get("RegPath", ""))
            src      = str(item.get("Source", ""))
            val      = str(item.get("Value", ""))[:60]
            enabled  = bool(item.get("Enabled", True))
            is_reg   = src == "Registry"

            row = ctk.CTkFrame(self._startup_frame,
                               fg_color=T["bg_row"] if enabled else T["bg_row2"],
                               corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)

            ctk.CTkLabel(row, text=name,
                         font=("Consolas", zf(10), "bold"),
                         text_color=T["fg_main"] if enabled else T["fg_dim"],
                         anchor="w", width=180).pack(side="left", padx=8, pady=4)
            ctk.CTkLabel(row, text=src,
                         font=("Consolas", zf(8)),
                         text_color=T["accent"], anchor="w", width=110).pack(side="left")

            state_lbl = ctk.CTkLabel(row,
                         text="Enabled" if enabled else "Disabled",
                         font=("Consolas", zf(8), "bold"),
                         text_color=T["accent3"] if enabled else T["danger"],
                         width=70, anchor="center")
            state_lbl.pack(side="left", padx=4)

            if is_reg and reg_name and reg_path:
                tog_text = "Disable" if enabled else "Enable"
                tog_btn = ctk.CTkButton(row, text=tog_text, width=70, height=26,
                    fg_color=T["danger"] if enabled else T["accent3"],
                    hover_color=T["bg_row2"],
                    text_color=T["fg_bright"], font=("Consolas", zf(9)),
                    command=lambda rn=reg_name, rp=reg_path, en=enabled,
                                   r=row, sl=state_lbl:
                        self._toggle_startup(rn, rp, en, r, sl))
                tog_btn.pack(side="right", padx=8, pady=4)

    def _toggle_startup(self, reg_name, reg_path, currently_enabled, row_widget, state_lbl):
        def _do():
            if currently_enabled:
                new_name = f"disabled_{reg_name}"
                run_ps(f"Rename-ItemProperty -Path '{reg_path}' "
                       f"-Name '{reg_name}' -NewName '{new_name}' -ErrorAction SilentlyContinue")
            else:
                # Strip "disabled_" prefix
                orig = reg_name[9:] if reg_name.startswith("disabled_") else reg_name
                run_ps(f"Rename-ItemProperty -Path '{reg_path}' "
                       f"-Name '{reg_name}' -NewName '{orig}' -ErrorAction SilentlyContinue")
            # Re-scan to refresh
            self.after(300, self._scan_startup)
        threading.Thread(target=_do, daemon=True).start()

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
                note_lbl.configure(text_color=T["fg_dim"],  font=("Consolas", zf(8)))
                st_lbl.configure(font=("Consolas", zf(9)))
                btn.configure(fg_color=T["bg_row"], hover_color=T["bg_row2"],
                              text_color=T["fg_main"], font=("Consolas", zf(9)))
        # Re-apply status colors
        for display, (sv, lbl) in self._status_lbls.items():
            lbl.configure(text_color=_status_color(sv.get()))
        for b in self._power_btns:
            b.configure(fg_color=T["bg_row"], hover_color=T["bg_row2"],
                        text_color=T["fg_main"], font=("Consolas", zf(10)))
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
        self._is_dark    = False
        self._running    = True
        self._active_tab = "optimizer"

        ctk.set_appearance_mode("light")
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
            right_bar, text="🌙  Dark",
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
            active = (tab_id == "optimizer")
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

        self._switch_tab("optimizer")

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
            ("📋  Export Report",       self._export_report),
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
            self._sb, text="Ctrl +/−  zoom  ·  Ctrl+0  reset  ·  Right-click process for options",
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
            self._update_disk_sidebar()
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

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        self._is_dark = not self._is_dark
        T.update(DARK if self._is_dark else LIGHT)
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

        icon = "☀  Light" if self._is_dark else "🌙  Dark"
        self._theme_btn.configure(text=icon, fg_color=T["toggle_bg"],
                                   hover_color=T["bg_row"], text_color=T["fg_dim"],
                                   font=("Consolas", zf(10)))

        self._zoom_frame.configure(fg_color=T["bg_row"])
        self._lbl_zoom.configure(text=f"{ZOOM_LEVELS[_zoom_idx]}pt",
                                  font=("Consolas", zf(10)),
                                  text_color=T["fg_dim"])
        for btn in (self._btn_zoom_in, self._btn_zoom_out):
            btn.configure(fg_color="transparent",
                          hover_color=T["bg_row2"],
                          text_color=T["fg_main"],
                          font=("Consolas", zf(14), "bold"))

        for tid, btn in self._tab_btns.items():
            active = (tid == self._active_tab)
            btn.configure(
                fg_color=T["accent"] if active else T["bg_card"],
                text_color=T["bg_deep"] if active else T["fg_dim"],
                font=("Consolas", zf(11), "bold"))

        self._sb.configure(fg_color=T["bg_card"])
        for w in (self._lbl_status, self._lbl_hint, self._lbl_proc_count):
            w.configure(text_color=T["fg_dim"], font=("Consolas", zf(9)))

        self.perf_tab.repaint()
        self.proc_table.repaint()
        self.opt_tab.repaint()

        self._disk_card_p.configure(fg_color=T["bg_card"])
        self._lbl_disk_p.configure(text_color=T["fg_dim"],
                                    font=("Consolas", zf(10), "bold"))
        self._qa_card.configure(fg_color=T["bg_card"])
        self._lbl_qa.configure(text_color=T["fg_dim"],
                                font=("Consolas", zf(10), "bold"))
        for b in self._qa_btns:
            b.configure(fg_color=T["bg_row"], hover_color=T["bg_row2"],
                        text_color=T["fg_main"], font=("Consolas", zf(10)))
        if self._active_tab == "processes":
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
        cpu_total = psutil.cpu_percent(interval=1.0)
        per_core  = psutil.cpu_percent(interval=None, percpu=True)
        ram       = psutil.virtual_memory()
        swap      = psutil.swap_memory()
        freq      = psutil.cpu_freq()
        try:
            net = psutil.net_io_counters()
        except Exception:
            net = None
        try:
            disk_io = psutil.disk_io_counters() if self._active_tab == "performance" else None
        except Exception:
            disk_io = None
        self.after(0, lambda: self._update_perf(cpu_total, per_core, ram, swap, freq, net, disk_io))
        self.after(2500, self._poll_perf)

    def _update_perf(self, cpu_total, per_core, ram, swap, freq, net, disk_io):
        self._lbl_time.configure(text=datetime.now().strftime("%H:%M:%S  %d %b %Y"))
        if self._active_tab == "performance":
            self.perf_tab.update_cpu(cpu_total, per_core or [], freq)
            self.perf_tab.update_memory(ram, swap)
            if net:
                self.perf_tab.update_network(net)
            if disk_io:
                self.perf_tab.update_disk(disk_io)
        self._lbl_status.configure(text=f"Updated: {datetime.now().strftime('%H:%M:%S')}")

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
        self.after(6000, self._poll_procs)

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
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    app = SysOptimizer()
    app.protocol("WM_DELETE_WINDOW", app.on_close)

    # Fixed mousewheel scroll — targets CTK _parent_canvas with 3× multiplier
    def _on_mousewheel(event):
        widget = event.widget
        while widget:
            # CTK scrollable frames expose _parent_canvas
            canvas = getattr(widget, "_parent_canvas", None)
            if canvas and hasattr(canvas, "yview_scroll"):
                canvas.yview_scroll(int(-3 * (event.delta / 120)), "units")
                return
            if hasattr(widget, "yview_scroll") and getattr(widget, "winfo_class", lambda: "")() == "Canvas":
                widget.yview_scroll(int(-3 * (event.delta / 120)), "units")
                return
            widget = getattr(widget, "master", None)

    app.bind_all("<MouseWheel>", _on_mousewheel)
    app.mainloop()
