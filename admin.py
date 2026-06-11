from django.contrib import admin
from .models import Book, EbookPurchase, Order, UserProfile


class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'book_type')
    list_filter = ('book_type',)
    search_fields = ('title', 'author')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'payment_method', 'is_paid', 'created_at')
    list_filter = ('payment_method', 'is_paid')
    filter_horizontal = ('books',)


class EbookPurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'amount_paid', 'purchased_at')
    list_filter = ('purchased_at',)
    search_fields = ('user__username', 'book__title')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')
    search_fields = ('user__username', 'phone_number')


admin.site.register(Book, BookAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(EbookPurchase, EbookPurchaseAdmin)
