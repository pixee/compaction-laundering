from src.checkout_service import Cart, LineItem, apply_discount


def test_cart_total():
    cart = Cart((LineItem("A", 2, 500), LineItem("B", 1, 1299)))
    assert cart.total_cents() == 2299


def test_apply_discount():
    assert apply_discount(2000, 10) == 1800
