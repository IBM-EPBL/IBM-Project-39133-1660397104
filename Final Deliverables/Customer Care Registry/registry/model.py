from flask_login import UserMixin
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
import os

class Customer(UserMixin):
    def set(self, uuid, first_name, last_name, email, password, date):
        '''
            Method to initialise the Customer
        '''
        self.uuid = uuid
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.date = date

    def get_id(self):
        '''
            Method to return the uuid of the Customer
        '''
        return (self.uuid)
  
class Agent(UserMixin):
    def set(self, uuid, first_name, last_name, email, password, date, confirm):
        '''
            Method to initialise the Agent
        '''
        self.uuid = uuid
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.date = date
        self.confirm = confirm

    def get_id(self):
        '''
            Method to return the uuid of the Agent
        '''
        return (self.uuid)

class Admin(UserMixin):
    def set(self, email, password):
        self.email = email
        self.password = password

    def get_id(self):
        '''
            Method to return the email of the Admin
        '''
        return (self.email)
    
class Mail():
    # mail server essentials
    from .secret import email, password

    smptpHost = "smtp.gmail.com"
    smtpPort = 587
    mailUName = email
    mailPwd = password
    fromMail = email

    # mail body, subject
    mailSubject = ""
    mailContent = ''
    recipient = []

    def sendEmail(self, subject, content, receivers):
        msg = MIMEMultipart()

        msg['From'] = self.fromMail
        msg['To'] = ','.join(receivers)
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'html'))

        # sending the message object
        s = smtplib.SMTP(self.smptpHost, self.smtpPort)
        s.starttls()
        s.login(self.mailUName, self.mailPwd)
        msgText = msg.as_string()
        sendErrs = s.sendmail(self.fromMail, receivers, msgText)

        s.quit()

        return sendErrs