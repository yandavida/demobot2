import inspect
import importlib


def test_canonical_imports_exist():
    # Contracts
    risk_types = importlib.import_module("core.contracts.risk_types")
    Greeks = getattr(risk_types, "Greeks")
    PortfolioRiskSnapshot = getattr(risk_types, "PortfolioRiskSnapshot")
    RiskScenarioResult = getattr(risk_types, "RiskScenarioResult")
    # Semantics
    semantics = importlib.import_module("core.risk.semantics")
    RiskContext = getattr(semantics, "RiskContext")
    # VaR
    var_types = importlib.import_module("core.risk.var_types")
    VarResult = getattr(var_types, "VarResult")
    # Unified report
    unified_types = importlib.import_module("core.risk.unified_report_types")
    UnifiedPortfolioRiskReport = getattr(unified_types, "UnifiedPortfolioRiskReport")
    # Assert all exist
    assert Greeks and PortfolioRiskSnapshot and RiskScenarioResult
    assert RiskContext
    assert VarResult
    assert UnifiedPortfolioRiskReport

def test_no_duplicate_contracts():
    # Symbol: (import path, canonical file ending)
    symbols = [
        ("Greeks", "core/contracts/risk_types.py"),
        ("PortfolioRiskSnapshot", "core/contracts/risk_types.py"),
        ("RiskScenarioResult", "core/contracts/risk_types.py"),
        ("RiskContext", "core/risk/semantics.py"),
        ("VarResult", "core/risk/var_types.py"),
        ("UnifiedPortfolioRiskReport", "core/risk/unified_report_types.py"),
    ]
    modules = {
        "Greeks": importlib.import_module("core.contracts.risk_types"),
        "PortfolioRiskSnapshot": importlib.import_module("core.contracts.risk_types"),
        "RiskScenarioResult": importlib.import_module("core.contracts.risk_types"),
        "RiskContext": importlib.import_module("core.risk.semantics"),
        "VarResult": importlib.import_module("core.risk.var_types"),
        "UnifiedPortfolioRiskReport": importlib.import_module("core.risk.unified_report_types"),
    }
    for symbol, canonical_path in symbols:
        obj = getattr(modules[symbol], symbol)
        src = inspect.getsourcefile(obj)
        assert src is not None and src.replace("\\", "/").endswith(canonical_path), f"{symbol} not from {canonical_path}: {src}"
