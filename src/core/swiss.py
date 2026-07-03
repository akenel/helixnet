import decimal

def swiss_chf(amount: float) -> str:
    """Format amount as Swiss francs with apostrophe thousands separator and two decimals."""
    d = decimal.Decimal(str(amount)).quantize(decimal.Decimal('0.00'), rounding=decimal.ROUND_HALF_UP)
    formatted = f"{d:,.2f}".replace(',', "'")
    return f"CHF {formatted}"
