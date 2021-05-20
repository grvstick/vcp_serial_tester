import re
import tkinter as tk
from tkinter import ttk, N, W, E, S, messagebox
from queue import Queue
import sys, traceback
from collections import deque


from serial.tools.list_ports import comports
from serial.serialutil import SerialException
from serial.threaded import ReaderThread, LineReader
from serial import Serial

rx_queue, tx_queue = Queue(), Queue()


class SerialCommTester(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid(row=0, column=0, sticky=(N, E, W, S))
        self.root = parent
        self.root.title("Serial Comm Tester")

        #  cf for config frame
        cf = ttk.LabelFrame(self, text="Configure Comms")
        cf.grid(row=0, column=0, rowspan=2, sticky=(N, E, W, S))
        cf['borderwidth'] = 2
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.serial_handler = None
        self.comm_settings = dict(port=None,
                                  baud='19200',
                                  size='8 bits',
                                  parity='N',
                                  stop='1',
                                  delim=b'\r')

        ttk.Label(cf, width=20, text='Port:').grid(row=0,
                                                   column=0,
                                                   sticky=(E, W))

        cbox_port = ttk.Combobox(cf, width=25, state='readonly')
        cbox_port.configure(postcommand=lambda: cbox_port.configure(values=comports()))
        cbox_port.grid(row=0, column=1, columnspan=2, sticky=(E, W))
        cbox_port.bind("<<ComboboxSelected>>", lambda event: self.cbox_selected(event=event,
                                                                                name="port",
                                                                                cbox=cbox_port))

        ttk.Label(cf, width=15, text='Baud Rate/Byte Size').grid(row=1, column=0, sticky=(E, W))
        cbox_baud = ttk.Combobox(cf, state='readonly',
                                 values=[1200, 2400, 4800, 9600, 19_200, 38_400, 57_600, 115_200, 230_400, 460_800,
                                         921_600])
        cbox_baud.grid(row=1, column=1, sticky=(E, W))
        cbox_baud.current(4)
        cbox_baud.bind("<<ComboboxSelected>>", lambda event: self.cbox_selected(event=event,
                                                                                name="baud",
                                                                                cbox=cbox_baud))

        cbox_size = ttk.Combobox(cf, state='readonly', values=['5 bits', '6 bits', '7 bits', '8 bits'])
        cbox_size.grid(row=1, column=2, sticky=(E, W))
        cbox_size.current(3)
        cbox_size.bind("<<ComboboxSelected>>", lambda event: self.cbox_selected(event=event,
                                                                                name="size",
                                                                                cbox=cbox_size))

        ttk.Label(cf, text='Parity/Stop bit').grid(row=2, column=0, sticky=(E, W))

        cbox_parity = ttk.Combobox(cf, state='readonly', values=['None', 'Even', 'Odd', 'Mark', 'Space'])
        cbox_parity.grid(row=2, column=1, sticky=(E, W))
        cbox_parity.current(0)
        cbox_parity.bind("<<ComboboxSelected>>", lambda event: self.cbox_selected(event=event,
                                                                                  name="parity",
                                                                                  cbox=cbox_parity))

        cbox_stop = ttk.Combobox(cf, state='readonly', values=[1, 1.5, 2])
        cbox_stop.grid(row=2, column=2, sticky=(E, W))
        cbox_stop.current(0)
        cbox_stop.bind("<<ComboboxSelected>>", lambda event: self.cbox_selected(event=event,
                                                                                name="stop",
                                                                                cbox=cbox_stop))

        ttk.Button(cf, text='Connect Port', command=self.connect_serial).grid(row=5,
                                                                              column=0,
                                                                              columnspan=3,
                                                                              sticky=(E, W))

        # transmit frame
        tf = ttk.LabelFrame(self, text="Enter Tx Message")
        tf.grid(row=0, column=1, sticky=(N, E, W, S))
        tf['borderwidth'] = 2
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.str_tx = tk.StringVar()
        tx_entry = ttk.Entry(tf, textvariable=self.str_tx)
        tx_entry.grid(row=0, column=0, sticky=(W, E))
        tx_entry.bind("<Return>", self.transmit)
        tx_btn = ttk.Button(tf, text='Send Message', command=self.transmit)
        tx_btn.grid(row=1, column=0, sticky=(W, E))
        tx_btn.bind("<Return>", self.transmit)

        # receiver frame
        rf = ttk.LabelFrame(self, text="Received Data")
        rf.grid(row=1, column=1, sticky=(N, W, E, S))
        self.str_rx = tk.StringVar()
        ttk.Label(rf, textvariable=self.str_rx).grid(row=2, column=0, columnspan=2)

        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)
            for grandchild in child.winfo_children():
                grandchild.grid_configure(padx=5, pady=5)

    def cbox_selected(self, event, name:str, cbox: ttk.Combobox):
        if name != 'delim':
            self.comm_settings[name] = cbox.get()
        elif cbox.get() == "CR":
            self.comm_settings[name] = b'\r'
        elif cbox.get() == "LF":
            self.comm_settings[name] = b'\n'
        elif cbox.get() == "CRLF":
            self.comm_settings[name] = b'\r\n'
        elif cbox.get() == "NULL":
            self.comm_settings[name] = b'\0'
        

    def connect_serial(self):
        if self.comm_settings['port'] is None:
            messagebox.showinfo("Error", "No port specified")
            return
        try:
            self.serial = Serial(port=self.comm_settings['port'].split()[0],
                                 baudrate=int(self.comm_settings['baud']),
                                 bytesize=int(self.comm_settings['size'][0]),
                                 parity=self.comm_settings['parity'][0],
                                 stopbits=float(self.comm_settings['stop']))
            messagebox.showinfo("Info", "Serial Connection Successful")
            print(self.serial_handler)
            self.root.after(100, self.receive)
            return

        except SerialException as SE:
            messagebox.showerror("Error", str(SE))
            return

    def transmit(self, *args):
        tx_data = (self.str_tx.get() + "\r").encode()
        print(tx_data)
        self.serial_handler.write(tx_data)

    def receive(self):
        if rx_queue.empty() is not True:
            self.str_rx.set(rx_queue.get())
        
        self.root.after(200, self.receive)
    
    # def transmit(self):
    #     tx_data = self.str_tx.get().encode() + self.comm_settings['delim']
    #     print(tx_data)
    #     self.serial_handler.write(tx_data)

    # def receive(self):
    #     rx_data = self.serial_handler.read_all()
    #     print("read: ", rx_data)
    #     try:
    #         self.str_rx.set(rx_data.decode("utf-8"))
    #     except UnicodeDecodeError:
    #         print("decode error")
    #     self.root.after(200, self.receive)


# class ThreadedRx(Thread):
#     def __init__(self, queue, serial_handler):
#         super().init(self)
#         self.queue = queue
#         self.serial_handler = serial_handler
        
#     def run(self):
#         pass


class StoreLines(LineReader):
    def __init__(self, terminator):
        self.TERMINATOR = terminator
        
    def connection_made(self, transport):
        super().connection_made(transport)
        print('port opened')


    def handle_line(self, data):
        rx_queue.put(data)
    
    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)
        print('port closed')
    

if __name__ == '__main__':
    root = tk.Tk()
    SerialCommTester(parent=root)
    root.mainloop()
    pass
