####################################################################################
# Version Control
# - File name: detect_movement.py
# - Creator: koreattle
# - Feb 5 2019: koreattle: Created
####################################################################################
import RPi.GPIO as GPIO
import cv2
import imutils
import json
import time
import requests
import os
import threading

from picamera.array import PiRGBArray
from picamera import PiCamera
from datetime import datetime

from manage_signal import ManageSignal
from display_image import ImageServer
from processor import Processor
from generator import IdGenerator

from omxplayer.player import OMXPlayer

video_folder = "video/"
waiting_time_threshold = 6000

class DetectMovement(object):

    def __init__(
            self,
            resolution_width="",
            resolution_height="",
            frame_rate="",
            threshold_person_box_size="",
            threshold_package_box_size="",
            threshold_reaction_width="",
            image_recognition_endpoint="",
            role="",            
            send_to_hub_callback=None,
            show_video=False):

        # initialize the camera and grab a reference to the raw camera capture
        ######################################## DETECT_MOVEMENT ############################################
        self.resolution_width = resolution_width
        self.resolution_height = resolution_height
        self.camera = PiCamera()
        self.camera.resolution = tuple([resolution_width, resolution_height])
        self.camera.framerate = frame_rate
        self.role = role
        if self.role == "person":
            self.threshold_size = threshold_person_box_size
        elif self.role == "package":
            self.threshold_size = threshold_package_box_size
        self.image_recognition_endpoint = image_recognition_endpoint
        self.send_to_hub_callback = send_to_hub_callback
        self.avg = None
        ######################################## REACTION ############################################
        self.threshold_reaction_width = threshold_reaction_width
        self.record_flag = False
        self.stolen_history = "n"
        self.member_detect = False
        self.stranger_detect = False
        self.pre_package_number = 0
        self.total_tracking_time = 0
        self.pre_tracking_time = 0
        self.first_frame = ""
        self.pib_yn = "n"

        ######################################## MANAGE_SIGNAL ############################################
        self.manage_signal = ManageSignal(role)
        self.pre_package_status = 0
        self.pre_signal_status = ""

        ######################################## DISPLAY_IMAGE ############################################
        self.show_video = show_video
        
        if self.show_video:
            self.display_frame = None
            if self.role == "person":
                self.imageServer = ImageServer(5012, self)
            elif self.role == "package":
                self.imageServer = ImageServer(5013, self)
            self.imageServer.start()
                
        ######################################## SAVE_VIDEO ############################################
        self.file_name = ""   
        
    def __enter__(self):
        self.rawCapture = PiRGBArray(self.camera, size=self.camera.resolution)
        time.sleep(1.0) # needed to load at least one frame into the VideoStream class
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        # Clean up signal pins
        if self.role == "person":
            self.manage_signal.cleanup("person")
        elif self.role == "package":
            self.manage_signal.cleanup("package")
        
        if self.record_flag:
            self.camera.stop_recording()
            self.record_flag = False
        # self.video_processor.close(True)
        if self.show_video:
            self.imageServer.close()
            cv2.destroyAllWindows()
        print(exception_type, exception_value)

    def __send_frame_for_recognition(self, url: str, frame):
        result = ""
        headers = {'Content-Type': 'application/octet-stream'}
        
        try:
            response = requests.post(url, headers = headers, data = frame)
            if response:
                result = response.json()
            else:
                result = ["nothing", 0]
            return result
        except Exception as e:
            print('EXCEPTION:', str(e))
            return ["nothing", 0] 
    
    def start(self):
        for capture in self.camera.capture_continuous(self.rawCapture, format="bgr", use_video_port=True):
            
            start_time = time.time()
            
            # 1) Preprocess Function
            #Grab the raw NumPy array representing the image and initialize
            frame = capture.array

            #Package Rpi doesn't need to run if there is no one out there and no package.
            if self.role == "person":
                package_change_signal = int(self.manage_signal.read_in_signal("change"))

                if package_change_signal == 1:
                    
                    # 1) Show reaction ("Put that back")
                    if self.member_detect == False:
                        self.play_sound("packop-stolen")
                        self.pib_yn = "y"
                    
                    # 2) Start recording
                    if self.record_flag == False:
                        self.start_recording(self.rawCapture)
                    
                    self.stolen_history = "y"
            
            #Converting color image to gray_scale image
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # gray = cv2.GaussianBlur(gray, (21, 21), 0)

            #if the average frame is None, initialize it
            if self.avg is None:
                self.avg = gray.copy().astype("float")
                self.rawCapture.truncate(0)
                continue
            
            #accumulate the weighted average between the current frame and previous frames,
            #then compute the difference between the current frame and running average
            cv2.accumulateWeighted(gray, self.avg, 0.5)
            frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg))

            #threshold the delta image, dilate the thresholded image to fill in holes,
            #then find contours on thresholded image
            thresh = cv2.threshold(frame_delta, 5, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = imutils.grab_contours(contours)

            # 2) Detect Function 
            # Find a bounding box over threshold_size value
            stage = self.detect_bounding_boxs(contours)

            # 3) Recognize Function
            # A. Person RPI case
            # Only if there is somthing detected, activate Package Rpi by Person Rpi
            if self.role == "person" and stage == "detecting":
                
                # Check the signal from Package Rpi: package or nothing                      
                package_status_signal = int(self.manage_signal.read_in_signal("status"))
                package_status = self.get_package_status(package_status_signal)

                face_width = self.detect_faces(gray)

                if face_width > self.threshold_reaction_width:
                    
                    # 2) Start recording
                    if self.record_flag == False and self.member_detect == False:
                        self.start_recording(frame)
                        self.play_sound("packop-greeting")
                        
                    
                    # 3) Call recognition
                    # Prepare the frame for sending it over HTTP, then call the send function
                    encodedFrame = cv2.imencode(".jpg", frame)[1].tostring()

                    response_result = []
                    url = self.image_recognition_endpoint + "/send/" + self.role                    
                    response_result = self.__send_frame_for_recognition(url, encodedFrame)
                    
                    if response_result[0] == "nothing":
                        if package_status == "stolen" and self.member_detect == False:
                            self.play_sound("packop-stolen")
                            self.pib_yn = "y"
                    else:                                 
                        # Member Case
                        if response_result[0] == "member": 
                            # Stop recording
                            if self.record_flag:
                                self.stop_recording(False, 'n')

                            # Package was delivered
                            if self.member_detect == False and self.stolen_history == "y":
                                self.play_sound("packop-report")
                                self.stolen_history = "n"
                                self.member_detect = True
                            elif self.member_detect == False and package_status == "keep":
                                self.play_sound("packop-owner")
                                self.member_detect = True
                            elif self.member_detect == False and package_status == "none":
                                self.play_sound("packop-welcome") 
                                self.member_detect = True
                            else:
                                print("Nothing happened")
                        # Stranger Case
                        elif response_result[0] == "stranger":
                            
                            if package_status == "stolen" and self.member_detect == False:
                                self.play_sound("packop-stolen")
                                self.pib_yn = "y"
                            elif package_status == "receive":
                                self.play_sound("packop-thanks")
                                if self.stolen_history == "y":
                                    self.stolen_history = "n"
                            else:
                                print("Nothing happen in stranger case")
                            
                            self.stranger_detect = True
                            self.total_tracking_time = 0
                else:
                    if package_status == "stolen" and self.member_detect == False:
                        self.play_sound("packop-stolen")
                        self.pib_yn = "y"
                    elif package_status == "receive":
                        self.play_sound("packop-thanks")

                        if self.stolen_history == "y":
                            self.stolen_history = "n"

            elif self.role == "person" and stage == "waiting":
                # Check the signal from Package Rpi: package or nothing                      
                package_status_signal = int(self.manage_signal.read_in_signal("status"))
                package_status = self.get_package_status(package_status_signal)
                
                if package_status == "stolen" and self.member_detect == False:
                    self.play_sound("packop-stolen")
                    self.pib_yn = "y"
                elif package_status == "receive":
                    self.play_sound("packop-thanks")
                    if self.stolen_history == "y":
                        self.stolen_history = "n"
                
                if self.record_flag == True:
                    if int(self.total_tracking_time) > int(waiting_time_threshold):
                        if self.stolen_history == "y":
                            self.stop_recording(True, "y")
                        elif self.stranger_detect == True:
                            self.stop_recording(True, "n")
                        else: 
                            self.stop_recording(False, "n")
                        
                        self.stranger_detect = False
                        self.member_detect = False

                    self.update_tracking_time(start_time)
                if self.member_detect == True:
                    if int(self.total_tracking_time) > int(waiting_time_threshold):
                        self.member_detect = False
                    self.update_tracking_time(start_time)

            # B. Package Rpi Function 
            elif self.role == "package" and stage == "detecting":
                encodedFrame = cv2.imencode(".jpg", frame)[1].tostring()

                response_result = []
                url = self.image_recognition_endpoint + "/send/" + self.role                    
                response_result = self.__send_frame_for_recognition(url, encodedFrame)
                # Package is detected
                if response_result[0] == "package":
                    self.manage_signal.set_signal("status", "ON")
                    self.pre_signal_status = "ON"
                    if int(response_result[1]) < self.pre_package_number:
                        self.manage_signal.set_signal("change","ON")
                    else:
                        self.manage_signal.set_signal("change","OFF")
                else:
                    self.manage_signal.set_signal("status", "OFF")
                    self.pre_signal_status = "OFF"
                    self.manage_signal.set_signal("change","OFF")

                self.pre_package_number = int(response_result[1])
            elif self.role == "package" and stage == "waiting":
                if self.pre_signal_status == "":
                    encodedFrame = cv2.imencode(".jpg", frame)[1].tostring()

                    response_result = []
                    url = self.image_recognition_endpoint + "/send/" + self.role                    
                    response_result = self.__send_frame_for_recognition(url, encodedFrame)
                    # Package is detected
                    if response_result[0] == "package":
                        self.manage_signal.set_signal("status", "ON")
                        self.pre_signal_status = "ON"
                        if int(response_result[1]) < int(self.pre_package_number):
                            self.manage_signal.set_signal("change","ON")
                        else:
                            self.manage_signal.set_signal("change","OFF")
                    else:
                        self.manage_signal.set_signal("status", "OFF")
                        self.pre_signal_status = "OFF"
                        self.manage_signal.set_signal("change","OFF")

                    self.pre_package_number = int(response_result[1])
                else:
                    self.manage_signal.set_signal("status", self.pre_signal_status)

            # Disply images via web socket (port:5012) for debugging
            if self.show_video:
                try:
                    self.display_frame = cv2.imencode('.jpg', frame)[1].tobytes()
                except Exception as e:
                    print("Could not display the video to a web browser.") 
                    print('Excpetion -' + str(e)) 
            self.rawCapture.truncate(0)
            
    def display_time_difference_in_ms(self, end_time, start_time):
            return int((end_time-start_time) * 1000)

    def detect_bounding_boxs(self, contours):
        stage = "waiting"
        for c in contours:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < self.threshold_size:
                continue
            stage = "detecting"
        return stage

    def detect_faces(self, gray_frame):
        face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(
            gray_frame,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=(30, 30)
        )
        longest_width = 0
        for (_, _, w, _) in faces:
            if longest_width < w:
                longest_width = w
        return longest_width

    def get_package_status(self, signal):
        status = ""
        if self.pre_package_status == 0 and signal == 0:
            status = "none"
        elif self.pre_package_status == 1 and signal == 0:
            status = "stolen"
            self.stolen_history = "y"
        elif self.pre_package_status == 1 and signal == 1:
            status = "keep"
        elif self.pre_package_status == 0 and signal == 1:
            status = "receive"
        print(status, " = ", str(self.pre_package_status), " = ", str(signal))
        self.pre_package_status = signal
        return status

    def update_tracking_time(self, time):
        if self.pre_tracking_time == 0:
            self.total_tracking_time = 0
        else:
            difference = self.display_time_difference_in_ms(time, self.pre_tracking_time)
            self.total_tracking_time += difference
        self.pre_tracking_time = time
        print("Total_tracking_time: ", str(self.total_tracking_time))

    def start_recording(self, first_frame):
        self.file_name = IdGenerator().gen_transaction_id() + ".h264"
        file_path = video_folder + self.file_name
        self.camera.start_recording(file_path)
        self.record_flag = True
        self.first_frame = first_frame
        print("Start recording :: ", self.file_name)
    
    def stop_recording(self, data_flag, stolen_yn):
        self.record_flag = False
        self.pre_tracking_time = 0
        self.total_tracking_time = 0

        # 1) Stop recording
        self.camera.stop_recording()
        
        # 2) Handling data and video in an extra thread
        data_processor = Processor(self.file_name, data_flag, stolen_yn, self.image_recognition_endpoint, self.first_frame, self.pib_yn)
        data_processor.start()
        self.first_frame = ""
        self.pib_yn = "n"

    def get_display_frame(self):
        return self.display_frame

    def play_sound(self, level):
        path = os.path.dirname(os.path.abspath(__file__))
        sound_file = "audio/{:s}.wav".format(level)
        sound_path = os.path.join(path, sound_file)
        
        def start_thread(sound_path):
            player = OMXPlayer(sound_path)
            time.sleep(1.8)
            player.quit()

        sound_thread = threading.Thread(target=start_thread, args=(sound_path,))
        sound_thread.start()
        time.sleep(1.5)
