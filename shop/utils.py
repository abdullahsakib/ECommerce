from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

signer = TimestampSigner()

def send_verification_email(user):
    token = signer.sign(user.pk)
    url = settings.SITE_URL + reverse('verify_email', args=[token])
    send_mail('Verify your email', f'Click to verify: {url}', settings.DEFAULT_FROM_EMAIL, [user.email])

def verify_token(token):
    try:
        user_id = signer.unsign(token, max_age=60*60*24)  # 1 day expiration
        return user_id
    except (BadSignature, SignatureExpired):
        return None