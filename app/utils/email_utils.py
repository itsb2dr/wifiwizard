import smtplib
from email.message import EmailMessage

EMAIL_ADDRESS = 'officialwifiwizard@gmail.com'
EMAIL_PASSWORD = 'qzlpwmqzascuvobc'  # Use an app password if using Gmail

def send_email(to_email, subject, content):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(content)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


def send_verification_email(to_email, code):
    subject = 'Your Verification Code'
    content = f'Your verification code is: {code}'
    send_email(to_email, subject, content)


def send_reset_code_email(to_email, code):
    subject = 'Your Password Reset Code'
    content = f'Your password reset code is: {code}'
    send_email(to_email, subject, content)
