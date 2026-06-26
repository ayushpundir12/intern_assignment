from django.db import models
from uuid import uuid4


class User(models.Model):
    user_id = models.CharField(max_length=64, unique=True)
    user_name = models.CharField(blank=False, max_length=50)
    total_credits = models.DecimalField(max_digits=18, decimal_places=5, default=0)
    total_debits = models.DecimalField(max_digits=18, decimal_places=5, default=0)
    transaction_count = models.IntegerField(default=0)
    net_balance = models.DecimalField(max_digits=18, decimal_places=5, default=0)
    rank_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["-rank_score"])]

    def __str__(self):
        return f"{self.user_id} ({self.user_name})"


class Transaction(models.Model):
    CREDIT = "credit"
    DEBIT = "debit"

    TYPE_CHOICES = [
        (CREDIT, "Credit"),
        (DEBIT, "Debit"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    idempotency_key = models.CharField(max_length=128)
    transaction_type = models.CharField(max_length=6, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    descriptions = models.CharField(max_length=256, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "idempotency_key")]
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return f"{self.transaction_type} {self.amount} for {self.user.user_id}"
