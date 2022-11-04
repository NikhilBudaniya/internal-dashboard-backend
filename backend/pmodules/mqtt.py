import paho.mqtt.client as mqtt
import socket
import json
import time
import sys
import keyboard

def check_ip(ip, port):
   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   try:
      s.connect((ip, int(port)))
      s.shutdown(2)
      return True
   except:
      return False

class MqttSender():
    def __init__(self, broker, port, topic, name):
        self.broker = broker
        self.port = port
        self.name = name
        
        # set topic
        if topic[-1] == "/":
            self.topic = '{}{}'.format(topic, self.name)
        else:
            self.topic = '{}/{}'.format(topic, self.name)

        self.connect()

    def connect(self):
        #TODO change to mac adress related name
        self.clientname = self.name + "_" + str(time.localtime().tm_min) + str(time.localtime().tm_sec)
        self.client = mqtt.Client(self.clientname)
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect
        rc = self.client.connect(self.broker, self.port)
        if not rc == 0: 
            print("[MQTT] connected to mqtt server {}:{} on {}".format(self.broker, self.port, self.topic))
        return rc

    def send(self, payload, topic=""):
        payload = json.dumps(payload)
        if not topic == "":
            rc = self.client.publish(topic, payload)
        else:
            rc = self.client.publish(self.topic, payload)
        if rc == 0:
            print("[MQTT] error while sending message.")
            print("[MQTT] maybe the client disconnected?")
        return rc

    def send_raw(self, payload, topic=""):
        if not topic == "":
            rc = self.client.publish(topic, payload)
        else:
            rc = self.client.publish(self.topic, payload)
        if rc == 0:
            print("[MQTT] error while sending message.")
            print("[MQTT] maybe the client disconnected?")
        return rc

    def on_publish(self, client, userdata, result):
        return result

    def on_disconnect(self, client, userdata, rc):
        print("[MQTT] trying to reconnect ...")
        self.client.reconnect()
        print("[MQTT] successfully reconnected")


class MqttListener():
    def __init__(self, broker, port, topic, function):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.function = function
        self.timeout = 10

        # create client object
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        self.connect()

    def connect(self):
        rc = self.client.connect(self.broker, self.port, self.timeout)
        if rc == 0:
            print("[MQTT] connected as listener to mqtt server {}:{} on {}".format(self.broker, self.port, self.topic))
            # start listening
            self.client.loop_start()
        else:
            print("[MQTT] error while connecting")

    def on_disconnect(self, client, userdata, rc):
        print(f"[MQTT] disconnected: {str(rc)}")
        print("[MQTT] trying to reconnect ...")
        self.client.reconnect()
        print("[MQTT] successfully reconnected")
        
    def on_connect(self, client, userdata, flags, rc):
        client.subscribe(self.topic)
        return rc

    def on_message(self, client, userdata, msg):
        self.function(client, userdata, msg)

    def stop(self):
        self.client.loop_stop()

if __name__ == "__main__":
    #def on_msg(client, userdata, msg):
    #    print(msg.payload)

    # listener = MqttListener("127.0.0.1", 1883, "test/#", on_msg)
    level = 1
    flag1 = False
    flag2 = False
    flag3 = False
    flag4 = False
    flag5 = False
    flag6 = False
    mqtts_warning = MqttSender("192.168.1.10", 1883, "warnings/", f"vehicle_0")
    mqtts_human = MqttSender("192.168.1.10", 1883, "position/", f"human")
    mqtts_forklift = MqttSender("192.168.1.10", 1883, "slam/", f"forklift")
    hx = 3.0
    hy = 16.0
    fx = 20.0
    fy = 2.0
    fh = 180
    t0 = time.time()
    while True:
        fx -= 0.07
        hx += 0.07
        hy -= 0.14
        if keyboard.is_pressed('a'):
            flag1 = True
            flag4 = False
            flag2 = False
            flag3 = False
        elif keyboard.is_pressed('d'):
            flag4 = True
            flag1 = False
            flag2 = False
            flag3 = False
        elif keyboard.is_pressed('b'):
            flag1 = False
            flag2 = True
            flag3 = False
            flag4 = False
        elif keyboard.is_pressed('c'):
            flag1 = False
            flag2 = False
            flag3 = True
            flag4 = False
        elif keyboard.is_pressed('e'):
            flag1 = False
            flag2 = False
            flag3 = False
            flag4 = False
            flag5 = True
        elif keyboard.is_pressed('f'):
            flag1 = False
            flag2 = False
            flag3 = False
            flag4 = False
            flag5 = False
            flag6 = True
        print("running ...")
        if  flag1 == True:
            level = 2
            angle = 270
            payload = {
                        "angle": angle,
                        "level": str(level),
                        "HumanDir": 2,
                        "x": 3,
                        "y": 4
                    }
            print(payload)
            mqtts_warning.send(payload)
            flag1 = True
        elif  flag4 == True:
            level = 2
            angle = 305
            payload = {
                        "angle": angle,
                        "level": str(level),
                        "HumanDir": 2,
                        "x": 3,
                        "y": 4
                    }
            print(payload)
            mqtts_warning.send(payload)
            flag4 = True
        elif  flag2 == True:
            level = 3
            angle = 305
            payload = {
                        "angle": angle,
                        "level": str(level),
                        "HumanDir": 2,
                        "x": 3,
                        "y": 4
                    }
            print(payload)
            mqtts_warning.send(payload)
            flag2 = True
        elif  flag3 == True:
            level = 4
            angle = 270
            payload = {
                        "angle": angle,
                        "level": str(level),
                        "HumanDir": 2,
                        "x": 3,
                        "y": 4
                    }
            print(payload)
            mqtts_warning.send(payload)
            flag3 = True
        elif  flag5 == True:
            level = 2
            angle = 45
            payload = {
                        "angle": angle,
                        "level": str(level),
                        "HumanDir": 2,
                        "x": 3,
                        "y": 4
                    }
            print(payload)
            mqtts_warning.send(payload)
            flag5 = True
        elif flag6 == True:
            level = 0
            angle = 90
            payload = {
                        "angle": angle,
                        "level": str(level),
                        "HumanDir": 2,
                        "x": 3,
                        "y": 4
                    }
            print(payload)
            mqtts_warning.send(payload)
            flag6 = True
        human_payload = {"0": {"x": round(hx, 3), "y": round(hy, 3), "heading": round(0, 3)}}
        forklift_payload = {"0":{"x": round(fx, 3), "y": round(fy, 3), "heading": round(fh, 3)}}
        mqtts_human.send(human_payload)
        mqtts_forklift.send(forklift_payload)
        print("still running ...")
        if time.time() - t0 > 10 :
            break
        time.sleep(0.1)
        
