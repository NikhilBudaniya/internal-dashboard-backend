#import os
from email import message
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
import paho.mqtt.client as mqtt
import base64

global topic
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    global topic
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(topic)
    # The callback for when a PUBLISH message is received from the server.

global file_name
def on_message(client, userdata, msg):
    # more callbacks, etc
    # Create a file with write byte permission
    ms = str(msg.payload.decode('utf-8'))
    img = ms.encode("ascii")
    final_msg = base64.b64decode(img)
    open(file_name, "wb").write(final_msg)
    print("File Received")


file_progress = {}

def progress(filename, size, sent):
    global file_progress
    #print("%s\'s progress: %.2f%%   \r" % (filename, float(sent)/float(size)*100) )
    file_progress[filename] = round(float(sent)/float(size)*100, 2)

def copy_element(ip, remote_path, local_path="", usr="probility", pwd="", upload=False):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.load_system_host_keys()
    ssh.connect(hostname=ip,
                username=usr,
                password=pwd)
    scp = SCPClient(ssh.get_transport(), progress=progress)
    if upload:
        scp.put(remote_path, local_path)
    else:
        scp.get(remote_path, local_path)
    scp.close()

def copy_element_mqtt(ip, remote_path, local_path="", usr="probility", pwd="", upload=False, topic_name=""):
    global topic, file_name
    client = mqtt.Client()
    client.connect("192.168.1.10")
    topic = topic_name + "jetson_" + str(ip[-2:])
    print("Getting the topic ", topic)
    file_name = local_path
    # client.on_connect = on_connect()
    client.subscribe(topic)
    client.on_message = on_message

    # Blocking call that processes network traffic, dispatches callbacks and
    # handles reconnecting.
    # Other loop*() functions are available that give a threaded interface and a
    # manual interface.
    client.loop_forever()

if __name__ == "__main__":
    copy_element("134.169.61.211", "/home/probility/JetsonNano/config/mask.bmp", "../data/", usr="probility", pwd="jetson")

    def combine_rectangles(self, rect):
        index = len(rect)-1
        if rect is None: return rect
        while index >= 0:
            no_Over_Lap = False
            while no_Over_Lap == False and len(rect) > 1 and index >= 0:
                # print("rect :", rect, "Index : ", index)
                rect1 = rect[index]
                tmpRect = np.delete(rect, index, 0)
                for i in range(len(tmpRect)-1,-1,-1):
                    rect2 = tmpRect[i]
                    if (self.is_rect_overlap(rect1, rect2)):
                        if (index in self.added_indices) and (i not in self.added_indices):
                            rect = tmpRect
                        else:
                            tmpRect[i] = self.merge_rectangle(rect1, rect2)
                            rect = tmpRect
                        no_Over_Lap = False
                        index -= 1
                        break
                    no_Over_Lap = True
            index -= 1
        return rect