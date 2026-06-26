import re
from rest_framework import serializers
from .models import User, Transaction


class TransactionInputSerializer(serializers.Serializer):
    """Validates the POST /transaction payload."""
    user_id = serializers.CharField(max_length=64)
    idempotency_key = serializers.CharField(max_length=128)
    transaction_type = serializers.ChoiceField(choices=["credit", "debit"])
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    descriptions = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )

    def validate_user_id(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("User ID cannot be empty.")
        if not re.match(r'^[A-Za-z0-9_-]+$', value):
            raise serializers.ValidationError(
                "User ID must contain only alphanumeric characters, hyphens, or underscores."
            )
        return value

    def validate_idempotency_key(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Idempotency key cannot be empty.")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be a positive number.")
        if value > 1_000_000:
            raise serializers.ValidationError(
                "Amount cannot exceed the single-transaction limit of 1,000,000."
            )
        return value


class TransactionOutputSerializer(serializers.ModelSerializer):
    transaction_id = serializers.UUIDField(source="id", read_only=True)
    user_id = serializers.CharField(source="user.user_id", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "transaction_id",
            "user_id",
            "idempotency_key",
            "amount",
            "transaction_type",
            "descriptions",
            "created_at",
        ]


class UserSummarySerializer(serializers.ModelSerializer):
    recent_transactions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "user_id",
            "user_name",
            "total_credits",
            "total_debits",
            "transaction_count",
            "net_balance",
            "rank_score",
            "recent_transactions",
        ]

    def get_recent_transactions(self, obj):
        txns = obj.transactions.order_by("-created_at")[:10]
        return TransactionOutputSerializer(txns, many=True).data


class UserRankSerializer(serializers.ModelSerializer):
    score_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "user_id",
            "user_name",
            "net_balance",
            "transaction_count",
            "rank_score",
            "score_breakdown",
        ]

    def get_score_breakdown(self, obj):
        from .ranking import compute_score_breakdown
        return compute_score_breakdown(obj)
