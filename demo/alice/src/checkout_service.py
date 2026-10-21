"""Checkout + payment reconciliation (trimmed for the demo repo)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LineItem:
    sku: str
    qty: int
    unit_cents: int

    @property
    def subtotal_cents(self) -> int:
        return self.qty * self.unit_cents


@dataclass(frozen=True)
class Cart:
    items: tuple[LineItem, ...]

    def total_cents(self) -> int:
        return sum(i.subtotal_cents for i in self.items)


def apply_discount(total_cents: int, pct: int) -> int:
    if not 0 <= pct <= 100:
        raise ValueError(f"discount pct out of range: {pct}")
    return total_cents - (total_cents * pct) // 100
