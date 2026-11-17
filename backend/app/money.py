def format_eur(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    euros, rest = divmod(abs(cents), 100)
    whole = f"{euros:,}".replace(",", ".")
    return f"{sign}{whole},{rest:02d} €"
