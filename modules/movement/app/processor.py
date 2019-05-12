import os
import datetime
import threading
import cv2
# from PIL import Image
import requests
import keymanager

from manage_media import ManageMedia
from manage_data import insert_data, select_data, get_connection, close_connection
from generator import IdGenerator
from send_notification import Sender

video_dir = "video/"
image_dir = "image/"
assigned_device_id = keymanager.MODULE_DEVICE_ID

class Processor(threading.Thread):
    def __init__(self, video_file_name, data_flag, stolen_yn, end_point, first_frame, pib_yn):
        threading.Thread.__init__(self)
        self.file_name = video_file_name
        self.video_manager = ManageMedia("video")
        self.data_flag = data_flag
        self.stolen_yn = stolen_yn
        self.image_recognition_endpoint = end_point
        self.image_manager = ManageMedia("image")
        self.first_frame = first_frame
        self.pib_yn = pib_yn
        print ("Media Processor Created, ", self.file_name)

    def run(self):
        try:
            print ("Media Processor Starts uploading, ", self.data_flag, self.file_name)
            
            if self.data_flag:
                level = "not_used"
                # Video Converting .h264 to .mp4
                tartget_file_name = video_dir + self.file_name
                converted_file_name = video_dir + self.file_name[:-4] + "mp4"
                command = "MP4Box -add {:s} {:s}".format(tartget_file_name, converted_file_name)
                os.system(command)

                # Image creation
                print("image starts")
                image_file_name = image_dir + self.file_name[:-4] + "jpeg"
                cv2.imwrite(image_file_name,self.first_frame)

                # Video Upload
                video_result = self.video_manager.upload([self.file_name[:-4] + "mp4"])

                # Image Upload
                image_result = self.image_manager.upload([self.file_name[:-4] + "jpeg"])
                print ("Media Processor Uploaded", video_result, image_result)

                # Data Manipulation

                #   Update packop_transaction
                generator = IdGenerator()
                transaction_id = self.file_name[:-5]
                transaction_date, transaction_time = generator.gen_date_time() 
                device_id = assigned_device_id
                stolen_yn = self.stolen_yn
                pib_yn = self.pib_yn
                video_blob_url = video_result[0]
                image_blob_url = image_result[0]
                 
                data_dict = [
                                transaction_id,
                                transaction_date,
                                transaction_time,
                                device_id,
                                level,
                                stolen_yn,
                                video_blob_url,
                                image_blob_url,
                                pib_yn
                            ]
                con = get_connection()
                print(data_dict)
                insert_data(con, "packop_transaction", data_dict)

                # # Data for send notification
                target = ["email", "address"]
                condition = {"device_id": device_id}

                result_data = select_data(con, "member", target, condition)

                # Commit and Close connection
                close_connection(con)

                url = self.image_recognition_endpoint + "/save/" + transaction_id     
                response = requests.post(url)
                
                # Send notification
                # Prepare content
                receiver_list = []
                address = ""

                for data in result_data:
                    receiver_list.append(data[0])
                    if address != data[1]:
                        address = data[1]
                
                subject = "Packop Security Alert [ " + address + " ]"
                time = str(transaction_date) + " " + str(transaction_time)

                # Create sender
                # sender = Sender("email")
                # message_template = sender.read_template("templates/mail_body.html")
                # content = message_template.format(time=time, address=address, url=video_blob_url)
                # sender.send_email(receiver_list, subject, content)
                
                # Mobile app notification
                sender = Sender("app")
                msg_title = "Packop Security Alert"
                msg_body = address
                sender.push_notification(msg_title, msg_body)
                
                print ("Media Processor Finishes jobs", response)

            else:
                # Video Delete
                self.video_manager.delete_local("video",[self.file_name])
                # Image Delete
                self.image_manager.delete_local("image",[self.file_name[:-4] + "jpeg"])
                print ("Media Processor Deleted")

            self.close()
            
        except Exception as e:
            print('Video Processor::exited run loop. Exception - '+ str(e))

    def close(self):
        print ("Processor is killed by the request")