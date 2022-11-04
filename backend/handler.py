# communication
from backend.pmodules.mqtt import *

# sensor
from backend.sensor import Sensor

# misc
from backend.pmodules.config_handler import ConfigHandler
from backend.pmodules.log import Logger
from backend.copy import copy_element, copy_element_mqtt
from backend.heatmap import Heatmap
from backend.history import History
import os
import queue
import copy
import numpy as np
import time
import base64
from backend.design import Ui_Form

log = Logger()

class Handler(Ui_Form):
    def __init__(self):
        self.sensors = []
        self.selected_sensor = None
        self.timestamp = None
        self.file_name = ""
        self.flag1 = False
        self.flag2 = False
        # load config
        self.settings = ConfigHandler("./backend/settings.json")
        self.s_mqtt_broker = self.settings.get("mqtt", "broker")
        self.s_mqtt_port = self.settings.get("mqtt", "port")
        self.s_logging_folder = self.settings.get("logging", "folder")
        self.s_logging_file = self.settings.get("logging", "filename")
        self.s_logging_level = self.settings.get("logging", "level")
        self.s_logging_verbose = self.settings.get("logging", "verbose")

        # logging
        log.init(self.s_logging_file, folder_path=self.s_logging_folder, log_level=self.s_logging_level, use_subprocess=False, verbose=self.s_logging_verbose)

        # check if connection to broker can be established
        log.log(f"try to connect to {self.s_mqtt_broker}")
        self.connected = check_ip(self.s_mqtt_broker, self.s_mqtt_port)

        # create lsitener and sender for general communication
        if self.connected:
            self.publisher_all = MqttSender(self.s_mqtt_broker, self.s_mqtt_port, "general", "all")
            self.listener_general = MqttListener(self.s_mqtt_broker, self.s_mqtt_port, "info/#", self.on_info_recv)
            self.listener_cal = MqttListener(self.s_mqtt_broker, self.s_mqtt_port, "calibration/#", self.on_cal_recv)
            log.log(f"connected to {self.s_mqtt_broker} as sender and listener")
        else:
            log.log(f"could not reach {self.s_mqtt_broker}", log.ERROR)

        # mqtt sender for calibration process
        self.publisher_cal = MqttSender(self.s_mqtt_broker, self.s_mqtt_port, "calibration", "cal_pos")

        # position listener
        self.listener_detections = MqttListener(self.s_mqtt_broker, self.s_mqtt_port, "detection/#", self.on_recv_event)
        self.listener_positions = MqttListener(self.s_mqtt_broker, self.s_mqtt_port, "position/#", self.on_recv_event)
        self.listener_warnings = MqttListener(self.s_mqtt_broker, self.s_mqtt_port, "warning/#", self.on_recv_event)
        self.listener_screenshot = MqttListener(self.s_mqtt_broker, self.s_mqtt_port, "screenshot/#", self.on_recv_event)

        self.switched = False

        # livemap
        self.queue = queue.Queue()
        self.events = {
            "person_unfiltered": {},
            "person_filtered": {},
            "vehicle_unfiltered": {},
            "vehicle_filtered": {},
            "warning": {}
        }
        self.statistics = {
            "person_filtered": 0,
            "vehicle_filtered": 0,
            "warning": 0
        }

        # heatmap
        self.s_heatmap_size = self.settings.get("heatmap", "size")
        self.heatmap = Heatmap(res_x=100, res_y=100, range_x=[0,100], range_y=[0,100])

    def add_to_events(self, topic, id, data):
        count_v = 0
        count_p = 0
        if topic != "vehicle_filtered":
            count_v += 1
            if count_v > 3:
                self.statistics["vehicle_filtered"] = 0
        else:
            count_v = 0
        if topic != "person_filtered":
            count_p += 1
            if count_p > 3:
                self.statistics["person_filtered"] = 0
        else:
            count_p = 0
        if id in self.events[topic]:
            self.events[topic][id].add(data)
        else:
            self.events[topic][id] = History(data)
        self.queue.put([topic, id, data])

    def on_recv_event(self, client, userdata, msg):
        data = json.loads(msg.payload.decode('utf-8'))
        if "detection/humans" in msg.topic:
            sender_id = copy.copy(int(msg.topic.split("jetson_")[-1]))
            for key in data.keys():
                self.add_to_events("person_unfiltered", sender_id, [data[key]["x"], data[key]["y"]])
        if "position" in msg.topic:
            self.statistics["person_filtered"] = len(data['human'])
            self.statistics["vehicle_filtered"] = len(data['vehicle'])
            for key in data['human'].keys():
                self.add_to_events("person_filtered", key, [data[key]['human']["x"], data[key]['human']["y"]])
            for key in data['vehicle'].keys():
                self.add_to_events("vehicle_filtered", key, [data['vehicle'][key]["x"], data['vehicle'][key]["y"]])
        if "detection/vehicle" in msg.topic:
            for key in data.keys():
                self.add_to_events("vehicle_unfiltered", key, [data[key]["x"], data[key]["y"]])
        if "warnings" in msg.topic:
            for key in data.keys():
                self.add_to_events("warning", key, [data[key]["x"], data[key]["y"]])
        if "screenshot" in msg.topic and self.flag1 and self.flag2:
            # sender_id = copy.copy(int(msg.topic.split("jetson_")[-1]))
            ms = str(msg.payload.decode('utf-8'))
            img = ms.encode("ascii")
            final_msg = base64.b64decode(img)
            open(self.file_name, "wb").write(final_msg)
            print("File Received")
            self.flag1 = False
            self.flag2 = False
        
    def load_timestamp(self, timestamp):
        self.timestamp = timestamp
        self.flag1 = True

    def load_sensor_images(self, timestamp):
        # check if sensor is selected
        if self.selected_sensor == None:
            log.log("no sensor selected", lvl=log.WARNING)
            pass

        # delete previous images
        img_name = self.selected_sensor.ip.replace(".","_")

        # copy all three images
        #copy_element(self.selected_sensor.ip, "/home/probility/jetsonconf/sample.png", f"./data/sensor_images/sample__{img_name}_{timestamp}.png", usr="probility", pwd="jetson")
        #copy_element(self.selected_sensor.ip, "/home/probility/jetsonconf/sample_masked.png", f"./data/sensor_images/sample_masked__{img_name}_{timestamp}.png", usr="probility", pwd="jetson")
        #copy_element(self.selected_sensor.ip, "/home/probility/jetsonconf/mask.bmp", f"./data/sensor_images/mask__{img_name}_{timestamp}.bmp", usr="probility", pwd="jetson")
        copy_element_mqtt(self.selected_sensor.ip, "/home/probility/jetsonconf/sample.png", f"./data/sensor_images/sample__{img_name}_{timestamp}.png", usr="probility", pwd="jetson", topic_name="screenshot")
        return True

    def upload_file_to_sensor(self, sensor, local_path, remote_path):
        copy_element(sensor.ip, local_path, remote_path, usr="probility", pwd="jetson", upload=True)

    def screenshot(self):
        # take screenshot on sensor
        if (not self.selected_sensor == None) and self.flag1:
            self.flag2 = True
            img_name = self.selected_sensor.ip.replace(".","_")
            self.file_name = f"./data/sensor_images/sample__{img_name}_{self.timestamp}.png"
            if not self.selected_sensor.sc_mode:
                self.selected_sensor.screenshot()
        
        self.get_status()

        if self.selected_sensor.sc_mode:
            if self.selected_sensor.mode == "screenshot":
                self.switched = True
            
            if self.switched and not self.selected_sensor.mode == "screenshot":
                self.selected_sensor.sc_mode = False
                self.switched = False
                return True
            else:
                return False


        # time_0 = time.time()

        # done = False
        # c = 0
        # while time.time() - time_0 < 3:
        #     if self.selected_sensor.mode == "screenshot":
        #         break
        #     if (time.time() - time_0) % 0.5 < 0.01:
        #         self.get_status()
        # while time.time() - time_0 < 13:
        #     if not self.selected_sensor.mode == "screenshot":
        #         done = True
        #         break
        #     if (time.time() - time_0) % 0.5 < 0.01:
        #         self.get_status()

    def on_cal_recv(self, client, userdata, msg):
        data = json.loads(msg.payload.decode('utf-8'))
        if not 'cal_pos' in msg.topic:
            if data['sight']:
                self.selected_sensor.has_vision = True
            else:
                self.selected_sensor.has_vision = False

    def on_info_recv(self, client, userdata, msg):
        data = json.loads(msg.payload.decode('utf-8'))
        sender_id = data["name"]

        # check if sensor already exists
        sensor = None
        for s in self.sensors:
            if sender_id == s.id:
                sensor = s
                s.ip = data["ip"]
                s.set_mode(data['mode'])

        # add sensor if it is not listed
        if not sensor:
            self.sensors.append(Sensor(sender_id, data['ip'], self.s_mqtt_broker, self.s_mqtt_port))
            sensor = self.sensors[-1]
            log.log(f"added new sensor: {sensor.id}")


    def send_all(self, command, value):
        payload = {
            "command": command,
            "value": value
        }
        self.publisher_all.send(payload)

    def get_status(self):
        self.send_all("info", False)

    def start_det_pose_human(self):
        self.send_all("detect", "pose_human")

    def start_det_pose_vehicle(self):
        self.send_all("detect","pose_vehicle")

    def start_det_pose(self):
        self.send_all("detect", "pose")

    def start_cal_search(self):
        self.send_all("calibrate", "search")

    def stop(self):
        self.send_all("stop", "")

    def reset_camera(self):
        self.send_all("reset_camera", "")

    def reboot(self):
        self.send_all("reboot", "")

    def send_marker_position(self, x, y):
        payload = {
            "offset": [x, y]
        }
        self.publisher_cal.send(payload)

    def record_video(self, filename, duration):
        val_str = {
            "filename": filename,
            "duration": duration
        }
        self.send_all("video", val_str)

    # single buttons
    def single_det_pose(self):
        self.selected_sensor.send("detect", "pose")

    def single_det_pose_human(self):
        self.selected_sensor.send("detect", "pose_human")
        
    def single_cal_search(self):
        self.selected_sensor.send("calibrate", "search")

    def single_cal_calibrate(self):
        self.selected_sensor.send("calibrate", "calibrate")

    def single_stop(self):
        self.selected_sensor.send("stop", "")

    def single_reboot(self):
        self.selected_sensor.send("reboot", "")
        
    def single_git_update(self):
        self.selected_sensor.send("update", "")
        
    def single_reset_camera(self):
        self.selected_sensor.send("reset_camera", "")

    def single_record_video(self, filename, duration):
        val_str = {
            "filename": filename,
            "duration": duration
        }
        self.selected_sensor.send("video", val_str)

    @staticmethod
    def distance(p1, p2):
        return np.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)