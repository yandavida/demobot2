# saas/repositories.py
from __future__ import annotations

from typing import Dict, Optional, Iterable

from .models import Customer, CustomerConfig, ApiKey
from .models import PlanTier


class CustomerRepository:
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        raise NotImplementedError

    def list_active(self) -> Iterable[Customer]:
        raise NotImplementedError


class CustomerConfigRepository:
    def get_by_customer_id(self, customer_id: str) -> Optional[CustomerConfig]:
        raise NotImplementedError


class ApiKeyRepository:
    def get_by_key(self, key: str) -> Optional[ApiKey]:
        raise NotImplementedError


# המשך saas/repositories.py


class InMemoryCustomerRepository(CustomerRepository):
    def __init__(self, customers: dict[str, Customer]):
        self._customers: Dict[str, Customer] = customers

    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        return self._customers.get(customer_id)

    def list_active(self) -> Iterable[Customer]:
        return (c for c in self._customers.values() if c.is_active)


class InMemoryCustomerConfigRepository(CustomerConfigRepository):
    def __init__(self, configs: dict[str, CustomerConfig]):
        # key = customer_id
        self._configs: Dict[str, CustomerConfig] = configs

    def get_by_customer_id(self, customer_id: str) -> Optional[CustomerConfig]:
        return self._configs.get(customer_id)


class InMemoryApiKeyRepository(ApiKeyRepository):
    def __init__(self, keys: dict[str, ApiKey]):
        # key = api_key
        self._keys: Dict[str, ApiKey] = keys

    def get_by_key(self, key: str) -> Optional[ApiKey]:
        return self._keys.get(key)


# אופציונלי – בסוף saas/repositories.py


def create_demo_repositories():
    demo_customer = Customer(
        id="cust_demo_1",
        name="Demo Customer",
        plan=PlanTier.PRO,
        is_active=True,
    )

    demo_config = CustomerConfig(
        customer_id=demo_customer.id,
        display_name="Demo Customer",
        default_underlying="SPX",
        max_open_positions=100,
        feature_flags={"fx_engine": True},
        risk_profile="standard",
    )

    demo_api_key = ApiKey(
        key="DEMO_API_KEY_123",
        customer_id=demo_customer.id,
        is_active=True,
    )

    cust_repo = InMemoryCustomerRepository(customers={demo_customer.id: demo_customer})
    cfg_repo = InMemoryCustomerConfigRepository(configs={demo_customer.id: demo_config})
    key_repo = InMemoryApiKeyRepository(keys={demo_api_key.key: demo_api_key})

    return cust_repo, cfg_repo, key_repo
