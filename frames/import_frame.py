import os
import tkinter as tk
from tkinter import ttk, filedialog
import logging
log = logging.getLogger("genese")

class ScrolledFrame(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.inner_frame = ttk.Frame(self.canvas)
        self._window = self.canvas.create_window((0,0), window = self.inner_frame, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._window, width=e.width))

    # def _on_frame_configure(self, event):
    #     canvas_width = self.winfo_width()
    #     self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=canvas_width)

    # def update_scrollbar_visibility(self):
    #     self.canvas.yview_moveto(0) 
        
    #     y_scroll_data = self.scrollbar.get()

    #     if y_scroll_data == (0.0, 1.0):
    #         self.scrollbar.pack_forget()
    #         self.canvas.configure(yscrollcommand=None)
    #     else:
    #         self.scrollbar.pack(side="right", fill="y")
    #         self.canvas.configure(yscrollcommand=self.scrollbar.set)

class FileItemWidget(ttk.Frame):
    def __init__(self, master, file_path, on_remove_callback, **kwargs):
        super().__init__(master, padding=5, relief="solid", borderwidth=1, **kwargs)

        filename_full = os.path.basename(file_path)
        filename, extension = os.path.splitext(filename_full)

        ttk.Label(self, text=filename, font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)

        ttk.Label(self, text=f"[{extension.upper()}]", foreground="#007bff").pack(side="left", padx=5)

        ttk.Button(self, text="X", width=3, command=lambda: on_remove_callback(file_path)).pack(side="right", expand=False)

        

class FileListView(ttk.Frame):
    def __init__(self, master, on_add, on_remove, **kwargs):
        super().__init__(master, **kwargs)

        self.on_add_callback = on_add
        self.on_remove_callback = on_remove

        self.scrolled_container = ScrolledFrame(self)
        self.scrolled_container.pack(fill="both", expand=True)

        self.list_container = self.scrolled_container.inner_frame

    def add_file(self, file_path):
        was_added = self.on_add_callback(file_path)

        if not was_added:
            return
        
        # self.files.append(file_path)

        item_widget = FileItemWidget(self.list_container, file_path, on_remove_callback=lambda path: self.on_remove_callback(path, item_widget))
        item_widget.pack(fill="x", pady=2, padx=5)


        # self.scrolled_container.canvas.configure(scrollregion=self.scrolled_container.canvas.bbox("all"))
        
        # self.list_container.update_idletasks()

        # self.scrolled_container.update_scrollbar_visibility()

class ImportFrame(ttk.Frame):
    def __init__(self, master, controller,  **kwargs):
        super().__init__(master, **kwargs)
        
        self.controller = controller
        self.imported_files = []
        self._create_widgets()
    
    def _check_read_files_button(self):
        new_state = "normal" if len(self.imported_files) > 0 else "disabled"
        self.button_read_files["state"] = new_state  

    def _add_file_to_list(self, file_path):
        if file_path not in self.imported_files:
            self.imported_files.append(file_path)
            self._check_read_files_button()
            return True
        return False

    def _remove_file_from_list(self, file_path, item_widget):
        if file_path in self.imported_files:
            self.imported_files.remove(file_path)
            item_widget.destroy()
            self._check_read_files_button()
    
    def read_files(self):
        log.info(f"Prosseguindo com {self.imported_files}")

        self.controller.start_process(self.imported_files)

    def _create_widgets(self):
        label_title =  ttk.Label(self, text="Tela de Importação", font=("Segoe UI", 14, "bold"))
        label_title.pack(pady=10)

        self.button_import = ttk.Button(self, text="Importar arquivo", command=self.import_file)
        self.button_import.pack(pady=5)

        self.button_read_files = ttk.Button(self, text="Prosseguir", command=self.read_files, state="disabled")
        self.button_read_files.pack(pady=5)

        self.file_list_view = FileListView(self, self._add_file_to_list, self._remove_file_from_list)
        self.file_list_view.pack(fill="both", expand=True, padx=10, pady=10)


        # frame_file_container = tk.Frame(self)
        # frame_file_container.pack(fill="both", expand=True)

        # canvas = tk.Canvas(frame_file_container)
        # canvas.pack(side="left", fill="both", expand=True)

        # scrollbar = ttk.Scrollbar(frame_file_container, orient="vertical", command=canvas.yview)

        # self.frame_file_list = tk.Frame(canvas)
        # canvas.create_window((0,0), window=self.frame_file_list, anchor="nw")

        # canvas.configure(yscrollcommand=scrollbar.set)
        # self.frame_file_list.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # scrollbar.pack(side="right", fill="y")
        # self.label_file = ttk.Label(self, text="Nenhum arquivo selecionado")
        # self.label_file.pack(pady=5)

        # self.button_proceed = ttk.Button(self, text="Prosseguir", command=self.proceed)

    def import_file(self):
        path = filedialog.askopenfilename(
            title="Selecione um arquivo",
            filetypes=[("All files", "*.*"), ("PDF files", "*.pdf"), ("Text files", "*.txt")]
        )

        # for widget in self.frame_file.winfo_children():
        #     widget.destroy()
        if path:
            self.file_list_view.add_file(path)
        
    # def proceed
    
