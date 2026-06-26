"""
Seed script — populates the database with demo users and transactions.

Usage:
    cd backend
    python manage.py shell < seed_data.py

Assumptions / Mock Data Documentation:
    - 5 demo users are created with readable names.
    - Each user gets 3-6 transactions (mix of credits and debits).
    - Amounts are realistic (₹500 – ₹50,000).
    - Idempotency keys are pre-defined so re-running the script is safe
      (duplicates are silently skipped via get_or_create).
    - Rank scores are computed after all transactions are inserted.
"""

import os
import sys
import django

# Ensure Django settings are loaded when running as a standalone script
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from decimal import Decimal
from Home.models import User, Transaction
from Home.ranking import compute_rank_score

SEED_USERS = [
    {"user_id": "alice_001", "user_name": "Alice Johnson"},
    {"user_id": "bob_0002", "user_name": "Bob Smith"},
    {"user_id": "carol_003", "user_name": "Carol Davis"},
    {"user_id": "dave_0004", "user_name": "Dave Wilson"},
    {"user_id": "eve_00005", "user_name": "Eve Martinez"},
]

SEED_TRANSACTIONS = [
    # Alice — high balance, moderate activity
    {"user_id": "alice_001", "idem": "seed-alice-1", "type": "credit", "amount": "50000.00", "desc": "Salary deposit"},
    {"user_id": "alice_001", "idem": "seed-alice-2", "type": "debit",  "amount": "1200.00",  "desc": "Rent payment"},
    {"user_id": "alice_001", "idem": "seed-alice-3", "type": "credit", "amount": "5000.00",  "desc": "Freelance project"},
    {"user_id": "alice_001", "idem": "seed-alice-4", "type": "debit",  "amount": "800.00",   "desc": "Groceries"},

    # Bob — moderate balance, high activity
    {"user_id": "bob_0002", "idem": "seed-bob-1", "type": "credit", "amount": "25000.00", "desc": "Monthly salary"},
    {"user_id": "bob_0002", "idem": "seed-bob-2", "type": "debit",  "amount": "3000.00",  "desc": "Electronics purchase"},
    {"user_id": "bob_0002", "idem": "seed-bob-3", "type": "credit", "amount": "1500.00",  "desc": "Cashback reward"},
    {"user_id": "bob_0002", "idem": "seed-bob-4", "type": "debit",  "amount": "500.00",   "desc": "Subscription"},
    {"user_id": "bob_0002", "idem": "seed-bob-5", "type": "credit", "amount": "7500.00",  "desc": "Bonus"},
    {"user_id": "bob_0002", "idem": "seed-bob-6", "type": "debit",  "amount": "2000.00",  "desc": "Dining out"},

    # Carol — low balance, few transactions
    {"user_id": "carol_003", "idem": "seed-carol-1", "type": "credit", "amount": "8000.00",  "desc": "Part-time income"},
    {"user_id": "carol_003", "idem": "seed-carol-2", "type": "debit",  "amount": "6500.00",  "desc": "Tuition fee"},
    {"user_id": "carol_003", "idem": "seed-carol-3", "type": "credit", "amount": "2000.00",  "desc": "Gift received"},

    # Dave — very high balance, moderate activity
    {"user_id": "dave_0004", "idem": "seed-dave-1", "type": "credit", "amount": "100000.00", "desc": "Investment return"},
    {"user_id": "dave_0004", "idem": "seed-dave-2", "type": "debit",  "amount": "15000.00",  "desc": "Car insurance"},
    {"user_id": "dave_0004", "idem": "seed-dave-3", "type": "credit", "amount": "40000.00",  "desc": "Consulting fee"},
    {"user_id": "dave_0004", "idem": "seed-dave-4", "type": "debit",  "amount": "5000.00",   "desc": "Travel expense"},

    # Eve — balanced credits/debits, moderate activity
    {"user_id": "eve_00005", "idem": "seed-eve-1", "type": "credit", "amount": "20000.00", "desc": "Salary"},
    {"user_id": "eve_00005", "idem": "seed-eve-2", "type": "debit",  "amount": "8000.00",  "desc": "Rent"},
    {"user_id": "eve_00005", "idem": "seed-eve-3", "type": "credit", "amount": "3000.00",  "desc": "Side gig"},
    {"user_id": "eve_00005", "idem": "seed-eve-4", "type": "debit",  "amount": "4500.00",  "desc": "Shopping"},
    {"user_id": "eve_00005", "idem": "seed-eve-5", "type": "debit",  "amount": "2000.00",  "desc": "Utilities"},
]


def seed():
    print("🌱 Seeding database...")

    # Create users
    user_map = {}
    for u in SEED_USERS:
        user, created = User.objects.get_or_create(
            user_id=u["user_id"],
            defaults={"user_name": u["user_name"]},
        )
        user_map[u["user_id"]] = user
        status = "created" if created else "exists"
        print(f"  User {u['user_id']:12s}  [{status}]")

    # Create transactions and update aggregates
    for t in SEED_TRANSACTIONS:
        user = user_map[t["user_id"]]
        txn, created = Transaction.objects.get_or_create(
            user=user,
            idempotency_key=t["idem"],
            defaults={
                "transaction_type": t["type"],
                "amount": Decimal(t["amount"]),
                "descriptions": t["desc"],
            },
        )
        if created:
            # Update user aggregates
            amt = Decimal(t["amount"])
            if t["type"] == "credit":
                user.total_credits += amt
                user.net_balance += amt
            else:
                user.total_debits += amt
                user.net_balance -= amt
            user.transaction_count += 1
            print(f"  Txn {t['idem']:20s}  {t['type']:6s}  {t['amount']:>12s}  ✓")
        else:
            print(f"  Txn {t['idem']:20s}  {t['type']:6s}  {t['amount']:>12s}  (skip)")

    # Recompute rank scores
    print("\n📊 Computing rank scores...")
    for uid, user in user_map.items():
        user.rank_score = compute_rank_score(user)
        user.save()
        print(f"  {uid:12s}  score={user.rank_score:.6f}  balance={user.net_balance}")

    print("\n✅ Seed complete!")


seed()
