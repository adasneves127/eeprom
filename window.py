import PySimpleGUI as psg
import requests
import base64
import tempfile
import subprocess


class GUI_Interface:
    def __init__(self):
        layout = [
            [psg.Text("Base64 EEPROM Image URL"), psg.Input(key="url"), 
             psg.Button("Get URL")],
            [psg.Multiline(size=(None, 33),font=('Courier New', 12), 
                           key="output")],
            [psg.Button('Edit'), psg.Push(), psg.Button('Write'), psg.Push(),
             psg.Button('Open'), psg.FileBrowse(key='Browse', visible=False), psg.Push(),
             psg.Button('Read'), psg.Push(), psg.FileSaveAs("Choose File",file_types=(("Binary Files", "*.bin"),)), psg.Button("Save"), psg.Push(),

             psg.Button('Exit')]]
        self.window = psg.Window('EPROM IDE', layout, size=(870,730))
        self.isValidData = False
        self.raw_data = None

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
            proc = subprocess.Popen(["/usr/bin/xterm", "-e", "/usr/local/bin/minipro", "-p", "AT28C256", '-w', dir + "/img.bin"])
            proc.communicate()
    
    def readFile(self,vals):
#        layout =    [[psg.Input(key='_FILEBROWSE_', enable_events=True, visible=False)],
#            [psg.FileBrowse(target='_FILEBROWSE_')],
#            [psg.OK()],]

#        window = psg.Window('My new window',layout,size=(100,100),modal=True)
#        return
        print(vals)
        filename = ""
        if vals.get('Browse', '') == '':
            print("Please press Browse first")
            filename = psg.popup_get_file("Open a File", no_window=True)
        else:
            filename=vals["Browse"]
        print(vals["Browse"])
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


    def readEEPROM(self):
        with tempfile.TemporaryDirectory() as dir:
            proc = subprocess.Popen(["/usr/bin/xterm", "-e", "/usr/local/bin/minipro", "-p", "AT28C256", '-r', dir + "/img.bin"])
            proc.communicate() 

            with open(dir + "/img.bin", 'rb') as f:
                self.raw_data = f.read()
            self.update_from_raw()
            self.isValidData = True
    

    def save_buffer(self, vals):
        with open(vals['Choose File'], 'wb') as f:
            f.write(self.raw_data)


    def __call__(self):
        while True:
            event, vals = self.window.read()
            print(event)
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
