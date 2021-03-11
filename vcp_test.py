import tkinter as tk
from tkinter import ttk, N, W, E, S
from serial.tools.list_ports import comports
from serial.serialutil import SerialException
from serial import Serial


class SerialCommTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Comm Tester")
        cf = ttk.Frame(self.root)  # cf for config frame
        cf.grid(row=0, column=0, sticky=(N, E, W, S))
        cf['borderwidth'] = 2
        cf['relief'] = 'sunken'
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.cbb_port = ttk.Combobox(cf, width=50, state='readonly')
        self.cbb_port.configure(postcommand=lambda: self.cbb_port.configure(values=comports()))
        self.cbb_port.grid(row=0, column=0)

if __name__ == '__main__':
    root_frame = tk.Tk()
    SerialCommTester(root=root_frame)
    root_frame.mainloop()
    pass
