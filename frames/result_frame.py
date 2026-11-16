import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from analysis import BLOOM_ORDER
from report_export import export_to_csv, export_to_pdf


class ResultFrame(ttk.Frame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.current_learning_path = []
        self.current_report = {}

        ttk.Label(self, text="Roteiro de Aprendizagem Gerado", font=("Segoe UI", 14, "bold")).pack(pady=10)

        self.summary_label = ttk.Label(self, text="", font=("Segoe UI", 10), justify="left")
        self.summary_label.pack(fill="x", padx=10, pady=(0, 10))

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Posição", "Nível Bloom", "Título"),
            show="headings"
        )

        self.tree.heading("Posição", text="#", anchor=tk.W)
        self.tree.heading("Nível Bloom", text="Nível Bloom", anchor=tk.W)
        self.tree.heading("Título", text="Título do Tópico", anchor=tk.W)

        self.tree.column("Posição", width=50, stretch=tk.NO)
        self.tree.column("Nível Bloom", width=150, stretch=tk.NO)
        self.tree.column("Título", width=450)

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(pady=10)

        ttk.Button(buttons_frame, text="Voltar para Revisão", command=lambda: self.controller.show_frame("TopicReviewFrame")).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Exportar CSV", command=self.export_csv).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Exportar PDF", command=self.export_pdf).pack(side="left", padx=5)

    def _level_label(self, topic):
        bloom_map = topic.get("bloom_level", {})
        if bloom_map and any(density > 0.0 for density in bloom_map.values()):
            dominant_level = max(bloom_map, key=bloom_map.get)
            return f"N{BLOOM_ORDER.get(dominant_level, '?')} · {dominant_level}"
        return "N/A"

    def refresh_data(self, learning_path):
        self.current_learning_path = learning_path or []
        self.current_report = self.controller.processor.build_analytics_report(self.current_learning_path)

        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.current_learning_path:
            self.tree.insert("", "end", values=("", "", "Nenhum tópico no roteiro."))
            self.summary_label.configure(text="")
            return

        for topic in self.current_learning_path:
            position = topic.get("path_position", "N/A")
            title = topic.get("title", "N/A")
            self.tree.insert("", "end", values=(position, self._level_label(topic), title))

        report = self.current_report
        distribution_text = " | ".join(
            f"{level} ({report['distribution'].get(level, 0)})"
            for level in sorted(BLOOM_ORDER, key=BLOOM_ORDER.get)
        )

        partes = [f"Distribuição: {distribution_text}"]

        total = report.get("total_topics") or 0
        nao_classificados = report.get("unclassified_count") or 0
        if nao_classificados:
            percentual = (nao_classificados / total * 100) if total else 0.0
            partes.append(
                f"Não classificados: {nao_classificados} de {total} ({percentual:.0f}%)"
            )

        if report["missing_levels"]:
            partes.append("Lacunas: " + ", ".join(report["missing_levels"]))
        else:
            partes.append("Todos os seis níveis receberam ao menos um tópico.")

        self.summary_label.configure(text="\n".join(partes))

    def export_csv(self):
        if not self.current_learning_path:
            messagebox.showwarning("Exportar CSV", "Não há roteiro gerado para exportar.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Exportar roteiro como CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not file_path:
            return

        export_to_csv(self.current_learning_path, file_path)
        messagebox.showinfo("Exportar CSV", f"Relatório exportado para:\n{file_path}")

    def export_pdf(self):
        if not self.current_learning_path:
            messagebox.showwarning("Exportar PDF", "Não há roteiro gerado para exportar.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Exportar roteiro como PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if not file_path:
            return

        export_to_pdf(self.current_learning_path, self.current_report, file_path)
        messagebox.showinfo("Exportar PDF", f"Relatório exportado para:\n{file_path}")
