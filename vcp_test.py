import tkinter as tk
from tkinter import ttk, N, W, E, S, messagebox
from serial.tools.list_ports import comports
from serial.serialutil import SerialException
from serial import Serial
from threading import Thread
from queue import Queue

class SerialCommTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Comm Tester")

        #  cf for config frame
        cf = ttk.Frame(self.root)
        cf.grid(row=0, column=0, sticky=(N, E, W, S))
        cf['borderwidth'] = 2
        cf['relief'] = 'sunken'
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.serial_handler = None
        self.comm_settings = dict(port=None,
                                  baud='19200',
                                  size='8 bits',
                                  parity='N',
                                  stop='1')

        ttk.Label(cf, width=15, text='Port:').grid(row=0,
                                                   column=0,
                                                   sticky=(E, W))

        cbb_port = ttk.Combobox(cf, width=30, state='readonly')
        cbb_port.configure(postcommand=lambda: cbb_port.configure(values=comports()))
        cbb_port.grid(row=0, column=1, sticky=(E, W))
        cbb_port.bind("<<ComboboxSelected>>", 
                      lambda event: self.cbb_selected(event=event,
                                                      name="port",
                                                      cbox=cbb_port))

        ttk.Label(cf, width=15, text='Baud Rate:').grid(row=1, column=0, sticky=(E, W))
        cbb_baud = ttk.Combobox(cf, width=30, state='readonly',
                                values=[1200, 2400, 4800, 9600, 19_200, 38_400, 57_600, 115_200, 230_400, 460_800, 921_600])
        cbb_baud.grid(row=1, column=1, sticky=(E, W))
        cbb_baud.current(4)
        cbb_baud.bind("<<ComboboxSelected>>", lambda event: self.cbb_selected(event=event,
                                                                              name="baud",
                                                                              cbox=cbb_baud))

        ttk.Label(cf, width=15, text='Bytesize:').grid(row=2,
                                                       column=0,
                                                       sticky=(E, W))
        
        cbb_size = ttk.Combobox(cf, width=30, state='readonly', values=['5 bits', '6 bits', '7 bits', '8 bits'])
        cbb_size.grid(row=2, column=1, sticky=(E, W))
        cbb_size.current(3)
        cbb_size.bind("<<ComboboxSelected>>", lambda event: self.cbb_selected(event=event,
                                                                              name="size",
                                                                              cbox=cbb_size))

        ttk.Label(cf, width=15, text='Parity:').grid(row=3,
                                                     column=0,
                                                     sticky=(E, W))
        cbb_parity = ttk.Combobox(cf, width=30, state='readonly', values=['None', 'Even', 'Odd', 'Mark', 'Space'])
        cbb_parity.grid(row=3, column=1, sticky=(E, W))
        cbb_parity.current(0)
        cbb_parity.bind("<<ComboboxSelected>>", lambda event: self.cbb_selected(event=event,
                                                                                name="parity",
                                                                                cbox=cbb_parity))

        ttk.Label(cf, width=15, text='Stopbit:').grid(row=4, column=0, sticky=(E, W))
        cbb_stop = ttk.Combobox(cf, width=30, state='readonly', values=[1, 1.5, 2])
        cbb_stop.grid(row=4, column=1, sticky=(E, W))
        cbb_stop.current(0)
        cbb_stop.bind("<<ComboboxSelected>>", lambda event: self.cbb_selected(event=event,
                                                                              name="stop",
                                                                              cbox=cbb_stop))

        ttk.Button(cf, text='Connect Port',command=self.connect_serial).grid(row=5,
                                                                             column=0,
                                                                             columnspan=2,
                                                                             sticky=(E, W))


        # transceiver frame
        tf = ttk.Frame(self.root)
        tf.grid(row=0, column=1, sticky=(N, E, W, S))
        tf['borderwidth'] = 2
        tf['relief'] = 'sunken'
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        ttk.Label(tf, text='Enter Tx Message').grid(row=0, column=0, columnspan=2, sticky=W)
        self.str_tx = tk.StringVar()
        ttk.Entry(tf, textvariable=self.str_tx).grid(row=1, column=0, sticky=(W, E))
        

        ttk.Button(tf, text='Send Message', command=self.transmit).grid(row=1, column=1, sticky=(W, E))

        self.str_rx = tk.StringVar()
        ttk.Label(tf, textvariable= self.str_rx).grid(row=2, column=0, columnspan=2)

        for child in cf.winfo_children():
            child.grid_configure(padx=5, pady=5)
        
        for child in tf.winfo_children():
            child.grid_configure(padx=5, pady=5)

        for child in self.root.winfo_children():
            child.grid_configure(padx=2, pady=2)

    def cbb_selected(self, event, name:str, cbox: ttk.Combobox):
        self.comm_settings[name] = cbox.get()

    def connect_serial(self):
        if self.comm_settings['port'] is None:
            self.str_comms.set("Error: No port specified")
            return
        try:
            self.serial_handler = Serial(port=self.comm_settings['port'].split()[0],
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
    
    def transmit(self):
        tx_data = (self.str_tx.get() + "\r").encode()
        print(tx_data)
        self.serial_handler.write(tx_data)

    def receive(self):
        rx_data = self.serial_handler.read_all()
        print("read: ", rx_data)
        try:
            self.str_rx.set(rx_data.decode("utf-8"))
        except UnicodeDecodeError:
            print("decode error")
        self.root.after(200, self.receive)


class ThreadedRx(Thread):
    def __init__(self, queue, serial_handler):
        super().init(self)
        self.queue = queue
        self.serial_handler = serial_handler
        
    def run(self):
        pass


if __name__ == '__main__':
    root_frame = tk.Tk()
    SerialCommTester(root=root_frame)
    root_frame.mainloop()
    pass
