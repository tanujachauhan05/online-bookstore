from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# ---- Choice Constants ----
GENRE_CHOICES = [
    ('romance', 'Romance'),
    ('thriller', 'Thriller'),
    ('fantasy', 'Fantasy'),
    ('fiction', 'Fiction'),
    ('nonfiction', 'Non-fiction'),
    ('horror', 'Horror'),
    ('other', 'Other'),
]

BOOK_TYPE_CHOICES = [
    ('ebook', 'eBook'),
    ('hardcopy', 'Hardcopy'),
]

CATEGORY_CHOICES = [
    ('fiction', 'Fiction'),
    ('nonfiction', 'Non-fiction'),
    ('romance', 'Romance'),
    ('mystery', 'Mystery'),
    ('sci-fi', 'Sci-Fi'),
    ('other', 'Other'),
]

# ---- Book Model ----
class Book(models.Model):
    BOOK_TYPES = (
        ('ebook', 'eBook'),
        ('hardcopy', 'Hard Copy'),
    )

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)  # If not already added
    price = models.DecimalField(max_digits=6, decimal_places=2)

    book_type = models.CharField(
        max_length=10,
        choices=BOOK_TYPES,
        default='hardcopy'
    )

    ebook_file = models.FileField(
        upload_to='ebooks/',
        null=True,
        blank=True
    )

    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True)  # if applicable

    def __str__(self):
        return self.title

    @property
    def ebook_download_price(self):
        """Online eBook purchase price (50% of list price)."""
        return (Decimal(self.price) / 2).quantize(Decimal('0.01'))

    def has_ebook_file(self):
        return bool(self.ebook_file)

# ---- User profile (mobile for SMS notifications) ----
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.username} — {self.phone_number or 'no phone'}"


# ---- CartItem Model ----
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

# ---- Order Model ----
class Order(models.Model):
    PAYMENT_COD = 'cod'
    PAYMENT_ONLINE = 'online'
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_COD, 'Cash on Delivery'),
        (PAYMENT_ONLINE, 'Online (Razorpay)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    books = models.ManyToManyField('Book')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default=PAYMENT_COD,
    )
    is_paid = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


# ---- eBook purchase (pay half price to unlock download) ----
class EbookPurchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ebook_purchases')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='ebook_purchases')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'book'], name='unique_ebook_purchase_per_user'),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.book.title}"


# ---- class review ----
class Review(models.Model):
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1 to 5 stars
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.rating})"