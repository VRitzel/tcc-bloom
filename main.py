import tkinter as tk
from tkinter import ttk

from analysis import CurriculumProcessor
from frames.import_frame import ImportFrame
from frames.loading_frame import LoadingFrame, clean_directory
from frames.topic_frame import TopicReviewFrame
from frames.result_frame import ResultFrame

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
)

log = logging.getLogger("genese")

class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Ferramenta de Bloom")
        self.geometry("800x600")

        self.final_curriculum_data = []
        self.final_learning_path = []

        self.processor = CurriculumProcessor(spacy_model="pt_core_news_lg")

        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (ImportFrame, LoadingFrame, TopicReviewFrame, ResultFrame):
            frame_name = F.__name__
            frame = F(master=container, controller=self)
            self.frames[frame_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("ImportFrame")

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()

        if frame_name == "TopicReviewFrame":
            frame.refresh_data(self.final_curriculum_data)
        elif frame_name == "ResultFrame":
            frame.refresh_data(self.final_learning_path)

    def start_process(self, imported_files):
        self.final_curriculum_data = []
        self.frames["LoadingFrame"].start_extraction(imported_files)
        self.show_frame("LoadingFrame")

    def extraction_finished(self, processed_curriculum):
        log.info("Extração de texto concluída.")
        self.final_curriculum_data = processed_curriculum
        self.show_frame("TopicReviewFrame")

    def generate_learning_path(self):
        self.final_learning_path = self.processor.generate_learning_path(self.final_curriculum_data)
        self.show_frame("ResultFrame")
    
    def reprocess_curriculum(self, threshold):
        raw = getattr(self.processor, "last_raw_topics", None)
        if not raw:
            return False, "Nenhum material processado nesta sessão."

        filtered, content_map = self.processor.process_curriculum_topics(
            list(raw), threshold=threshold
        )
        data = self.processor.run_bloom_classification(filtered, content_map)

        self.final_curriculum_data = data
        self.frames["TopicReviewFrame"].refresh_data(data)
        return True, f"{len(data)} tópicos com limiar {threshold:.2f}."



# root.mainloop()


if __name__ == "__main__":
    clean_directory()
    app = MainApplication()
    app.mainloop()
