import smtplib
from email.message import EmailMessage

EMAIL_ADDRESS = 'officialwifiwizard@gmail.com'
EMAIL_PASSWORD = 'svtnceepxiywivci'  # Use app password

def send_email(to_email, subject, content, html=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(content)
    if html:
        msg.add_alternative(html, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


def send_verification_email(to_email, code):
    subject = 'WiFi Wizard Verification Code'
    plain = f"Your WiFi Wizard verification code is: {code}"

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9f9fb; padding: 30px;">
      <div style="max-width: 500px; margin: auto; background: white; padding: 24px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
        <h2 style="color: #0a0a23;">WiFi Wizard Verification</h2>
        <p style="font-size: 15px; color: #333;">Thank you for signing up. Please use the verification code below:</p>
        <div style="font-size: 22px; font-weight: bold; margin: 20px 0; background: #00bfff; color: white; padding: 12px; border-radius: 8px; text-align: center;">
          {code}
        </div>
        <p style="font-size: 13px; color: #777;">If you didn't request this, you can ignore this message.</p>
        <p style="font-size: 13px; color: #999;">– The WiFi Wizard Team</p>
      </div>
    </body>
    </html>
    """
    send_email(to_email, subject, plain, html)


def send_reset_code_email(to_email, code):
    subject = 'WiFi Wizard Password Reset Code'
    plain = f"Your WiFi Wizard password reset code is: {code}"

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9f9fb; padding: 30px;">
      <div style="max-width: 500px; margin: auto; background: white; padding: 24px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
        <h2 style="color: #0a0a23;">Reset Your WiFi Wizard Password</h2>
        <p style="font-size: 15px; color: #333;">We received a request to reset your password. Use the code below:</p>
        <div style="font-size: 22px; font-weight: bold; margin: 20px 0; background: #dc3545; color: white; padding: 12px; border-radius: 8px; text-align: center;">
          {code}
        </div>
        <p style="font-size: 13px; color: #777;">If you didn't request this, please ignore this message.</p>
        <p style="font-size: 13px; color: #999;">– The WiFi Wizard Team</p>
      </div>
    </body>
    </html>
    """
    send_email(to_email, subject, plain, html)
