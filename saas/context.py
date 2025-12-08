# saas/context.py
from __future__ import annotations

from dataclasses import dataclass

from .models import Customer, CustomerConfig
from .repositories import (
    CustomerRepository,
    CustomerConfigRepository,
    ApiKeyRepository,
)


@dataclass
class RequestContext:
    customer: Customer
    config: CustomerConfig


class UnknownCustomerError(Exception):
    pass


class InactiveCustomerError(Exception):
    pass


def resolve_context_from_api_key(
    api_key: str,
    customer_repo: CustomerRepository,
    config_repo: CustomerConfigRepository,
    key_repo: ApiKeyRepository,
) -> RequestContext:
    """לשימוש ב-API: משייך api_key ללקוח ולקונפיגורציה שלו."""
    api_key_obj = key_repo.get_by_key(api_key)
    if api_key_obj is None or not api_key_obj.is_active:
        raise UnknownCustomerError("Invalid or inactive API key")

    customer = customer_repo.get_by_id(api_key_obj.customer_id)
    if customer is None:
        raise UnknownCustomerError("Customer not found")

    if not customer.is_active:
        raise InactiveCustomerError("Customer is inactive")

    config = config_repo.get_by_customer_id(customer.id)
    if config is None:
        # אפשר להחליט אם לזרוק שגיאה או ליצור קונפיגורציה ברירת־מחדל
        raise UnknownCustomerError("Customer config not found")

    return RequestContext(customer=customer, config=config)


def get_demo_context(
    customer_repo: CustomerRepository,
    config_repo: CustomerConfigRepository,
) -> RequestContext:
    """לשימוש מקומי / UI – מחזיר context של לקוח דמו."""
    # נניח שהדמו הוא הלקוח הראשון האקטיבי
    for customer in customer_repo.list_active():
        config = config_repo.get_by_customer_id(customer.id)
        if config:
            return RequestContext(customer=customer, config=config)
    raise UnknownCustomerError("No active demo customer found")
