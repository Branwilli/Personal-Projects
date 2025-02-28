import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

HOST = "smtp.gmail.com"
PORT = 587

Sender_email = "bw709788@gmail.com"     
Receiver_email = input("[RECEIVER]: ")
Password = "etnp gaii rkkr djii"

def send_email(): 
    subject = input("Enter subject: ")
    body = """
    Hello, this is a test run to simulate how automated emails are sent.

    Please do not responsed to this email.
    """

    msg = MIMEMultipart()
    msg['From'] = Sender_email
    msg['To'] = Receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    filename = "Customers.csv"
    attachment = open(filename, 'rb')

    attachment_package = MIMEBase('application', 'ocset-stream')
    attachment_package.set_payload((attachment).read())
    encoders.encode_base64(attachment_package)
    attachment_package.add_header('Content-Disposition', "attachment; filename= " + filename)
    msg.attach(attachment_package)
    text = msg.as_string()

    print("[MESSAGE]: Connecting to server...")
    server = smtplib.SMTP(HOST, PORT)
    server.starttls()
    server.login(Sender_email, Password)
    print("[MESSAGE]: Connected to server")

    server.sendmail(Sender_email, Receiver_email, text)
    print(f"Email was successfully sent to {Receiver_email}")
    server.quit()

send_email()
