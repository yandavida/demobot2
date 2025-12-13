from fastapi import APIRouter
import pytest

from api.v1.arbitrage_orch import check_route_collisions


def test_check_route_collisions_detects_duplicates():
    router = APIRouter()

    @router.get("/duplicate")
    def first():
        return {"message": "first"}

    @router.get("/duplicate")
    def second():
        return {"message": "second"}

    with pytest.raises(ValueError):
        check_route_collisions(router)
