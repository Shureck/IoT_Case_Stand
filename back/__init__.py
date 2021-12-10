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

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)
app = FastAPI()
sio_app = socketio.ASGIApp(sio)

app.mount("/case/node_modules", StaticFiles(directory="../node_modules"), name="node_modules")
app.mount("/case/scripts", StaticFiles(directory="../scripts"), name="scripts")
app.mount("/case/images", StaticFiles(directory="../images"), name="images")
app.mount("/case/fonts", StaticFiles(directory="../fonts"), name="fonts")
app.mount("/case/styles", StaticFiles(directory="../styles"), name="styles")
app.mount('/case/ws', sio_app)

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

# client.connect("192.168.1.31", 1883, 60)
client.loop_start()

async def dell_after(sid, secret):
    data = {}
    data['sid'] = sid
    data['secret'] = secret
    await sio.emit("timer",data)
    print("I killed",sid, secret)
def between_callback(sid, secret):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(dell_after(sid, secret))
    loop.close()

@app.get("/case")
def giveMain(key: str = None):
    if key == "qwe":
        return FileResponse("../main.html")
    else:
        return FileResponse("../refresh.html")

@app.get("/setColor")
def setColor(color):
    print(color)
    return color

current_active_users = []

@sio.event
async def connect(sid, environ):
    print(f"{sid} is connected.")
    data = {}
    data['secret'] = secrets.token_urlsafe(8)
    await sio.emit('new_token', data)
    for i in data_case:
        data = {"topic": i, "msg": data_case[i]}
        print("data _______", data)
        await sio.emit('topic_data', data)
    # threading.Timer(10.0,between_callback,args=(sid,data['secret'],)).start()


@sio.on('message')
async def broadcast(sid, data: object):
    print(f'sender-{sid}: ', data)
    await sio.emit('response', data)

@sio.on('change_color')
async def changColor(sid, data: object):
    client.publish("/devices/wb-mrgbw-d_78/controls/RGB/on",data)
    print(f'sender-{sid}: ', data)

@sio.on('button')
async def setState(sid, data: object):
    client.publish("/devices/wb-gpio/controls/"+data,"1")
    time.sleep(0.8)
    client.publish("/devices/wb-gpio/controls/"+data,"0")
    print(f'sender-{sid}: ', data)


@sio.on('update_status')
async def broadcast_status(sid, data: object):
    print(f'status {data["presence"]}')
    data['sid'] = sid

    if data not in current_active_users:
        current_active_users.append(data)

    if data['presence'] == 'offline':
        for user in current_active_users:
            if user['sid'] == data['sid'] and user['secret'] == data['secret']:
                current_active_users.remove(user)

    await sio.emit('status', current_active_users)


@sio.event
async def disconnect(sid):
    print('disconnected from front end', sid)
    for user in current_active_users:
        if user['sid'] == sid:
            user['presence'] = 'offline'
    print(current_active_users)
    await sio.emit('re_evaluate_status')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8089)