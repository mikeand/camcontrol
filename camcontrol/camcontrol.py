#!/bin/env python
from datetime import datetime

import picamera
import io
import os
import logging
import time

MODE_SLEEP = 0
MODE_SEEK = 1
MODE_RECORD = 2
SLEEP_SECONDS = 10

OUTPUT_PATH = '/home/michael/Sync/HomeCam'
PIR_DETECT = '/usr/local/bin/pir'
PIR_ENABLED = '/usr/local/bin/pir_enabled'


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

    def is_pir_detected(self):
        if self.current_mode == MODE_SEEK:
            return os.path.isfile(PIR_DETECT)
        return False

    def is_camera_enabled(self):
        return os.path.isfile(PIR_ENABLED)

    def perform_seek(self):
        seconds = 0

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
                    seconds += 1

                    if self.is_pir_detected():
                        logging.info("IR Detected, Capturing +10 Seconds")
                        camera.wait_recording(10)
                        self.write_video(stream)
                        self.current_mode = MODE_RECORD
                    elif seconds > SLEEP_SECONDS:
                        seconds = 0
                        if not self.is_camera_enabled():
                            self.current_mode = MODE_SLEEP
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

    def perform_sleep(self):
        if not self.is_camera_enabled():
            time.sleep(SLEEP_SECONDS)
        else:
            logging.info("PIR enabled, switching to seek mode")
            self.current_mode = MODE_SEEK

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    logging.info("Starting up Camera Control")
    cam = CameraControl()
    while True:
        cam.event_loop()
