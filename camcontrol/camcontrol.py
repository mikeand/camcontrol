#!/bin/env python
from datetime import datetime

import picamera
import RPi.GPIO as GPIO
import io
import os
import logging
import time

MODE_SLEEP = 0
MODE_SEEK = 1
MODE_RECORD = 2
MOBILE_IP = '10.1.1.6'
PIR_IN = 7
SLEEP_SECONDS = 300
PING_SECONDS = 30
LED_OUT = 11

GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIR_IN, GPIO.IN)
GPIO.setup(LED_OUT, GPIO.OUT)

OUTPUT_PATH='/home/michael/Sync/HomeCam'

class CameraControl:

    def __init__(self):
        self.current_mode = MODE_SLEEP
        self.file_name = ''

    def event_loop(self):
        if self.current_mode == MODE_SEEK:
            self.perform_seek()
        if self.current_mode == MODE_RECORD:
            self.perform_record()
        if self.current_mode == MODE_SLEEP:
            self.perform_sleep()

    def perform_seek(self):
        seconds = 0
        blink = 0
        total_seconds = 0

        with picamera.PiCamera() as camera:
            camera.resolution = (1280, 720)
            camera.framerate = 30
            camera.vflip = True
            camera.hflip = True
            stream = picamera.PiCameraCircularIO(camera, seconds=20)
            camera.start_recording(stream, format='h264')

            try:
                while self.current_mode == MODE_SEEK:
                    camera.wait_recording(1)
                    if GPIO.input(PIR_IN):
                        logging.info("IR Detected, Capturing +10 Seconds")
                        camera.wait_recording(10)
                        self.write_video(stream)
                        self.current_mode = MODE_RECORD
                    elif seconds < PING_SECONDS:
                         seconds += 1
                         total_seconds += 1
                         blink = 1 - blink
                         if total_seconds > 200: 
                             blink = 0
                         GPIO.output(LED_OUT, blink)
                    elif self.check_mobile_is_here():
                        logging.info("Mobile phone found, going into sleep")
                        self.current_mode = MODE_SLEEP
                    else:
                        seconds = 0
            finally:
                camera.stop_recording()

    def perform_record(self):
        logging.info("Logging additional captures for 5 minutes")
        with picamera.PiCamera() as camera:
            camera.resolution = (1280, 720)
            camera.framerate = 30
            camera.vflip = True
            camera.hflip = True
            camera.start_recording(self.file_name + '.1.h264')
            camera.wait_recording(5)
            for i in range(2, 60):
                camera.split_recording(self.file_name + '.%d.h264' % i)
                camera.wait_recording(5)
            camera.stop_recording()
            self.current_mode = MODE_SEEK

    def write_video(self, stream):
        self.file_name = datetime.now().strftime("capture%d%m%Y%H%M%S")
        self.file_name = os.path.join(OUTPUT_PATH, self.file_name)

        out_name = self.file_name + '.h264'
        logging.info("Write video: " + out_name)
        with stream.lock:
            for frame in stream.frames:
                if frame.frame_type == picamera.PiVideoFrameType.sps_header:
                    stream.seek(frame.position)
                    break

            with io.open(out_name, 'wb') as output:
                output.write(stream.read())

        self.current_mode = MODE_RECORD

    def check_mobile_is_here(self):
        response = os.system("ping -c 1 -w2 " + MOBILE_IP + " > /dev/null 2>&1")
        return response == 0

    def perform_sleep(self):
        if self.check_mobile_is_here():
            logging.info("Currently sleeping, mobile found")
            time.sleep(SLEEP_SECONDS)
        else:
            logging.info("Mobile missing, switching to seek mode")
            self.current_mode = MODE_SEEK

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    logging.info("Starting up Camera Control")
    cam = CameraControl()
    while True:
        cam.event_loop()
