import json
import pytest
from pathlib import Path

from core.numeric_policy import DEFAULT_TOLERANCES, MetricClass
from core.services.portfolio_valuation import PublicValuationRequest, PublicPosition, valuate_portfolio


MANIFEST = Path("tests/golden/pipeline/datasets_manifest.json")


pytestmark = pytest.mark.pipeline_golden


def nearly_equal(a: float, b: float, tol) -> bool:
    if tol.abs is not None and abs(a - b) <= tol.abs:
        return True
    if tol.rel is not None and abs(a - b) <= tol.rel * max(abs(a), abs(b), 1.0):
        return True
    return False


def test_pipeline_golden_manifest_driven():
    assert MANIFEST.exists(), f"manifest missing: {MANIFEST}"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for entry in manifest:
        dataset_id = entry["dataset_id"]
        input_path = Path(entry["input_file"])
        assert input_path.exists(), f"input missing: {input_path}"

        data = json.loads(input_path.read_text(encoding="utf-8"))

        # build PublicValuationRequest from P-INPUT v1 envelope
        positions = []
        for p in data["positions"]:
            symbol = p["instrument_id"]
            quantity = p["quantity"]
            # price taken from market.quotes
            quote = data["market"]["quotes"].get(symbol)
            assert quote is not None and "price" in quote, f"missing market quote for {symbol}"
            price = float(quote["price"])
            positions.append(PublicPosition(symbol=symbol, quantity=quantity, price=price))

        req = PublicValuationRequest(positions=positions, fx_rates=data.get("fx", {}).get("rates", {}), base_currency=data["base_currency"])

        # run deterministic entrypoint
        resp = valuate_portfolio(req)

        # canonicalize actual
        per_pos = sorted(
            [
                {"instrument_id": p["instrument_id"], "pv": float(p["quantity"]) * float(data["market"]["quotes"][p["instrument_id"]]["price"]), "currency": data["market"]["quotes"][p["instrument_id"]].get("currency", data["base_currency"]) }
                for p in data["positions"]
            ],
            key=lambda x: x["instrument_id"],
        )

        actual = {
            "dataset_id": dataset_id,
            "version": entry.get("version", 1),
            "base_currency": data["base_currency"],
            "per_position": per_pos,
            "total_pv": float(resp.total_value),
            "metadata": {"policy_ref": "Gate N DEFAULT_TOLERANCES"},
        }

        expected_path = Path(f"tests/golden/pipeline/expected/{dataset_id}/expected_v1.json")
        assert expected_path.exists(), f"expected file missing: {expected_path}"
        expected = json.loads(expected_path.read_text(encoding="utf-8"))

        # compare total_pv using PNL tolerance
        tol = DEFAULT_TOLERANCES[MetricClass.PNL]
        assert nearly_equal(actual["total_pv"], expected["total_pv"], tol), (
            f"total_pv mismatch for {dataset_id}: expected {expected['total_pv']}, actual {actual['total_pv']} (tol abs={tol.abs} rel={tol.rel})"
        )

        # compare per-position pv
        for a, e in zip(sorted(actual["per_position"], key=lambda x: x["instrument_id"]), sorted(expected["per_position"], key=lambda x: x["instrument_id"])):
            assert a["instrument_id"] == e["instrument_id"]
            assert nearly_equal(a["pv"], e["pv"], tol), (
                f"pv mismatch for {dataset_id} {a['instrument_id']}: expected {e['pv']}, actual {a['pv']} (tol abs={tol.abs} rel={tol.rel})"
            )
