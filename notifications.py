from django.conf import settings

from .models import Order, UserProfile
from .sms import send_sms


def get_user_mobile(user, mobile_from_request=None):
    mobile = (mobile_from_request or '').strip()
    if mobile:
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.phone_number != mobile:
            profile.phone_number = mobile
            profile.save(update_fields=['phone_number'])
        return mobile
    profile = UserProfile.objects.filter(user=user).first()
    return profile.phone_number if profile else ''


def _book_titles_short(books, max_titles=2):
    titles = [b.title[:25] for b in books[:max_titles]]
    if len(books) > max_titles:
        titles.append(f'+{len(books) - max_titles} more')
    return ', '.join(titles)


def build_order_sms_message(user, books, total_price, payment_method, is_ebook=False):
    titles = _book_titles_short(books)
    name = user.get_short_name() or user.username
    pay_label = dict(Order.PAYMENT_METHOD_CHOICES).get(payment_method, payment_method)

    if is_ebook:
        return (
            f"Hi {name}, your eBook purchase is confirmed: {titles}. "
            f"Paid Rs.{total_price} online. You can download now. - Online Bookstore"
        )
    if payment_method == Order.PAYMENT_COD:
        return (
            f"Hi {name}, order placed successfully! {titles}. "
            f"Total Rs.{total_price}. Pay cash on delivery. - Online Bookstore"
        )
    return (
        f"Hi {name}, order confirmed! {titles}. "
        f"Total Rs.{total_price}. Payment: {pay_label}. - Online Bookstore"
    )


def send_order_sms(user, books, total_price, payment_method, mobile=None, is_ebook=False):
    phone = get_user_mobile(user, mobile)
    if not phone:
        return False
    message = build_order_sms_message(user, books, total_price, payment_method, is_ebook=is_ebook)
    return send_sms(phone, message)
