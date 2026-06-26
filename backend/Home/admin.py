from django.contrib import admin
from .models import User, Transaction


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("user_id", "user_name", "net_balance", "transaction_count", "rank_score")
    search_fields = ("user_id", "user_name")
    ordering = ("-rank_score",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "transaction_type", "amount", "idempotency_key", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("user__user_id", "idempotency_key")
    ordering = ("-created_at",)
