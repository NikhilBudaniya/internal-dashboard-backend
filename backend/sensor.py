from backend.pmodules.mqtt import MqttListener, MqttSender

class Sensor():
    def __init__(self, id, ip, mqtt_broker, mqtt_port=1883):
        # general vars
        self.mode = "none"
        self.id = id
        self.ip = ip
        self.has_vision = False
        self.sc_mode = False

        # mqtt handler
        self.publisher = MqttSender(mqtt_broker, mqtt_port, "general", self.id)

    def get_status(self):
        pass

    def set_mode(self, mode):
        self.mode = mode

    def send(self, command, value):
        payload = {
            "command": command,
            "value": value
        }
        self.publisher.send(payload)

    def stop(self):
        self.send("stop", "")

    def calibrate_search(self):
        self.send("calibrate", "search")

    def calibrate_calibrate(self):
        self.send("calibrate", "calibrate")

    def calibrate_calibrate(self):
        self.send("calibrate", "calibrate")

    def detect_pose(self):
        self.send("detect", "pose")

    def detect_yolo(self):
        self.send("detect", "yolo")
    
    def screenshot(self):
        self.send("screenshot", "")
        self.sc_mode = True