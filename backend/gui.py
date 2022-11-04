# QT
from asyncio.base_subprocess import ReadSubprocessPipeProto
from multiprocessing.queues import Queue
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF, QRandomGenerator, QRect, QTimer, QDateTime
from PyQt5.QtGui import *

# openvslam communication
import subprocess
import os
from PyQt5.sip import setdeleted

# misc
import numpy as np
import argparse
import time
import json
import sys
import queue
import random
import shutil

# backend and gui
from backend.design import Ui_Form
from backend.handler import Handler
from backend.pmodules.mqtt import MqttListener, MqttSender
from backend.heatmap import Heatmap

# PIL
from PIL import Image
from PIL.ImageQt import ImageQt


class ui_interface(Ui_Form):
    def __init__(self,handler):
        self.handler = handler

        # List updates
        self.timer_list = QTimer()
        self.timer_list.timeout.connect(self.update_lists)
        self.timer_list.start(500)

        # active cam
        self.active_cam = None

        # default image mode
        self.image_mode = "normal"
        self.scaled = False
        self.timestamp = int(time.time())
        # load cb_system_topic items
        self.cb_add_items()

        # mqtt listener
        self.mqtt_listener_topic = "/#"
        self.mqtt_listener = MqttListener(self.handler.s_mqtt_broker, self.handler.s_mqtt_port,
                                          self.mqtt_listener_topic, self.listener_recv)
        self.fifo = queue.Queue()
        self.timer_mqtt = QTimer()
        self.timer_mqtt.timeout.connect(self.mqtt_update)
        self.timer_mqtt.start(20)

        # image load
        self.timer_copy = QTimer()
        self.timer_copy.timeout.connect(self.update_progress_bar)
        self.timer_copy.start(500)
        self.take_screenshot = False
        self.delete_old_images()

        # connect events
        self.connect_events()

    def connect_events(self):
        # Overview
        self.btn_all_det_pose.clicked.connect(self.handler.start_det_pose)
        self.btn_all_det_pose_human.clicked.connect(self.handler.start_det_pose_human)
        self.btn_all_cal_search.clicked.connect(self.handler.start_cal_search)
        self.btn_all_stop.clicked.connect(self.handler.stop)
        self.btn_video_record_all.clicked.connect(self.record_video)
        self.btn_reset_camera.clicked.connect(self.reset_camera)
        self.btn_all_reboot.clicked.connect(self.handler.reboot)
        # self.btn_all_git_update.clicked.connect(self.handler.git_update)./main.sh

        # Sensors
        self.cb_sensor.currentIndexChanged.connect(self.update_lists)

        ## sensor control
        self.btn_single_det_pose.clicked.connect(self.handler.single_det_pose)
        self.btn_single_stop.clicked.connect(self.handler.single_stop)
        self.btn_single_reboot.clicked.connect(self.handler.single_reboot)
        self.btn_single_git_update.clicked.connect(self.handler.single_git_update)
        self.btn_single_det_pose_human.clicked.connect(self.handler.single_det_pose_human)
        self.btn_single_cal_search.clicked.connect(self.handler.single_cal_search)
        self.btn_single_cal_calibrate.clicked.connect(self.handler.single_cal_calibrate)
        self.btn_single_reset_cam.clicked.connect(self.handler.single_reset_camera)
        self.btn_single_cal_search.clicked.connect(self.handler.single_cal_search)
        self.btn_video_record.clicked.connect(self.single_record_video)
        self.cb_sensor.currentIndexChanged.connect(self.update_image)

        ## calibration
        self.btn_cal_send_markersize.clicked.connect(self.single_set_marker_size)
        self.btn_cal_send_position.clicked.connect(self.send_marker_position)
        self.btn_single_cal_search_2.clicked.connect(self.handler.single_cal_search)
        self.btn_single_cal_calibrate_2.clicked.connect(self.handler.single_cal_calibrate)
        self.btn_single_stop_2.clicked.connect(self.handler.single_stop)

        ## mask
        self.btn_select_mask.clicked.connect(self.select_mask)
        self.btn_upload_mask.clicked.connect(self.upload_mask)
        self.pushButton.clicked.connect(self.get_images)
        self.rb_image_normal.toggled.connect(self.change_image_mode)
        self.rb_image_mask.toggled.connect(self.change_image_mode)
        self.rb_image_merged.toggled.connect(self.change_image_mode)

        ## settings
        self.cb_flip_cam.toggled.connect(self.single_set_flip_state)

        # System
        ## mqtt
        self.cb_system_topic.currentIndexChanged.connect(self.mqtt_switch_mode)

    def cb_add_items(self):
        self.cb_system_topic.addItem("/#")
        self.cb_system_topic.addItem("info/#")
        self.cb_system_topic.addItem("general/#")
        self.cb_system_topic.addItem("detection/#")
        self.cb_system_topic.addItem("detection/humans/#")
        self.cb_system_topic.addItem("detection/vehicle/#")
        self.cb_system_topic.addItem("position/#")
        self.cb_system_topic.addItem("position/humans/#")
        self.cb_system_topic.addItem("position/vehicle/#")
        self.cb_system_topic.addItem("warnings/#")

    def update_lists(self):
        # check if mqtt connection is established
        if self.handler.connected:
            self.lb_mqtt_con_state.setText("connected")
        else:
            self.lb_mqtt_con_state.setText("not connected")

        # get sensor status
        self.handler.get_status()

        # overview
        for i in range(len(self.handler.sensors)):
            sensor = self.handler.sensors[i]
            exists = False
            for j in range(self.lw_sensors.count()):
                item = self.lw_sensors.item(j)
                if item.text().split(" -")[0] == sensor.id:
                    item.setText(f"{sensor.id} - {sensor.mode} [{sensor.ip}]")
                    exists = True
            if not exists:
                self.lw_sensors.addItem(f"{sensor.id} - {sensor.mode} [{sensor.ip}]")

        # sensors
        for i in range(len(self.handler.sensors)):
            sensor = self.handler.sensors[i]
            exists = False
            for j in range(self.cb_sensor.count()):
                item = self.cb_sensor.itemText(j)
                if item == sensor.id:
                    # print(item, sensor.id)
                    self.cb_sensor.setItemText(j, f"{sensor.id}")
                    exists = True
                    break
            if not exists:
                self.cb_sensor.addItem(f"{sensor.id}")

        # select current sensor
        for i in range(len(self.handler.sensors)):
            # print(self.cb_sensor.currentText())
            if self.handler.sensors[i].id == self.cb_sensor.currentText():
                # print(self.cb_sensor.currentText())
                self.handler.selected_sensor = self.handler.sensors[i]

        # sensor selection
        if not self.handler.selected_sensor == None:
            self.lb_ip.setText(self.handler.selected_sensor.ip)
            self.lb_mode.setText(self.handler.selected_sensor.mode)
            self.label_25.setText(str(self.handler.selected_sensor.has_vision))
            self.label_5.setText(str(self.handler.selected_sensor.has_vision))

    # overview
    ## record video
    def record_video(self):
        self.handler.record_video(self.le_video_filename_all.text(), int(self.le_video_duration_all.text()))

    def reset_camera(self):
        self.handler.reset_camera()

    # general
    def single_record_video(self):
        self.handler.single_record_video(self.le_video_filename_all.text(), int(self.le_video_duration_all.text()))

    # visualization
    ## scale


    ## upload image


    ## draw


    ## heatmap
 
    # mqtt
    def listener_recv(self, client, userdata, msg):
        data = json.loads(msg.payload.decode('utf-8'))
        self.fifo.put(f"[{time.time()}][{msg.topic.split('/')[-1]}] {data}")

    def mqtt_switch_mode(self):
        self.mqtt_listener_topic = self.cb_system_topic.currentText()
        self.mqtt_listener.stop()
        self.mqtt_listener = MqttListener(self.handler.s_mqtt_broker, self.handler.s_mqtt_port,
                                          self.mqtt_listener_topic, self.listener_recv)

    def mqtt_update(self):
        while not self.fifo.empty():
            self.plainTextEdit.appendPlainText(self.fifo.get())

    # calibration
    def single_set_marker_size(self):
        self.handler.selected_sensor.send("set_marker_size", float(self.le_marker_size.text()))  # le_marker_size

    def send_marker_position(self):
        # self.le_cal_x, le_cal_y
        self.handler.send_marker_position(float(self.le_calibration_x.text()), float(self.le_calibration_y.text()))

    # config
    def single_set_flip_state(self):
        if self.cb_flip_cam.isChecked():
            self.handler.selected_sensor.send("set_flip", 2)
        else:
            self.handler.selected_sensor.send("set_flip", 0)




