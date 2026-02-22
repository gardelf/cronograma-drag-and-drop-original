"""
Email Sender
Handles sending the daily agenda via email
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional


class EmailSender:
    """Send emails with the daily agenda"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        """
        Initialize email sender
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            username: SMTP username (usually email address)
            password: SMTP password or app-specific password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_agenda(self, recipient: str, agenda_html: str, subject: Optional[str] = None) -> bool:
        """
        Send the daily agenda via email
        
        Args:
            recipient: Recipient email address
            agenda_html: HTML content of the agenda
            subject: Email subject (optional, will use default with date)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not subject:
            today = datetime.now().strftime("%d/%m/%Y")
            subject = f"📅 Tu Agenda del Día - {today}"
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.username
            msg['To'] = recipient
            
            # Add HTML content
            html_part = MIMEText(agenda_html, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Send email
            if self.smtp_server and self.username and self.password:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg)
                
                print(f"✅ Email sent successfully to {recipient}")
                return True
            else:
                # If no SMTP configured, just print the HTML
                print("⚠️ SMTP not configured. Email content:")
                print(f"To: {recipient}")
                print(f"Subject: {subject}")
                print(f"Content preview: {agenda_html[:200]}...")
                return False
                
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def send_test_email(self, recipient: str) -> bool:
        """
        Send a test email to verify configuration
        
        Args:
            recipient: Recipient email address
            
        Returns:
            True if sent successfully, False otherwise
        """
        test_html = """
        <html>
        <body>
            <h1>✅ Test Email</h1>
            <p>This is a test email from your Daily Agenda Automation system.</p>
            <p>If you received this, your email configuration is working correctly!</p>
        </body>
        </html>
        """
        
        return self.send_agenda(recipient, test_html, "Test Email - Daily Agenda Automation")


if __name__ == "__main__":
    # Test the email sender
    from config import get_config
    
    config = get_config()
    
    # For testing without SMTP, we'll just print
    sender = EmailSender(
        smtp_server=config['SMTP_SERVER'],
        smtp_port=config['SMTP_PORT'],
        username=config['SMTP_USERNAME'],
        password=config['SMTP_PASSWORD']
    )
    
    test_html = """
    <html>
    <body>
        <h1>📅 Agenda del Día</h1>
        <p>This is a test agenda.</p>
    </body>
    </html>
    """
    
    recipient = config['RECIPIENT_EMAIL']
    if recipient:
        sender.send_agenda(recipient, test_html)
    else:
        print("RECIPIENT_EMAIL not configured")
