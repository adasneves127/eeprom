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
            [psg.Button('Edit'), psg.Push(), psg.Button('Write'), psg.Push(), psg.Button('Exit')]]
        self.window = psg.Window('HelloWorld', layout, size=(850,710))
        self.isValidData = False
        self.raw_data = None

    def parse_result(self, result: str):
        with tempfile.TemporaryDirectory() as dir:
            with open(dir + "/img.bin", 'wb') as f:
                bin_data = base64.b64decode(result)
                self.raw_data = bin_data
                f.write(bin_data)
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
            proc = subprocess.Popen(["/usr/bin/hexdump", "-C", dir + "/img.bin"], stdout=subprocess.PIPE)
        
            output = proc.stdout.read().decode()
            self.window['output'].update(value=output)
                
    
    def __call__(self):
        while True:
            event, vals = self.window.read()
            # print(event, vals)
            if event in (None, 'Exit'):
                break
            if event == 'Get URL':
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
            if event == "Edit" and self.isValidData:
                self.open_hexedit()