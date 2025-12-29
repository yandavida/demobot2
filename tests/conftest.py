

import pytest
from api.v2.service import reset_for_tests


@pytest.fixture(autouse=True)
def _v2_isolation():
    reset_for_tests()
    yield
    reset_for_tests()
