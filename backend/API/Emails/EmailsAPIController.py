import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

class EmailsAPIController:
    def __init__(self, appPassword: str, gmailUserEmail: str, senderName : str):
        self.senderName = senderName
        self.gmailUser = gmailUserEmail
        self.appPassword = appPassword

    def sendEmail(self, toEmailAddress: str, subject: str, body: str) -> bool:
        """
        - Send An Email to a Specified Email Address.
        - Sets the Email Subject to the passed `subject` field.
        - The `body` field is interpreted as HTML code.
        """
        
        msg = MIMEMultipart()
        msg["From"] = formataddr((self.senderName, self.gmailUser))
        msg["To"] = toEmailAddress.strip().strip("\n")
        msg["Subject"] = subject.strip().strip("\n")
        msg.attach(MIMEText(body, "html"))
        # msg.attach(MIMEText(body, 'plain'))
        # msg.add_header('X-Priority', '1')

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.gmailUser, self.appPassword)
            server.sendmail(self.gmailUser, toEmailAddress, msg.as_string())
            server.quit()
            
            return True
        except Exception:
            raise