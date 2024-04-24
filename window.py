from PySimpleGUI import Text, Button, Multiline, Push, Input, Window,popup_get_file, Combo
import requests
import base64
import tempfile
import subprocess


class GUI_Interface:
    def __init__(self):
        layout = [
            [Text("Base64 EEPROM Image URL"), Input(key="url"), 
             Button("Get URL"), Combo([], key="devices")],
            [Multiline(size=(None, 33),font=('Courier New', 12), 
                           key="output")],
            [
                Button('Read'),Button('Write'),Button("Erase"),
                Push(), Button('Edit'), Push(), Button('Open'), Button("Save"),
                Push(), Button('Exit')]]
        self.window = Window('EPROM IDE', layout, size=(870,730), finalize=True)
        self.isValidData = False
        self.raw_data = None
        self.get_devices()
        self.device_choice = "AT28C256"

    def get_devices(self):
        proc = subprocess.Popen(["/usr/local/bin/minipro", "-l"], stdout=subprocess.PIPE)
        devices = proc.stdout.read().decode().split("\n")
        valid_devices = []
        for device in devices:
            if device.startswith("AT28C") or device.startswith("AT27C"):
                valid_devices.append(device)

        self.window['devices'].update(values=valid_devices, value="AT28C256")

    def parse_result(self, result: str):
        with tempfile.TemporaryDirectory() as dir:
            with open(dir + "/img.bin", 'wb') as f:
                bin_data = base64.b64decode(result)
                self.raw_data = bin_data
                f.write(bin_data)
            self.update_from_raw()
                
    def update_from_raw(self):
        with tempfile.TemporaryDirectory() as dir:
            with open(dir + "/img.bin", 'wb') as f:
                f.write(self.raw_data)
            proc = subprocess.Popen(["/usr/bin/hexdump", "-C", dir + "/img.bin"], stdout=subprocess.PIPE)
            
            output = proc.stdout.read().decode()
            self.window['output'].update(value=output)
    
    def open_hexedit(self):
        with tempfile.TemporaryDirectory() as dir:
            with open(dir + "/img.bin", 'wb') as f:
                f.write(self.raw_data)
            print("Waiting for user to edit file")
            proc = subprocess.Popen(["/usr/bin/xterm", "-e", "/usr/bin/hexedit", dir + "/img.bin"], stdout=subprocess.PIPE)
            proc.communicate()
            print("File closed!")
            with open(dir + "/img.bin", 'rb') as f:
                bin_data = f.read()
                self.raw_data = bin_data

            self.update_from_raw()
    
    def writeEEPROM(self):
        with tempfile.TemporaryDirectory() as dir:
            with open(dir + "/img.bin", 'wb') as f:
                f.write(self.raw_data)
            proc = subprocess.Popen(["/usr/bin/xterm", "-e", "/usr/local/bin/minipro", "-p", self.device_choice, '-w', dir + "/img.bin", '-s'])
            proc.communicate()
    
    def readFile(self,vals):
        print(vals)
        filename = popup_get_file("Open a File", no_window=True,
                                      file_types=(
                                          ("Binary File", "*.bin"),
                                          ("Text File", "*.txt")
                                      ))
        if filename is None:
            return
        
        if(filename.endswith(".txt")):
            with open(filename,"r") as f:
                binbuffer=f.read().split("\n")[:-1]
                print(binbuffer)
                self.raw_data=b""
                for b in binbuffer:
                    bchar = chr(int(b,16))
                    self.raw_data+=bchar.encode()
        else:
            with open(filename,"rb") as f:
                self.raw_data=f.read()
        self.update_from_raw()
        self.isValidData = True


    def readEEPROM(self):
        with tempfile.TemporaryDirectory() as dir:
            proc = subprocess.Popen(["/usr/bin/xterm", "-e", "/usr/local/bin/minipro", "-p", self.device_choice, '-r', dir + "/img.bin"])   
            proc.communicate()

            with open(dir + "/img.bin", 'rb') as f:
                self.raw_data = f.read()
            self.update_from_raw()
            self.isValidData = True
    

    def save_buffer(self):
        filename = popup_get_file("Open a File", no_window=True,
                                      file_types=(
                                          ("Binary File", "*.bin"),
                                          ("Text File", "*.txt")
                                      ),
                                      save_as=True)
        if filename is None or self.raw_data is None:
            return
        
        if(filename.endswith(".txt")):
            with open(filename,"w") as f:
                    f.writelines([
                        hex(x)[2:]
                        for x in self.raw_data
                    ])
        else:
            with open(filename,"wb") as f:
                f.write(self.raw_data)

    def eraseEEPROM(self):
        proc = subprocess.Popen(["/usr/bin/xterm", "-e", "/usr/local/bin/minipro", "-p", self.device_choice, '-E'])   
        proc.communicate()

    def __call__(self):
        while True:
            event, vals = self.window.read()
            self.device_choice = vals['devices']
            if event in (None, 'Exit'):
                break
            elif event == 'Get URL':
                url: str = vals['url']
                split_url = url.split('/')
                if split_url[0] not in ('http:','https:'):
                    self.window['output'].update(value="No scheme provided for web get")
                    continue
                else:
                    self.isValidData = True
                if 'pastebin.com' in url and "raw" not in url:
                    split_url.insert(3, "raw")
                url = "/".join(split_url)
                self.parse_result(requests.get(url).text)
            elif event == "Edit" and self.isValidData:
                self.open_hexedit()
            elif event == "Write" and self.isValidData:
                self.writeEEPROM()
            elif event == "Read":
                self.readEEPROM()
            elif event == "Save":
                self.save_buffer(vals)
            elif event == "Open":
                self.readFile(vals)
            elif event == "Erase":
                self.eraseEEPROM()
