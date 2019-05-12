# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

####################################################################################
# Version Control
# - File name: main.py
# - Creator: koreattle
# - Feb 5 2019: koreattle: Created
####################################################################################
import random
import time
import datetime
import sys
import os
import iothub_client
# pylint: disable=E0611
from iothub_client import IoTHubModuleClient, IoTHubClientError, IoTHubTransportProvider
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError

from detect_movement import DetectMovement

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubModuleClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

# global counters
RECEIVE_CALLBACKS = 0
SEND_CALLBACKS = 0

# Choose HTTP, AMQP or MQTT as transport protocol.  Currently only MQTT is supported.
PROTOCOL = IoTHubTransportProvider.MQTT

# Callback received when the message that we're forwarding is processed.
def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    print ( "Confirmation[%d] received for message with result = %s" % (user_context, result) )
    map_properties = message.properties()
    key_value_pair = map_properties.get_internals()
    print ( "    Properties: %s" % key_value_pair )
    SEND_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % SEND_CALLBACKS )


# receive_message_callback is invoked when an incoming message arrives on the specified 
# input queue (in the case of this sample, "input1").  Because this is a filter module, 
# we will forward this message onto the "output1" queue.
def receive_message_callback(message, hubManager):
    global RECEIVE_CALLBACKS
    message_buffer = message.get_bytearray()
    size = len(message_buffer)
    print ( "    Data: <<<%s>>> & Size=%d" % (message_buffer[:size].decode('utf-8'), size) )
    map_properties = message.properties()
    key_value_pair = map_properties.get_internals()
    print ( "    Properties: %s" % key_value_pair )
    RECEIVE_CALLBACKS += 1
    print ( "    Total calls received: %d" % RECEIVE_CALLBACKS )
    hubManager.forward_event_to_output("output1", message, 0)
    return IoTHubMessageDispositionResult.ACCEPTED

# Send messages to Hub 
def send_to_hub_callback(strMessage):
    message = IoTHubMessage(bytearray(strMessage, 'utf8'))
    hub_manager.forward_event_to_output("output1", message, 0)

def __convertStringToBool(env):
    if env in ['True', 'TRUE', '1', 'y', 'YES', 'Y', 'Yes']:
        return True
    elif env in ['False', 'FALSE', '0', 'n', 'NO', 'N', 'No']:
        return False
    else:
        raise ValueError('Could not convert string to bool.')

class HubManager(object):

    def __init__(
            self,
            protocol=IoTHubTransportProvider.MQTT):
        self.client_protocol = protocol
        self.client = IoTHubModuleClient()
        self.client.create_from_environment(protocol)

        # set the time until a message times out
        self.client.set_option("messageTimeout", MESSAGE_TIMEOUT)
        
        # sets the callback when a message arrives on "input1" queue.  Messages sent to 
        # other inputs or to the default will be silently discarded.
        self.client.set_message_callback("input1", receive_message_callback, self)

    # Forwards the message received onto the next stage in the process.
    def forward_event_to_output(self, outputQueueName, event, send_context):
        self.client.send_event_async(
            outputQueueName, event, send_confirmation_callback, send_context)

def main(protocol,
        resolution_width="",
        resolution_height="",
        frame_rate="",
        threshold_person_box_size="",
        threshold_package_box_size="",
        threshold_reaction_width="",
        image_recognition_endpoint="",
        role="",
        show_video=False):
    try:
        try:
            print ( "IoT Hub Client for Python" )
            
            global hub_manager
            hub_manager = HubManager(protocol)

            print ( "Starting the IoT Hub Python sample using protocol %s..." % hub_manager.client_protocol )
            print ( "The sample is now waiting for messages and will indefinitely.  Press Ctrl-C to exit. ")

            print (datetime.datetime.now())
        except IoTHubError as iothub_error:
            print ( "Unexpected error %s from IoTHub" % iothub_error )
            return
        with DetectMovement(resolution_width, resolution_height, frame_rate, threshold_person_box_size,
                            threshold_package_box_size, threshold_reaction_width, image_recognition_endpoint,
                            role, send_to_hub_callback, show_video) as camera_capture:
                camera_capture.start()
    except KeyboardInterrupt:
        print ("Camera capture module stopped")

if __name__ == '__main__':
    try:
        # VIDEO_PATH = os.environ['VIDEO_PATH']
        RESOLUTION_WIDTH = int(os.getenv('RESOLUTION_WIDTH', ""))
        RESOLUTION_HEIGHT = int(os.getenv('RESOLUTION_HEIGHT', ""))
        FRAME_RATE = int(os.getenv('FRAME_RATE', ""))
        THRESHOLD_PERSON_BOX_SIZE = int(os.getenv('THRESHOLD_PERSON_BOX_SIZE', ""))
        THRESHOLD_PACKAGE_BOX_SIZE = int(os.getenv('THRESHOLD_PACKAGE_BOX_SIZE', ""))
        THRESHOLD_REACTION_WIDTH = int(os.getenv('THRESHOLD_REACTION_WIDTH', ""))
        
        IMAGE_RECOGNITION_ENDPOINT = os.getenv('IMAGE_RECOGNITION_ENDPOINT', "")
        SHOW_VIDEO = __convertStringToBool(os.getenv('SHOW_VIDEO', 'False'))
        ROLE = os.getenv('ROLE', "")

    except ValueError as error:
        print(error)
        sys.exit(1)
    print (datetime.datetime.now())
    main(PROTOCOL, RESOLUTION_WIDTH, RESOLUTION_HEIGHT, FRAME_RATE, THRESHOLD_PERSON_BOX_SIZE, THRESHOLD_PACKAGE_BOX_SIZE, THRESHOLD_REACTION_WIDTH, IMAGE_RECOGNITION_ENDPOINT, ROLE, SHOW_VIDEO)