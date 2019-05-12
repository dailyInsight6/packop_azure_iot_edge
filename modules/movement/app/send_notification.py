import os
import smtplib
from pyfcm import FCMNotification
import keymanager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Change to your own account information
# EMAIL Account Information
gmail_user = keymanager.MODULE_EMAIL_USERNAME
gmail_password = keymanager.MODULE_EMAIL_PASSWORD

# MOBILE App
MODULE_PUSH_API_KEY = keymanager.MODULE_PUSH_API_KEY
MODULE_PUSH_DEVICE_ID = keymanager.MODULE_PUSH_DEVICE_ID

class Sender(object):
    def __init__(self, type: str):
        self.type = type
        if type == "email":
            self.smtpserver = smtplib.SMTP('smtp.gmail.com', 587)  # Server to use.
            self.smtpserver.ehlo()  # Identify ourselves to smtp gmail client
            self.smtpserver.starttls()  # Secure our email with tls encryption
            self.smtpserver.ehlo()  # Re-identify ourselves as an encrypted connection
            self.smtpserver.login(gmail_user, gmail_password)  # Log in to server
        elif type == "app":
            self.push_service = FCMNotification(api_key=MODULE_PUSH_API_KEY)
        else:
            print("There is no way you request")

    def push_notification(self, msg_title: str, msg_body: str):
        self.push_service.notify_multiple_devices(registration_ids=MODULE_PUSH_DEVICE_ID, message_title=msg_title,
                                               message_body=msg_body)

    def send_email(self, receiver_list: list, subject: str, content: str):
        # Creates the text, subject, 'from', and 'to' of the message.
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = gmail_user
        msg['To'] = ', '.join(receiver_list)
        msg.attach(MIMEText(content, 'html'))

        # Sends the message
        self.smtpserver.send_message(msg)
        # Closes the smtp server.
        self.smtpserver.quit()

    def read_template(self, filename):
        with open(filename, 'r', encoding='utf-8') as template_file:
            template_file_content = template_file.read()
        return template_file_content
