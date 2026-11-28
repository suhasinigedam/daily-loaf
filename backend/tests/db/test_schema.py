from datetime import date

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.enums import OrderSource, OrderStatus
from app.models import Customer, Order, OrderItem, Product, ProductRate

AUDIT = {"created_by": "test", "updated_by": "test"}


def make_product(session: Session) -> Product:
    product = Product(code="TEST", name="Test", sort_order=99, **AUDIT)
    session.add(product)
    session.flush()
    return product


def test_migration_creates_all_tables(engine: Engine) -> None:
    names = set(inspect(engine).get_table_names())
    assert {
        "customers", "products", "product_rates", "orders", "order_items",
        "payments", "adjustments", "monthly_statements", "billing_months",
    } <= names


def test_models_match_migrations(alembic_config: Config) -> None:
    # Fails if a model changed but no migration was written for it.
    command.check(alembic_config)


def test_rate_unique_per_product_and_date(session: Session) -> None:
    product = make_product(session)
    session.add_all(
        [
            ProductRate(product_id=product.id, price_cents=55, effective_from=date(2026, 1, 1), **AUDIT),
            ProductRate(product_id=product.id, price_cents=60, effective_from=date(2026, 1, 1), **AUDIT),
        ]
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_order_item_quantity_must_be_positive(session: Session) -> None:
    customer = Customer(name="Asha", **AUDIT)
    product = make_product(session)
    session.add(customer)
    session.flush()
    order = Order(
        customer_id=customer.id,
        delivery_date=date(2026, 11, 5),
        source=OrderSource.WHATSAPP,
        items=[OrderItem(product_id=product.id, quantity=0, unit_price_cents=40, **AUDIT)],
        **AUDIT,
    )
    session.add(order)
    with pytest.raises(IntegrityError):
        session.flush()


def test_new_order_is_pending(session: Session) -> None:
    customer = Customer(name="Asha", **AUDIT)
    session.add(customer)
    session.flush()
    order = Order(customer_id=customer.id, delivery_date=date(2026, 11, 5),
                  source=OrderSource.PHONE, **AUDIT)
    session.add(order)
    session.flush()
    assert order.status == OrderStatus.PENDING