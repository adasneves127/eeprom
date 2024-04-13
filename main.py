# import PySimpleGUI as psg
# import requests
# import base64
# layout = [[psg.Text("Base64 EEPROM Image URL"), psg.Input(key="url"), psg.Button("Get URL")],[psg.Multiline(size=(None, 10),font=('Courier New', 12), key="output")], [psg.Push(), psg.Button('Exit')]]
# window = psg.Window('HelloWorld', layout, size=(715,715))
# while True:
#     event, values = window.read()
#     print(event, values)
#     if event in (None, 'Exit'):
#         break
#     if event == 'Get':
#         values["output"] = requests.get(values['url']).text
        
# window.close()

from window import GUI_Interface

x = GUI_Interface()
x()