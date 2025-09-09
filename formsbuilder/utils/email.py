from django.core.mail import EmailMultiAlternatives
import threading
import logging

logger = logging.getLogger(__name__)

def send_async_email(subject, message, from_email, recipient_list, html_message=None):
    """
    Send email asynchronously with optional HTML content.
    """
    def _send():
        try:
            email = EmailMultiAlternatives(subject, message, from_email, recipient_list)
            if html_message:
                email.attach_alternative(html_message, "text/html")
            email.send()
            logger.debug(f"[✅] Email successfully sent to {recipient_list}")
        except Exception as e:
            logger.error(f"[❌] Failed to send email to {recipient_list}: {str(e)}")

    threading.Thread(target=_send).start()
