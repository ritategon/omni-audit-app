"""
OMNI(Orthographic & Marginalia Normalization Integrity Auditor)-Audit Desktop GUI Application (Tkinter - Zero Dependencies)
=================================================================
Author: Dr. Rita Tegon (rita.tegon@usal.es)
Project: An interactive desktop dashboard for running OMNI-Audit on manuscript transcriptions,
visualizing ONI / CER / MPR metrics, inspecting TEI-XML tags, and exporting audit reports.
"""

import sys
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from omni_auditor import OMNIAuditor, TextNormalizer


class OMNIAuditGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("OMNI-Audit v2.0 — Archival Normalization & Marginalia Audit Dashboard")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        # Style Configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colors
        self.NAVY = "#003366"
        self.WHITE = "#FFFFFF"
        self.LIGHT_BG = "#F4F6F9"
        
        self._build_ui()

    def _build_ui(self):
        # --- Top Header Banner ---
        header_frame = tk.Frame(self.root, bg=self.NAVY, height=60)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        
        title_label = tk.Label(
            header_frame, 
            text="OMNI-Audit v2.0: Orthographic & Marginalia Integrity Dashboard",
            font=("Segoe UI", 14, "bold"),
            fg=self.WHITE, bg=self.NAVY,
            padx=15, pady=12
        )
        title_label.pack(side=tk.LEFT)

        subtitle_label = tk.Label(
            header_frame,
            text="Prototype",
            font=("Segoe UI", 9, "italic"),
            fg="#D0E0FF", bg=self.NAVY,
            padx=15
        )
        subtitle_label.pack(side=tk.RIGHT)

        # --- Main Notebook (Tabs) ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Audit Dashboard
        self.tab_dashboard = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_dashboard, text=" Audit Dashboard ")

        # Tab 2: Sample Data Loader
        self.tab_samples = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_samples, text=" Sample Manuscripts ")

        self._build_dashboard_tab()
        self._build_samples_tab()

    def _build_dashboard_tab(self):
        # Split into Left Panel (Inputs) and Right Panel (Results)
        paned = ttk.PanedWindow(self.tab_dashboard, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # --- Left Panel: File Selection & Direct Text Inputs ---
        left_frame = ttk.LabelFrame(paned, text=" Diagnostic Inputs ", padding=10)
        paned.add(left_frame, weight=1)

        # File Pickers
        ttk.Label(left_frame, text="Diplomatic Baseline Text (.txt):", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(5,2))
        dip_file_frame = ttk.Frame(left_frame)
        dip_file_frame.pack(fill=tk.X, pady=(0,5))
        self.entry_dip = ttk.Entry(dip_file_frame)
        self.entry_dip.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(dip_file_frame, text="Browse...", command=lambda: self._browse_file(self.entry_dip)).pack(side=tk.RIGHT)

        ttk.Label(left_frame, text="Datafied / HTR Text (.txt):", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(5,2))
        dat_file_frame = ttk.Frame(left_frame)
        dat_file_frame.pack(fill=tk.X, pady=(0,5))
        self.entry_dat = ttk.Entry(dat_file_frame)
        self.entry_dat.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(dat_file_frame, text="Browse...", command=lambda: self._browse_file(self.entry_dat)).pack(side=tk.RIGHT)

        ttk.Label(left_frame, text="TEI-XML Archive Export (.xml):", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(5,2))
        xml_file_frame = ttk.Frame(left_frame)
        xml_file_frame.pack(fill=tk.X, pady=(0,5))
        self.entry_xml = ttk.Entry(xml_file_frame)
        self.entry_xml.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(xml_file_frame, text="Browse...", command=lambda: self._browse_file(self.entry_xml)).pack(side=tk.RIGHT)

        # Action Buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=15)
        
        btn_run = tk.Button(
            btn_frame, text="▶ RUN OMNI-AUDIT", font=("Segoe UI", 10, "bold"),
            bg="#003366", fg="white", activebackground="#002244", activeforeground="white",
            padx=10, pady=8, command=self._run_audit
        )
        btn_run.pack(fill=tk.X, pady=(0,5))

        btn_load_sample = ttk.Button(btn_frame, text="⚡ Quick Load Included Sample Data", command=self._quick_load_samples)
        btn_load_sample.pack(fill=tk.X)

        # Quick Preview Area
        ttk.Label(left_frame, text="Diplomatic Text Quick Preview:", font=("Segoe UI", 8, "italic")).pack(anchor=tk.W, pady=(10,2))
        self.txt_preview = scrolledtext.ScrolledText(left_frame, height=10, font=("Consolas", 9))
        self.txt_preview.pack(fill=tk.BOTH, expand=True)

        # --- Right Panel: Results & Diagnostic Metrics ---
        right_frame = ttk.LabelFrame(paned, text=" Audit Metrics & Diagnostics ", padding=10)
        paned.add(right_frame, weight=2)

        # Metric Summary Cards
        cards_frame = ttk.Frame(right_frame)
        cards_frame.pack(fill=tk.X, pady=(0,10))

        # ONI Card
        self.card_oni = tk.LabelFrame(cards_frame, text=" ONI Score ", font=("Segoe UI", 9, "bold"), bg="#EBF3FB", padx=10, pady=5)
        self.card_oni.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        self.lbl_oni_val = tk.Label(self.card_oni, text="0.000", font=("Segoe UI", 16, "bold"), bg="#EBF3FB", fg="#003366")
        self.lbl_oni_val.pack()

        # CER Card
        self.card_cer = tk.LabelFrame(cards_frame, text=" CER (Char Error Rate) ", font=("Segoe UI", 9, "bold"), bg="#EBF3FB", padx=10, pady=5)
        self.card_cer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        self.lbl_cer_val = tk.Label(self.card_cer, text="0.00%", font=("Segoe UI", 16, "bold"), bg="#EBF3FB", fg="#003366")
        self.lbl_cer_val.pack()

        # MPR Card
        self.card_mpr = tk.LabelFrame(cards_frame, text=" MPR (Marginalia) ", font=("Segoe UI", 9, "bold"), bg="#EBF3FB", padx=10, pady=5)
        self.card_mpr.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        self.lbl_mpr_val = tk.Label(self.card_mpr, text="100.0%", font=("Segoe UI", 16, "bold"), bg="#EBF3FB", fg="#003366")
        self.lbl_mpr_val.pack()

        # Risk Banner
        self.lbl_risk_banner = tk.Label(
            right_frame, text="STATUS: READY TO AUDIT", font=("Segoe UI", 11, "bold"),
            bg="#D0D0D0", fg="black", pady=6
        )
        self.lbl_risk_banner.pack(fill=tk.X, pady=(0,10))

        # JSON / Report Output Display
        ttk.Label(right_frame, text="Structured Audit Report (JSON Output):", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self.txt_report = scrolledtext.ScrolledText(right_frame, font=("Consolas", 10), bg="#1E1E1E", fg="#D4D4D4")
        self.txt_report.pack(fill=tk.BOTH, expand=True, pady=(2,10))

        # Export Report Button
        ttk.Button(right_frame, text="💾 Export Audit Report JSON...", command=self._export_report).pack(anchor=tk.E)

    def _build_samples_tab(self):
        frame = ttk.Frame(self.tab_samples, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Sample Manuscripts Included in App Package", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(0,10))

        samples_info = (
            "1. sample_diplomatic.txt:\n"
            "   Ground-truth 1584 manuscript text preserving archaic spelling (Thif fcripture wrayten in ye yeare 1584).\n\n"
            "2. sample_datafied.txt:\n"
            "   Modernized HTR output text (This scripture written in the year 1584).\n\n"
            "3. sample_archival_tei.xml:\n"
            "   TEI-P5 XML manuscript document with <add place='margin'>, <del>, and <choice><abbr> tags."
        )

        lbl = tk.Label(frame, text=samples_info, justify=tk.LEFT, font=("Segoe UI", 10), bg="#F8F9FA", anchor="nw", relief=tk.RIDGE, padx=10, pady=10)
        lbl.pack(fill=tk.BOTH, expand=True)

    def _browse_file(self, entry_widget):
        filename = filedialog.askopenfilename()
        if filename:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)

    def _quick_load_samples(self):
        base_dir = os.path.join(os.path.dirname(__file__), "sample_data")
        dip = os.path.join(base_dir, "sample_diplomatic.txt")
        dat = os.path.join(base_dir, "sample_datafied.txt")
        xml = os.path.join(base_dir, "sample_archival_tei.xml")

        if os.path.exists(dip):
            self.entry_dip.delete(0, tk.END)
            self.entry_dip.insert(0, dip)
            with open(dip, "r", encoding="utf-8") as f:
                self.txt_preview.delete("1.0", tk.END)
                self.txt_preview.insert(tk.END, f.read())

        if os.path.exists(dat):
            self.entry_dat.delete(0, tk.END)
            self.entry_dat.insert(0, dat)

        if os.path.exists(xml):
            self.entry_xml.delete(0, tk.END)
            self.entry_xml.insert(0, xml)

        messagebox.showinfo("Samples Loaded", "Loaded sample manuscript files successfully!")

    def _run_audit(self):
        dip_path = self.entry_dip.get().strip()
        dat_path = self.entry_dat.get().strip()
        xml_path = self.entry_xml.get().strip()

        dip_text = ""
        dat_text = ""

        if dip_path and os.path.exists(dip_path):
            with open(dip_path, "r", encoding="utf-8") as f:
                dip_text = f.read()

        if dat_path and os.path.exists(dat_path):
            with open(dat_path, "r", encoding="utf-8") as f:
                dat_text = f.read()

        auditor = OMNIAuditor(dip_text, dat_text)
        report = auditor.generate_full_report(tei_file_path=xml_path if (xml_path and os.path.exists(xml_path)) else None)

        # Update Card Metrics
        oni = report["metrics"]["orthographic_normalization_index_oni"]
        cer = report["metrics"]["character_error_rate_cer"]
        
        xml_audit = report.get("xml_markup_audit", {})
        mpr = xml_audit.get("mpr_percentage", 100.0)

        self.lbl_oni_val.config(text=f"{oni:.4f}")
        self.lbl_cer_val.config(text=f"{cer*100:.2f}%")
        self.lbl_mpr_val.config(text=f"{mpr:.1f}%")

        # Update Risk Banner
        risk = report["risk_assessment"]
        level = risk["risk_level"]
        color_code = risk["color_code"]

        color_map = {
            "GREEN": "#28A745",
            "YELLOW": "#FFC107",
            "ORANGE": "#FD7E14",
            "RED": "#DC3545"
        }
        bg_color = color_map.get(color_code, "#003366")
        fg_color = "black" if color_code == "YELLOW" else "white"

        self.lbl_risk_banner.config(text=f"STATUS: {level}", bg=bg_color, fg=fg_color)

        # Update JSON Report Text Display
        self.txt_report.delete("1.0", tk.END)
        self.txt_report.insert(tk.END, json.dumps(report, indent=2, ensure_ascii=False))

    def _export_report(self):
        content = self.txt_report.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("No Report", "Please run an audit first!")
            return

        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Exported", f"Audit report saved to: {filename}")


def main():
    root = tk.Tk()
    app = OMNIAuditGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
