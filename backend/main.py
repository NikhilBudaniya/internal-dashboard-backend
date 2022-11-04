from backend.handler import Handler
from backend.gui import ui_interface
from fastapi import FastAPI, Query,Response
from backend.pmodules.mqtt import MqttListener, MqttSender
from PyQt5.QtCore import QPointF, QRandomGenerator, QRect, QTimer, QDateTime
import queue
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from backend.design import Ui_Form
import json
import time



handler = Handler()





fifo = queue.Queue()


def record_video():
    handler.record_video(handler.le_video_filename_all.text(), int(handler.le_video_duration_all.text()))

def reset_camera():
    handler.reset_camera()

def listener_recv(client, userdata, msg):
        data = json.loads(msg.payload.decode('utf-8'))
        fifo.put(f"[{time.time()}][{msg.topic.split('/')[-1]}] {data}")

def mqtt_switch_mode(self):
        mqtt_listener_topic = self.cb_system_topic.currentText()
        mqtt_listener.stop()
        mqtt_listener = MqttListener(handler.s_mqtt_broker, handler.s_mqtt_port,
                                          mqtt_listener_topic, listener_recv)

def mqtt_update():
        while not fifo.empty():
            handler.plainTextEdit.appendPlainText(fifo.get())

# calibration
def single_set_marker_size():
        handler.selected_sensor.send("set_marker_size", float(handler.le_marker_size.text()))  # le_marker_size

def send_marker_position():
        # self.le_cal_x, le_cal_y
    handler.send_marker_position(float(handler.le_calibration_x.text()), float(handler.le_calibration_y.text()))

# config
def single_set_flip_state():
    if handler.cb_flip_cam.isChecked():
        handler.selected_sensor.send("set_flip", 2)
    else:
        handler.selected_sensor.send("set_flip", 0)

mqtt_listener_topic = "/#"
mqtt_listener = MqttListener(handler.s_mqtt_broker,handler.s_mqtt_port,mqtt_listener_topic,listener_recv)

timer_mqtt = QTimer()
timer_mqtt.timeout.connect(mqtt_update)
timer_mqtt.start(20)



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def get_root():
    data = """
    {
        "status": "ok",
        "text": "Hello World!"
    }
    """
    return Response(content=data, media_type="application/json")

def update_lists():
        # check if mqtt connection is established
        if handler.connected:
            handler.lb_mqtt_con_state.setText("connected")
        else:
            handler.lb_mqtt_con_state.setText("not connected")

        # get sensor status
        handler.get_status()

        # overview
        for i in range(len(handler.sensors)):
            sensor = handler.sensors[i]
            exists = False
            for j in range(handler.lw_sensors.count()):
                item = handler.lw_sensors.item(j)
                if item.text().split(" -")[0] == sensor.id:
                    item.setText(f"{sensor.id} - {sensor.mode} [{sensor.ip}]")
                    exists = True
            if not exists:
                handler.lw_sensors.addItem(f"{sensor.id} - {sensor.mode} [{sensor.ip}]")

timer_list = QTimer()
timer_list.timeout.connect(update_lists)
timer_list.start(500)

       

@app.get("/overview/buttons/{button_clicked}")
async def connect_events(button_clicked:str):
    if button_clicked=="detection":
         handler.start_det_pose()
         return {"success":"detection started"}
       
    ##elif button_clicked=="detection-human":
    ##    handler.start_det_pose_human
    ##elif button_clicked=="detection-forklift":
    ##    handler.start_det_pose_vehicle
    elif button_clicked=="stop":
        handler.stop()
        return {"success":"sensors stopped"}
    elif button_clicked=="reset-camera":
        reset_camera()
        return {"success":"Camera reset successfully"}
    elif button_clicked=="reboot":
        handler.reboot()
        return {"success":"Reboot successfull"}
    ##elif button_clicked=="record-video":
    ##   record_video()

@app.get("/get-sensors-list")
async def get_sensors_list():
    sensors_list={"sensors":[]}
    a=handler.get_sensors()
    for i in range(len(a)):
        sensors_list["sensors"].append(a[i].id)
    return sensors_list









