import tkinter as tk
from tkinter import ttk

from analysis import DOMINANCE_RATIO, MIN_DENSITY

class TopicReviewFrame(ttk.Frame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller

        ttk.Label(self, text="Revisão do Currículo Processado", font=("Segoe UI", 14, "bold")).pack(pady=10)

        options_frame = ttk.Frame(self)
        options_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(options_frame, text="Limiar de Similaridade (0.0-1.0):").pack(side="left")
        self.threshold_entry = ttk.Entry(options_frame, width=5)
        self.threshold_entry.insert(0, "0.6")
        self.threshold_entry.pack(side="left", padx=5)

        self.reprocess_button = ttk.Button(options_frame, text="Re-processar", command=self.on_reprocess)
        self.reprocess_button.pack(side="left")

        self.status_label = ttk.Label(options_frame, text="")
        self.status_label.pack(side="left", padx=10)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("Nível", "Título", "Bloom (Sugerido)", "Densidade (%)"),
            show="headings"
        )

        self.tree.heading("Nível", text="Nível", anchor=tk.W)
        self.tree.heading("Título", text="Título do Tópico", anchor=tk.W)
        self.tree.heading("Bloom (Sugerido)", text="Bloom (Sugerido)", anchor=tk.W)
        self.tree.heading("Densidade (%)", text="Densidade (%)", anchor=tk.W)

        self.tree.column("Nível", width=50, stretch=tk.NO)
        self.tree.column("Título", width=400)
        self.tree.column("Bloom (Sugerido)", width=120, stretch=tk.NO)
        self.tree.column("Densidade (%)", width=120, stretch=tk.NO)

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(pady=10)

        ttk.Button(buttons_frame, text="Voltar para Importação", command=lambda: self.controller.show_frame("ImportFrame")).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Gerar Roteiro de Aprendizagem", command=self.controller.generate_learning_path).pack(side="left", padx=5)
    
    def refresh_data(self, curriculum_data):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not curriculum_data:
            self.tree.insert("", "end", values=("", "Nenhum tópico encontrado.", "", ""))
            return
        
        for topic in curriculum_data:
            level = topic.get("markdown_level", "N/A")
            title = topic.get("title", "N/A")
            bloom_map = topic.get("bloom_level", {})

            sugerido = "Não classificado"
            max_density = 0.0

            if bloom_map:
                ranked = sorted(bloom_map.items(), key=lambda kv: kv[1], reverse=True)
                nivel, dens = ranked[0]
                segundo = ranked[1][1] if len(ranked) > 1 else 0.0
                if dens >= MIN_DENSITY and not (segundo > 0.0 and dens < segundo * DOMINANCE_RATIO):
                    sugerido = nivel
                    max_density = dens

            self.tree.insert("", "end", values=(f"H{level}", title, sugerido, f"{max_density:.2f}%"))
    def on_reprocess(self):
        texto = self.threshold_entry.get().strip().replace(",", ".")
        try:
            limiar = float(texto)
        except ValueError:
            self.status_label.config(text="Informe um número entre 0.0 e 1.0.")
            return
        if not 0.0 <= limiar <= 1.0:
            self.status_label.config(text="O limiar deve estar entre 0.0 e 1.0.")
            return

        self.reprocess_button.config(state="disabled")
        self.status_label.config(text="Reprocessando...")
        self.update_idletasks()
        try:
            ok, msg = self.controller.reprocess_curriculum(limiar)
        except Exception as erro:
            msg = f"Falha no reprocessamento: {erro}"
        finally:
            self.reprocess_button.config(state="normal")
        self.status_label.config(text=msg)