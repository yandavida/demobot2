from __future__ import annotations


def test_smoke_imports() -> None:
    """
    Smoke test – ensures the core package can be imported.
    Exists so pytest in CI will collect at least one test.
    """
    import core  # noqa: F401
    assert True
