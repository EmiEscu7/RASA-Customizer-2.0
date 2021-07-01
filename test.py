import requests
import json

PORT = "http://localhost:5005/webhooks/rest/webhook"

def send_msg(msg, name, personality):
    data = {"sender": name, "message": msg, "metadata": { "personality": personality} }
    x = requests.post(PORT, json = data)
    rta = x.json()
    text = rta['text']
    """if(rta != [] ):
        while(len(rta) > 1): #Lo ultimo que hay en rta es el nombre a quien está destinado el mensaje
            text += rta.pop(0)['text'] + ". "
        text = [text]
        text.append(rta.pop(0)['text'])
    else:
        text = ['','None']"""
    if x.status_code == 200:
        return text
    else:
        print(x.raw)
        return None

personality = [0.82, 0.54, 0.66, 0.69, 0.22]
rta = send_msg("He estado trabajando con la tarea {0}", "scrum", personality)
print(rta)
