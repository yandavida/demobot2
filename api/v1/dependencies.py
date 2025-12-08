# api/v1/dependencies.py
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from saas.repositories import (
    create_demo_repositories,
    CustomerRepository,
    CustomerConfigRepository,
    ApiKeyRepository,
)
from saas.context import (
    RequestContext,
    resolve_context_from_api_key,
    UnknownCustomerError,
    InactiveCustomerError,
)

# === יצירת Repos גלובליים (בשלב זה InMemory) ===
_customer_repo, _config_repo, _api_key_repo = create_demo_repositories()


def get_customer_repo() -> CustomerRepository:
    return _customer_repo


def get_config_repo() -> CustomerConfigRepository:
    return _config_repo


def get_api_key_repo() -> ApiKeyRepository:
    return _api_key_repo


# === API Key Dependency ===


def get_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """
    מושך את ה-API key מה-header: X-API-Key
    """
    return x_api_key


def get_request_context(
    api_key: str = Depends(get_api_key),
    customer_repo: CustomerRepository = Depends(get_customer_repo),
    config_repo: CustomerConfigRepository = Depends(get_config_repo),
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repo),
) -> RequestContext:
    """
    רזולבר מרמת request -> RequestContext (לקוח + קונפיגורציה).
    """
    try:
        ctx = resolve_context_from_api_key(
            api_key=api_key,
            customer_repo=customer_repo,
            config_repo=config_repo,
            key_repo=api_key_repo,
        )
        return ctx

    except UnknownCustomerError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    except InactiveCustomerError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
