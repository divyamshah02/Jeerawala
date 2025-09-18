import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_booking_email(
    gmail_user: str,
    gmail_password: str,
    name: str,
    email: str,
    number: str,
    origin: str,
    destination: str,
    datetime_: str,
    car_type: str,
    trip_type: str,
    return_datetime: str = None,
):
    """
    Sends a booking confirmation email to self (from and to are same).
    """

    # Email content
    subject = "New booking received"
    body = f"""
    New Booking Details:

    Name: {name}
    Email: {email}
    Number: {number}
    Trip Type: {trip_type}
    Car Type: {car_type}
    Origin: {origin}
    Destination: {destination}
    Date & Time: {datetime_}
    Return Date & Time: {return_datetime if return_datetime else 'N/A'}
    """

    # Create message
    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = gmail_user  # sending to self
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Connect to Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, gmail_user, msg.as_string())
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")



# Example usage
if __name__ == "__main__":
    send_booking_email(
        gmail_user="jirawalataxi@gmail.com",
        gmail_password="wmwc owcv fhbu rcgk",  # use App Password, not Gmail password
        name="John Doe",
        email="johndoe@example.com",
        number="+91-9876543210",
        origin="Mumbai",
        destination="Delhi",
        datetime_="2025-09-20 10:30 AM",
        return_datetime="2025-09-25 05:00 PM",
        car_type="Sedan",
        trip_type="One Way",
    )
