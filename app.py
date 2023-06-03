import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
import paho.mqtt.client as mqtt
import json
import socket
import random
from playsound import playsound

class mqttChat:
    # declare variables
    host = "127.0.0.1"
    topic = "0"
    userIP = socket.gethostbyname(socket.gethostname())
    clientID = random.randint(10000, 99999)
    newConn = True
    # declare mqtt client
    client = mqtt.Client()

    def __init__(self, master=None):
        # build ui
        toplevel1 = tk.Tk() if master is None else tk.Toplevel(master)
        toplevel1.configure(height=500, relief="flat", width=650)
        self.serverHost = tk.Label(toplevel1)
        self.serverHost.configure(font="TkDefaultFont", text='Server:')
        self.serverHost.pack(side="top")
        self.entry4 = tk.Entry(toplevel1)
        self.entry4.pack(side="top")
        self.chatID = tk.Label(toplevel1)
        self.chatID.configure(
            justify="left",
            takefocus=False,
            text='Chat ID #:')
        self.chatID.pack(side="top")
        self.entry5 = tk.Entry(toplevel1)
        self.entry5.pack(side="top")
        self.connectBtn = tk.Button(toplevel1)
        self.connectBtn.configure(text='Connect', command=self.connect)
        self.connectBtn.pack(side="top")
        self.chatLog = ScrolledText(toplevel1)
        self.chatLog.configure(insertunfocussed="none", takefocus=False, state='disabled')
        self.chatLog.tag_config('system', foreground='red')
        self.chatLog.tag_config('you', foreground='green')
        self.chatLog.tag_config('people', foreground='blue')
        self.chatLog.pack(side="top")
        self.textMsg = tk.Entry(toplevel1)
        self.textMsg.pack(side="top")
        self.sendMsg = tk.Button(toplevel1)
        self.sendMsg.configure(text='Send', command=self.send)
        self.sendMsg.pack(side="top")

        # Main widget
        self.mainwindow = toplevel1
        self.mainwindow.title("MQTT Chat Client ID: #" + str(self.clientID))

    def run(self):
        self.mainwindow.protocol('WM_DELETE_WINDOW',self.on_close)
        self.mainwindow.mainloop()

    def connect(self):
        self.connectBtn.configure(text='Connecting...')
        # Connect to the MQTT server
        self.host = self.entry4.get()
        self.topic = self.entry5.get()
        self.entry4.configure(state='disabled')
        self.entry5.configure(state='disabled')
        self.client.connect(self.host, 1883, 60)
        # Subscribe to the chatID topic
        subs = [(self.topic,0),(("SYS_" + str(self.clientID)),0)]
        # Set the on_message callback
        self.client.on_message = lambda client, userdata, message: self.onmsg(client, userdata, message, self)
        # Start the MQTT client
        self.client.loop_start()
        self.connectBtn.configure(text='Connected!', state='disabled')
        payload = {
            "sender" : self.clientID,
            "client" : "SYSTEMCONN",
            "msg" : "Client #" + str(self.clientID) +" has connected!"
        }
        payload = json.dumps(payload)
        self.client.publish(self.topic, payload)
        self.client.subscribe(subs)
        payload = {
            "sender" : "SYSTEM",
            "client" : "SYSTEM",
            "msg" : "List of connected Users:"
        }
        payload = json.dumps(payload)
        self.client.publish("SYS_" + str(self.clientID), payload)

    def onmsg(item1, item2, item3, item4, item5):
        try:
            received_message = item4.payload.decode("utf-8")
            
            payload = json.loads(received_message)
            if payload['client'] == "SYSTEMCONN" and not(item5.newConn):
                item5.chatLog.configure(state='normal')
                finalmsg = str(payload['client']) + " : " + payload['msg']
                item5.chatLog.insert(tk.END, finalmsg + '\n', 'system')
                item5.chatLog.configure(state='disabled')
                item5.chatLog.see(tk.END)
                item5.client.publish("SYS_" + str(payload['sender']), "Client ID #" + str(item5.clientID))
                playsound('sounds/online.wav', False)
            else:
                item5.chatLog.configure(state='normal')
                if payload['sender'] == item5.userIP and payload['client'] == item5.clientID:
                    finalmsg = "(You) : " + payload['msg']
                    item5.chatLog.insert(tk.END, finalmsg + '\n', 'you')
                elif payload['sender'] == "SYSTEM" or payload['client'] == "SYSTEMCONN" or payload['client'] == "SYSTEMDISC":
                    finalmsg = str(payload['client']) + " : " + payload['msg']
                    item5.chatLog.insert(tk.END, finalmsg + '\n', 'system') 
                    if payload['client'] == "SYSTEMDISC":
                        playsound('sounds/offline.wav', False)
                else:
                    finalmsg = str(payload['client']) + " : " + payload['msg']
                    item5.chatLog.insert(tk.END, finalmsg + '\n', 'people')
                    playsound('sounds/msg.wav', False)
                # Append the received message to the chatLog text box
                item5.chatLog.configure(state='disabled')
                item5.chatLog.see(tk.END)  # Scroll to the bottom of the chatLog
        except:
            item5.chatLog.configure(state='normal')
            item5.chatLog.insert(tk.END, item4.payload.decode("utf-8") + '\n')
            item5.chatLog.configure(state='disabled')
            item5.chatLog.see(tk.END)
        item5.newConn = False

    def send(self):
        # Get the message from the textMsg text box
        message = self.textMsg.get()
        # Publish the message to the chatID topic
        payload = {
            "sender" : self.userIP,
            "client" : self.clientID,
            "msg" : message
        }
        payload = json.dumps(payload)
        self.client.publish(self.topic, payload)
        # clear the textMsg text box
        self.textMsg.delete(0, tk.END)

    def on_close(self):
        response = messagebox.askyesno('Exit','Are you sure you want to exit?')
        if response:
            payload = {
                "sender" : self.clientID,
                "client" : "SYSTEMDISC",
                "msg" : "Client #" + str(self.clientID) +" has disconnected!"
            }
            payload = json.dumps(payload)
            self.client.publish(self.topic, payload)
            self.mainwindow.destroy()


if __name__ == "__main__":
    app = mqttChat()
    app.run()
