# src/ui_components.py
from tkinter import ttk

class ScrollableTreeview(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.vscroll = ttk.Scrollbar(self, orient="vertical")
        self.hscroll = ttk.Scrollbar(self, orient="horizontal")
        self.tree = ttk.Treeview(
            self,
            yscrollcommand=self.vscroll.set,
            xscrollcommand=self.hscroll.set
        )
        self.vscroll.config(command=self.tree.yview)
        self.hscroll.config(command=self.tree.xview)
        self.vscroll.grid(row=0, column=1, sticky="ns")
        self.hscroll.grid(row=1, column=0, sticky="ew")
        self.tree.grid(row=0, column=0, sticky="nsew")