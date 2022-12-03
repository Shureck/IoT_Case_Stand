import asyncio
import paho.mqtt.client as mqtt
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
from fastapi.responses import FileResponse
from fastapi_socketio import SocketManager
import socketio
import threading
import time
from fastapi.staticfiles import StaticFiles
import secrets

from starlette.middleware.cors import CORSMiddleware
import logging
import json

# logger = logging.getLogger()
# logger.setLevel(logging.INFO)
#
# file_handler = logging.FileHandler('foo2.log')
# stream_handler = logging.StreamHandler()
#
# stream_formatter = logging.Formatter(
#     '%(asctime)-15s %(levelname)-8s %(message)s')
# file_formatter = logging.Formatter(
#     "{'time':'%(asctime)s', 'name': '%(name)s', 'level': '%(levelname)s', 'message': '%(message)s'}"
# )
#
# file_handler.setFormatter(file_formatter)
# stream_handler.setFormatter(stream_formatter)
#
# logger.addHandler(file_handler)
# logger.addHandler(stream_handler)

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)
app = FastAPI()
sio_app = socketio.ASGIApp(sio)

app.mount("/case/2/scripts", StaticFiles(directory="../scripts"), name="scripts")
app.mount("/case/2/images", StaticFiles(directory="../images"), name="images")
app.mount("/case/2/styles", StaticFiles(directory="../styles"), name="styles")
app.mount('/case/2/ws', sio_app)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_case = {}
qr_que = []
qr_secret = secrets.token_urlsafe(10)
# qr_que.append(qr_secret)


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("/devices/wb-mrgbw-d_78/controls/RGB")
    client.subscribe("/devices/wb-msw-v3_21/controls/Temperature")
    client.subscribe("/devices/wb-msw-v3_21/controls/Current Motion")
    client.subscribe("/devices/wb-msw-v3_21/controls/Illuminance")
    client.subscribe("/devices/wb-msw-v3_21/controls/Sound Level")
    client.subscribe("/devices/wb-msw-v3_21/controls/CO2")
    client.subscribe("/devices/wb-msw-v3_21/controls/Humidity")


def on_message(client, userdata, msg):
    # print(msg.topic+" "+str(msg.payload.decode('utf-8')))
    data_case[msg.topic] = str(msg.payload.decode('utf-8'))
    data = {"topic": msg.topic, "msg": str(msg.payload.decode('utf-8'))}
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(sio.emit('topic_data', data))
    loop.close()


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# client.connect("192.168.1.24", 1883, 60)
# client.loop_start()


async def dell_after(sid, token):
    if token in qr_que:
        qr_que.remove(token)
    print({"event": "dell_pop", "current_queue": qr_que})
    await sio.disconnect(sid)
    print("I killed", sid)


def between_callback(sid, token):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(dell_after(sid, token))
    loop.close()


@app.get("/case/2")
async def giveMain(key: str = None):
    global qr_secret
    if key in qr_que:
        return FileResponse("../main2.html")
    elif key == qr_secret:
        data = {}
        qr_que.append(qr_secret)
        qr_secret = secrets.token_urlsafe(10)
        data['qr_secret'] = qr_secret
        await sio.emit('new_qr', data)
        return FileResponse("../main2.html")
    else:
        return FileResponse("../refresh.html")


@app.get("/case/2/getQR")
def setColor():
    return FileResponse("../qr_generator2.html")


current_active_users = []


@sio.event
async def connect(sid, environ, auth=None):
    print(f"{sid} is connected.")
    print(auth)
    if 'token' in auth and auth['token'] in qr_que:
        await sio.save_session(sid, {"authorized": True})
        threading.Timer(60.0, between_callback, args=(sid, auth['token'], )).start()
        for i in data_case:
            data = {"topic": i, "msg": data_case[i]}
            print("data _______", data)
            await sio.emit('topic_data', data)
    elif "qr_viewer_key" in auth and auth["qr_viewer_key"] == "#qwe":
        await sio.save_session(sid, {"authorized": False})
        await sio.emit('new_qr', {"qr_secret": qr_secret}, sid)
    else:

        raise ConnectionRefusedError('authentication failed')


@sio.on('change_color')
async def changColor(sid, data: object):
    session = await sio.get_session(sid)
    if not session["authorized"]:
        print(session )
        return

    client.publish("/devices/wb-mrgbw-d_78/controls/RGB/on", data)
    print(f'sender-{sid}: ', data)


@sio.on('button')
async def setState(sid, data: object):
    session = await sio.get_session(sid)
    if not session["authorized"]:
        return
    client.publish("/devices/wb-gpio/controls/"+data, "1")
    time.sleep(0.8)
    client.publish("/devices/wb-gpio/controls/"+data, "0")
    print(f'sender-{sid}: ', data)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8089)
