"""
Ranking — weighted composite score from balance, activity, and credit ratio.
Caps and log scaling are intentional to limit gaming.
"""

import math
from decimal import Decimal

BALANCE_CAP = Decimal("1000000.00")
ACTIVITY_MAX = 1001  # ~1000 txns to hit max score
WEIGHTS = {
    "balance": 0.5,
    "activity": 0.3,
    "credit_ratio": 0.2,
}


def _compute_components(user) -> tuple[float, float, float]:
    net_balance = user.net_balance
    credits = user.total_credits
    debits = user.total_debits
    count = user.transaction_count

    # cap balance so whales can't dominate
    capped = min(net_balance, BALANCE_CAP)
    s_balance = float(capped / BALANCE_CAP) if BALANCE_CAP else 0.0

    # log scale so spamming txns gives diminishing returns
    s_activity = (
        math.log10(1 + count) / math.log10(ACTIVITY_MAX) if count > 0 else 0.0
    )
    s_activity = min(s_activity, 1.0)

    total_volume = credits + debits
    s_ratio = float(credits / total_volume) if total_volume > 0 else 0.0

    return s_balance, s_activity, s_ratio


def compute_rank_score(user) -> float:
    s_balance, s_activity, s_ratio = _compute_components(user)

    rank_score = (
        s_balance * WEIGHTS["balance"]
        + s_activity * WEIGHTS["activity"]
        + s_ratio * WEIGHTS["credit_ratio"]
    )
    return round(rank_score, 6)


def compute_score_breakdown(user) -> dict:
    s_balance, s_activity, s_ratio = _compute_components(user)

    return {
        "balance_component": round(s_balance * WEIGHTS["balance"], 6),
        "activity_component": round(s_activity * WEIGHTS["activity"], 6),
        "credit_ratio_component": round(s_ratio * WEIGHTS["credit_ratio"], 6),
    }