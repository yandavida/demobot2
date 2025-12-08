# saas/runtime.py
from __future__ import annotations

from functools import lru_cache

from .repositories import (
    create_demo_repositories,
    CustomerRepository,
    CustomerConfigRepository,
    ApiKeyRepository,
)
from .context import RequestContext, get_demo_context


@lru_cache(maxsize=1)
def get_repositories() -> (
    tuple[CustomerRepository, CustomerConfigRepository, ApiKeyRepository]
):
    """
    יוצר (פעם אחת) את ה-Repos לשכבת ה-SaaS ומחזיר אותם.
    ה-lru_cache דואג שזה יהיה Singleton בתוך הפרוסס.
    """
    return create_demo_repositories()


@lru_cache(maxsize=1)
def get_demo_request_context() -> RequestContext:
    """
    מחזיר RequestContext של לקוח דמו – לשימוש ב-UI המקומי.
    בעתיד אפשר להחליף לפונקציה שמזהה לקוח לפי Login / Token.
    """
    cust_repo, cfg_repo, key_repo = get_repositories()
    return get_demo_context(cust_repo, cfg_repo)
