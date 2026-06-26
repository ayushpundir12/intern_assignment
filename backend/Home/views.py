import threading

from django.db import transaction as db_transaction, IntegrityError
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle

from .models import User, Transaction
from .serializers import (
    TransactionInputSerializer,
    TransactionOutputSerializer,
    UserSummarySerializer,
    UserRankSerializer,
)
from .ranking import compute_rank_score

# per-user locks to handle concurrent requests for the same user
_user_locks: dict[str, threading.Lock] = {}
_map_lock = threading.Lock()


def _get_user_lock(user_id: str) -> threading.Lock:
    with _map_lock:
        if user_id not in _user_locks:
            _user_locks[user_id] = threading.Lock()
        return _user_locks[user_id]


class TransactionThrottle(AnonRateThrottle):
    rate = "60/min"


class ReadThrottle(AnonRateThrottle):
    rate = "120/min"


class TransactionView(APIView):
    throttle_classes = [TransactionThrottle]

    def post(self, request):
        serializer = TransactionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "error", "message": "Validation failed", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        user_id_str = data["user_id"]
        idem_key = data["idempotency_key"]

        user_lock = _get_user_lock(user_id_str)

        with user_lock:
            try:
                with db_transaction.atomic():
                    user, _ = User.objects.get_or_create(
                        user_id=user_id_str,
                        defaults={"user_name": user_id_str},
                    )

                    # lock this user's row until we're done
                    user = User.objects.select_for_update().get(pk=user.pk)

                    # check if this request was already processed
                    existing = Transaction.objects.filter(
                        user=user, idempotency_key=idem_key
                    ).first()

                    if existing:
                        return Response(
                            {
                                "status": "duplicate",
                                "message": "This idempotency_key was already processed.",
                                "transaction": TransactionOutputSerializer(existing).data,
                            },
                            status=status.HTTP_200_OK,
                        )

                    txn = Transaction.objects.create(
                        user=user,
                        amount=data["amount"],
                        transaction_type=data["transaction_type"],
                        idempotency_key=idem_key,
                        descriptions=data.get("descriptions", ""),
                    )

                    # update user totals using F() so it's safe under concurrency
                    if data["transaction_type"] == Transaction.CREDIT:
                        user.total_credits = F("total_credits") + data["amount"]
                        user.net_balance = F("net_balance") + data["amount"]
                    else:
                        user.total_debits = F("total_debits") + data["amount"]
                        user.net_balance = F("net_balance") - data["amount"]

                    user.transaction_count = F("transaction_count") + 1
                    user.save(
                        update_fields=[
                            "total_credits", "total_debits",
                            "net_balance", "transaction_count",
                        ]
                    )

                    # need fresh values from db before computing rank
                    user.refresh_from_db()
                    user.rank_score = compute_rank_score(user)
                    user.save(update_fields=["rank_score"])

                return Response(
                    {
                        "status": "success",
                        "transaction": TransactionOutputSerializer(txn).data,
                    },
                    status=status.HTTP_201_CREATED,
                )

            except IntegrityError:
                # race condition: another thread inserted the same idempotency key
                existing = Transaction.objects.filter(
                    user__user_id=user_id_str, idempotency_key=idem_key
                ).first()

                if existing:
                    return Response(
                        {
                            "status": "duplicate",
                            "message": "This idempotency_key was already processed (concurrent duplicate).",
                            "transaction": TransactionOutputSerializer(existing).data,
                        },
                        status=status.HTTP_200_OK,
                    )
                return Response(
                    {"status": "error", "message": "Transaction could not be saved."},
                    status=status.HTTP_409_CONFLICT,
                )


class UserSummaryView(APIView):
    throttle_classes = [ReadThrottle]

    def get(self, request, user_id: str):
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response(
                {"status": "not_found", "message": f"User '{user_id}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # rank = how many users score higher + 1
        rank = User.objects.filter(rank_score__gt=user.rank_score).count() + 1
        total_users = User.objects.count()

        data = UserSummarySerializer(user).data
        data["rank"] = rank
        data["total_users"] = total_users
        return Response(data, status=status.HTTP_200_OK)


class RankingView(APIView):
    throttle_classes = [ReadThrottle]

    def get(self, request):
        limit = request.query_params.get("limit", "20")
        try:
            limit = max(1, min(int(limit), 100))
        except ValueError:
            return Response(
                {"error": "limit must be a positive integer (max 100)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        users = User.objects.order_by("-rank_score")[:limit]
        entries = []
        for rank, user in enumerate(users, start=1):
            data = UserRankSerializer(user).data
            data["rank"] = rank
            entries.append(data)

        return Response(
            {"ranking": entries, "total_users": User.objects.count()},
            status=status.HTTP_200_OK,
        )
