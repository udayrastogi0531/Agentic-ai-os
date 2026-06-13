"""
Nidhi — Memory Decay Scoring

Implements exponential decay math to rank memory items dynamically based on age and access history.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone


def calculate_recall_score(
    importance: float,
    last_accessed: datetime,
    decay_constant: float = 0.005,  # decay rate per hour
) -> float:
    """
    Calculate the recall score using the exponential decay formula:
    S = I * e^(-lambda * t)

    Where:
      - I: base importance score
      - lambda: decay constant (decay_constant)
      - t: hours elapsed since last accessed
    """
    now = datetime.now(timezone.utc)
    
    # Ensure timezone aware
    if last_accessed.tzinfo is None:
        last_accessed = last_accessed.replace(tzinfo=timezone.utc)
        
    delta = now - last_accessed
    hours_elapsed = max(0.0, delta.total_seconds() / 3600.0)

    # Math exponential decay
    retention = math.exp(-decay_constant * hours_elapsed)
    score = float(importance * retention)

    return score
