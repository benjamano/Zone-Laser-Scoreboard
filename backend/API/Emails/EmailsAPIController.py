import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailsAPIController:
    def __init__(self, gmailUserEmail: str, appPassword: str):
        self.gmailUser = gmailUserEmail
        self.appPassword = appPassword

    def sendEmail(self, toEmailAddress: str, subject: str, body: str) -> bool:
        """
        - Send An Email to a Specified Email Address.
        - Sets the Email Subject to the passed `subject` field.
        - The `body` field is interpreted as HTML code.
        
        """
        
        msg = MIMEMultipart()
        msg["From"] = self.gmailUser
        msg["To"] = toEmailAddress
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.gmailUser, self.appPassword)
            server.sendmail(self.gmailUser, toEmailAddress, msg.as_string())
            server.quit()
            
            return True
        except Exception as e:
            return False