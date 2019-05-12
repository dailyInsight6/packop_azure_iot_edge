## This module is for communicating from RPI Package to RPI Person
import os
import time
import RPi.GPIO as GPIO

## Manage Signal objects can set one signal going out from the object and read one signal coming into the object
## Objects should take one of two roles, "PERSON" or "PACKAGE", depending on which RPI they are on.
class ManageSignal(object):

    # Expected arguments
    # role: "person" or "package"
    def __init__(self, role = ""):

        # check if role is a string
        if isinstance(role, str):
            # instantiate instance variables
            self.role = role

            # set pin mapping and values
            GPIO.setmode(GPIO.BCM)
            # set pins roles
            if self.role == "person":
                self.pin_to_read_status = 17
                self.pin_to_read_change = 27
                GPIO.setup(self.pin_to_read_status, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                GPIO.setup(self.pin_to_read_change, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            elif self.role == "package":
                self.pin_to_set_status = 17
                self.pin_to_set_change = 27
                GPIO.setup(self.pin_to_set_status, GPIO.OUT)
                GPIO.output(self.pin_to_set_status, GPIO.LOW)
                GPIO.setup(self.pin_to_set_change, GPIO.OUT)
                GPIO.output(self.pin_to_set_change, GPIO.LOW)
            else:
                print("WARNING! Role must be either \"person\" or \"package\".")
            
            print("ManageSignal object created : ", self.role)
        else:
            print("WARNING! Role must be a string, pins must be integers.")

    ## Toggles signal going out from object on or off.
    def set_signal(self, target, state: str):
        # check arg is a string
        if isinstance(target, str) and isinstance(state, str):
            pin_to_set = ""
            if target == "status":
                pin_to_set = self.pin_to_set_status
            elif target == "change":
                pin_to_set = self.pin_to_set_change

            # if arg "on", turn signal on
            if state == "ON":
                GPIO.output(pin_to_set, GPIO.HIGH)
                # print("Signal is on.")
            # if arg "off", turn signal off
            elif state == "OFF":
                GPIO.output(pin_to_set, GPIO.LOW)
                # print("Signal is off.")
            else:
                print("WARNING! State must be \"on\" or \"off\"")
        else:
            print("WARNING! State must be \"on\" or \"off\"")

    ## Returns the signal coming into object
    def read_in_signal(self, target):
        pin_to_read = ""
        if target == "status":
            pin_to_read = self.pin_to_read_status
        elif target == "change":
            pin_to_read = self.pin_to_read_change
        signal = GPIO.input(pin_to_read)
        print("Signal coming in is ", target, " ===== " + str(signal))
        return signal

    ## (For test and debug) Returns the signal going out from object 
    def read_out_signal(self, target):
        pin_to_set = ""
        if target == "status":
            pin_to_set = self.pin_to_set_status
        elif target == "change":
            pin_to_set = self.pin_to_set_change
        signal = GPIO.input(pin_to_set)
        # print("Signal going out is " + str(signal))
        return signal

    ## Cleans up pins and board
    def cleanup(self, target):
        if target == "package":
            GPIO.output(self.pin_to_set_status, GPIO.LOW)
            GPIO.output(self.pin_to_set_change, GPIO.LOW)
        GPIO.cleanup()
        print("Pins cleaned up.")