from datetime import timedelta
from decimal import Decimal
import json
import logging

import razorpay
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db.models import Avg, Count, Q, Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from .forms import ReviewForm, SignupForm, SupportContactForm
from .models import Book, CartItem, EbookPurchase, Order, Review, UserProfile
from .notifications import get_user_mobile, send_order_sms

logger = logging.getLogger(__name__)


def _purchased_ebook_ids(user):
    if not user.is_authenticated:
        return set()
    return set(
        EbookPurchase.objects.filter(user=user).values_list('book_id', flat=True)
    )


def _user_can_download_ebook(user, book):
    return EbookPurchase.objects.filter(user=user, book=book).exists()


def _ebook_payment_amount_paise(price):
    amount = int(Decimal(price) * 100)
    return max(amount, 100)


def _create_order(user, books, total_amount=None, payment_method=Order.PAYMENT_COD):
    books = list(books)
    if not books:
        return None
    if total_amount is None:
        total_amount = sum(book.price for book in books)
    is_paid = payment_method == Order.PAYMENT_ONLINE
    order = Order.objects.create(
        user=user,
        total_amount=total_amount,
        payment_method=payment_method,
        is_paid=is_paid,
    )
    order.books.set(books)
    return order


def _payment_method_label(payment_method):
    return dict(Order.PAYMENT_METHOD_CHOICES).get(payment_method, payment_method)


def _send_order_email(request, books, total_price, subject, payment_method):
    """Send confirmation email; returns True if sent. Never blocks checkout on failure."""
    if not request.user.email or not request.user.email.strip():
        logger.warning('Order email skipped: user %s has no email', request.user.username)
        return False
    try:
        context = {
            'user': request.user,
            'books': books,
            'total_price': total_price,
            'payment_method': _payment_method_label(payment_method),
            'is_cod': payment_method == Order.PAYMENT_COD,
        }
        text_content = render_to_string('email/order_confirmation.txt', context)
        html_content = render_to_string('email/order_confirmation.html', context)
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email.strip()],
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)
        return True
    except Exception:
        logger.exception('Order confirmation email failed for %s', request.user.email)
        return False


def _send_order_notifications(request, books, total_price, payment_method, subject, is_ebook=False):
    """Email + SMS after successful order; failures do not block checkout."""
    mobile = request.POST.get('mobile') if request.method == 'POST' else None
    email_sent = _send_order_email(request, books, total_price, subject, payment_method)
    sms_sent = False
    try:
        sms_sent = send_order_sms(
            request.user,
            books,
            total_price,
            payment_method,
            mobile=mobile,
            is_ebook=is_ebook,
        )
    except Exception:
        logger.exception('Order SMS failed for user %s', request.user.username)
    return email_sent, sms_sent


def _complete_cod_order(request, books, total_price):
    mobile = request.POST.get('mobile', '').strip()
    if not get_user_mobile(request.user, mobile or None):
        messages.error(request, 'Please enter a valid 10-digit mobile number for order updates.')
        if len(books) == 1:
            return redirect('book_detail', book_id=books[0].id)
        return redirect('view_cart')

    payment_method = Order.PAYMENT_COD
    _create_order(request.user, books, total_amount=total_price, payment_method=payment_method)
    email_sent, sms_sent = _send_order_notifications(
        request,
        books,
        total_price,
        payment_method,
        'Your Cash on Delivery Order - Online Bookstore',
    )
    return render(request, 'books/order_placed.html', {
        'books': books,
        'total_price': total_price,
        'payment_method': payment_method,
        'is_cod': True,
        'email_sent': email_sent,
        'sms_sent': sms_sent,
        'user_email': request.user.email,
    })


# ------------------- Home Page -------------------
def home(request):
    query = request.GET.get('q')
    book_type = request.GET.get('book_type')
    sort_by = request.GET.get('sort_by')

    books = Book.objects.all()

    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query))
    if book_type:
        books = books.filter(book_type=book_type)

    if sort_by == 'price_asc':
        books = books.order_by('price')
    elif sort_by == 'price_desc':
        books = books.order_by('-price')
    elif sort_by == 'newest':
        books = books.order_by('-id')

    return render(request, 'books/home.html', {
        'books': books,
        'purchased_ebook_ids': _purchased_ebook_ids(request.user),
    })


# ------------------- Signup -------------------
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            UserProfile.objects.create(user=user, phone_number=form.cleaned_data['mobile'])
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'books/signup.html', {'form': form})


def logout_view(request):
    """Log out user (GET or POST). Django's built-in LogoutView only allows POST in Django 5+."""
    auth_logout(request)
    return redirect('home')


def help_support(request):
    """Customer help, FAQ, and contact form."""
    initial = {}
    if request.user.is_authenticated:
        initial['name'] = request.user.get_full_name() or request.user.username
        if request.user.email:
            initial['email'] = request.user.email
    form = SupportContactForm(request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        body = (
            f"Name: {data['name']}\n"
            f"Email: {data['email']}\n\n"
            f"{data['message']}"
        )
        try:
            send_mail(
                subject=f"[BookVerse Support] {data['subject']}",
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.SUPPORT_EMAIL],
                reply_to=[data['email']],
                fail_silently=False,
            )
            messages.success(request, 'Your message was sent. We will reply within 24–48 hours.')
            return redirect('help_support')
        except Exception:
            logger.exception('Support email failed')
            messages.error(request, 'Could not send your message. Please email us directly.')

    return render(request, 'books/help.html', {
        'form': form,
        'support_email': settings.SUPPORT_EMAIL,
        'support_phone': settings.SUPPORT_PHONE,
        'support_hours': settings.SUPPORT_HOURS,
    })


# ------------------- Dashboard -------------------
@login_required
def dashboard_view(request):
    user = request.user
    recent_books = Book.objects.order_by('-id')[:5]
    return render(request, 'books/dashboard.html', {'user': user, 'recent_books': recent_books})


# ------------------- Cart -------------------
@login_required
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if book.book_type == 'hardcopy':
        CartItem.objects.get_or_create(user=request.user, book=book)
        messages.success(request, f'"{book.title}" added to your cart.')
    return redirect('view_cart')


@login_required
def remove_from_cart(request, book_id):
    deleted, _ = CartItem.objects.filter(user=request.user, book_id=book_id).delete()
    if deleted:
        messages.success(request, 'Item removed from your cart.')
    return redirect('view_cart')


@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'books/cart.html', {
        'cart_items': cart_items,
        'user_mobile': profile.phone_number,
    })


# ------------------- Place Single Order (COD) -------------------
@login_required
def place_order_single(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method != 'POST':
        return redirect('book_detail', book_id=book.id)
    if book.book_type != 'hardcopy':
        return redirect('book_detail', book_id=book.id)
    mobile = request.POST.get('mobile', '').strip()
    if not get_user_mobile(request.user, mobile or None):
        messages.error(request, 'Please enter a valid 10-digit mobile number for order SMS updates.')
        return redirect('book_detail', book_id=book.id)
    return _complete_cod_order(request, [book], book.price)


# ------------------- Place Order from Cart -------------------
@login_required
def place_order_cart(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('book')
    if request.method != 'POST':
        return redirect('view_cart')

    ordered_books = [item.book for item in cart_items]
    if not ordered_books:
        return redirect('view_cart')

    payment_method = request.POST.get('payment_method', Order.PAYMENT_COD)
    if payment_method == Order.PAYMENT_ONLINE:
        return redirect('make_payment')

    total_price = sum(book.price for book in ordered_books)
    cart_items.delete()
    return _complete_cod_order(request, ordered_books, total_price)


# ------------------- Order History -------------------
@login_required
def order_history(request):
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related('books')
        .order_by('-created_at')
    )
    return render(request, 'books/order_history.html', {'orders': orders})


# ------------------- Book Detail with Review -------------------
@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    reviews = book.reviews.all()
    form = ReviewForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.book = book
        review.user = request.user
        review.save()
        return redirect('book_detail', book_id=book.id)

    average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    return render(request, 'books/book_detail.html', {
        'book': book,
        'reviews': reviews,
        'form': form,
        'average_rating': average_rating,
        'owns_ebook': _user_can_download_ebook(request.user, book),
        'ebook_price': book.ebook_download_price,
        'user_mobile': profile.phone_number,
    })


@staff_member_required
def admin_dashboard(request):
    today = now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    labels = [d.strftime('%b %d') for d in last_7_days]

    data = []
    for day in last_7_days:
        count = Order.objects.filter(created_at__date=day).count()
        data.append(count)

    total_orders = Order.objects.count()
    total_users = User.objects.count()
    total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0

    return render(request, 'books/admin_dashboard.html', {
        'labels_json': mark_safe(json.dumps(labels)),
        'data_json': mark_safe(json.dumps(data)),
        'total_orders': total_orders,
        'total_users': total_users,
        'total_revenue': total_revenue,
    })


# ------------------- Payment -------------------
@login_required
def make_payment(request, book_id=None):
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    if book_id:
        book = get_object_or_404(Book, id=book_id)
        total_price = Decimal(book.price)
        context_books = [book]
    else:
        cart_items = CartItem.objects.filter(user=request.user).select_related('book')
        context_books = [item.book for item in cart_items]
        if not context_books:
            return redirect('view_cart')
        total_price = sum(Decimal(item.book.price) for item in cart_items)

    amount = int(total_price * 100)
    if amount < 100:
        return redirect('view_cart')

    payment = client.order.create({
        'amount': amount,
        'currency': 'INR',
        'payment_capture': '1',
    })

    return render(request, 'books/payment_page.html', {
        'payment': payment,
        'amount': total_price,
        'books': context_books,
        'book_id': book_id,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    })


def payment_success(request):
    return render(request, 'books/payment_success.html')


# ------------------- eBook: pay 50% then download -------------------
@login_required
def buy_ebook(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if not book.ebook_file:
        return redirect('book_detail', book_id=book.id)
    if _user_can_download_ebook(request.user, book):
        return redirect('download_ebook', book_id=book.id)

    ebook_price = book.ebook_download_price
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    payment = client.order.create({
        'amount': _ebook_payment_amount_paise(ebook_price),
        'currency': 'INR',
        'payment_capture': '1',
        'notes': {'book_id': str(book.id), 'user_id': str(request.user.id)},
    })

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'books/ebook_payment_page.html', {
        'book': book,
        'payment': payment,
        'amount': ebook_price,
        'full_price': book.price,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'user_mobile': profile.phone_number,
    })


@login_required
def ebook_payment_verify(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method != 'POST':
        return redirect('buy_ebook', book_id=book.id)

    if _user_can_download_ebook(request.user, book):
        return redirect('download_ebook', book_id=book.id)

    payment_id = request.POST.get('razorpay_payment_id', '')
    order_id = request.POST.get('razorpay_order_id', '')
    signature = request.POST.get('razorpay_signature', '')

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature,
        })
    except razorpay.errors.SignatureVerificationError:
        return render(request, 'books/ebook_payment_failed.html', {'book': book})

    EbookPurchase.objects.get_or_create(
        user=request.user,
        book=book,
        defaults={
            'amount_paid': book.ebook_download_price,
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature,
        },
    )

    email_sent, sms_sent = _send_order_notifications(
        request,
        [book],
        book.ebook_download_price,
        Order.PAYMENT_ONLINE,
        'Your eBook Purchase - Online Bookstore',
        is_ebook=True,
    )

    return render(request, 'books/ebook_payment_success.html', {
        'book': book,
        'email_sent': email_sent,
        'sms_sent': sms_sent,
        'user_email': request.user.email,
    })


@login_required
def download_ebook(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if not book.ebook_file:
        raise Http404('eBook file not available.')
    if not _user_can_download_ebook(request.user, book):
        return redirect('buy_ebook', book_id=book.id)

    return FileResponse(
        book.ebook_file.open('rb'),
        as_attachment=True,
        filename=book.ebook_file.name.split('/')[-1],
    )
