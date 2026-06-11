import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)


def normalize_phone(phone):
    """Return E.164-style number for India (+91...) or None if invalid."""
    if not phone:
        return None
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) == 10 and digits[0] in '6789':
        return f'+91{digits}'
    if len(digits) == 12 and digits.startswith('91'):
        return f'+{digits}'
    if len(digits) == 11 and digits.startswith('0'):
        return f'+91{digits[1:]}'
    return None


def send_sms(phone, message):
    """
    Send SMS to phone. Uses Twilio when configured; otherwise logs to console.
    Returns True if sent or logged successfully.
    """
    normalized = normalize_phone(phone)
    if not normalized:
        logger.warning('Invalid phone number for SMS: %r', phone)
        return False

    if not getattr(settings, 'SMS_ENABLED', False):
        print(f'\n[SMS to {normalized}]\n{message}\n')
        return True

    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=normalized,
        )
        return True
    except Exception as exc:
        logger.exception('SMS send failed: %s', exc)
        print(f'\n[SMS FAILED — logged to console]\nTo: {normalized}\n{message}\n')
        return False
