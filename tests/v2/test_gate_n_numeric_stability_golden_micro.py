import importlib
import math

import pytest

np = importlib.import_module("core.numeric_policy")
bs = importlib.import_module("core.pricing.bs")
units = importlib.import_module("core.pricing.units")


def assert_close(metric_class, actual, expected):
    t = np.DEFAULT_TOLERANCES.get(metric_class)
    assert t is not None, f"No tolerance for {metric_class}"
    if t.abs is None and t.rel is None:
        pytest.fail("Tolerance for {} is not set".format(metric_class))
    assert math.isclose(actual, expected, abs_tol=t.abs or 0.0, rel_tol=t.rel or 0.0)


def run_case(opt_type, spot, strike, t, rate, div, vol):
    price = bs.bs_price('call' if opt_type == 'C' else 'put', spot, strike, rate, div, vol, t)
    raw = bs.bs_greeks(opt_type, spot, strike, rate, div, vol, t)
    canon = units.to_canonical_greeks(raw)
    return price, canon


def test_golden_cases():
    # Case 1: ATM call
    price, canon = run_case('C', 100.0, 100.0, 1.0, 0.0, 0.0, 0.20)
    assert_close(np.MetricClass.PRICE, price, 7.965567455405804)
    assert_close(np.MetricClass.DELTA, canon['delta'], 0.539827837277029)
    assert_close(np.MetricClass.GAMMA, canon['gamma'], 0.01984762737385059)
    assert_close(np.MetricClass.VEGA, canon['vega'], 0.39695254747701175)
    assert_close(np.MetricClass.THETA, canon['theta'], -0.010875412259644158)

    # Case 2: ATM put
    price, canon = run_case('P', 100.0, 100.0, 1.0, 0.0, 0.0, 0.20)
    assert_close(np.MetricClass.PRICE, price, 7.965567455405804)
    assert_close(np.MetricClass.DELTA, canon['delta'], -0.460172162722971)
    assert_close(np.MetricClass.GAMMA, canon['gamma'], 0.01984762737385059)
    assert_close(np.MetricClass.VEGA, canon['vega'], 0.39695254747701175)
    assert_close(np.MetricClass.THETA, canon['theta'], -0.010875412259644158)

    # Case 3: Deep ITM call
    price, canon = run_case('C', 200.0, 100.0, 1.0, 0.0, 0.0, 0.20)
    assert_close(np.MetricClass.PRICE, price, 100.00188621817614)
    assert_close(np.MetricClass.DELTA, canon['delta'], 0.9998185816915897)
    assert_close(np.MetricClass.GAMMA, canon['gamma'], 1.7295672165924913e-05)
    assert_close(np.MetricClass.VEGA, canon['vega'], 0.001383653773273993)
    assert_close(np.MetricClass.THETA, canon['theta'], -3.790832255545186e-05)

    # Case 4: Deep OTM call
    price, canon = run_case('C', 50.0, 100.0, 1.0, 0.0, 0.0, 0.20)
    assert_close(np.MetricClass.PRICE, price, 0.0009431090880723803)
    assert_close(np.MetricClass.DELTA, canon['delta'], 0.0003816987985820197)
    assert_close(np.MetricClass.GAMMA, canon['gamma'], 0.0001383653773273993)
    assert_close(np.MetricClass.VEGA, canon['vega'], 0.0006918268866369964)
    assert_close(np.MetricClass.THETA, canon['theta'], -1.895416127772593e-05)

    # Case 5: Near-expiry
    price, canon = run_case('C', 100.0, 100.0, 1e-4, 0.0, 0.0, 0.20)
    assert_close(np.MetricClass.PRICE, price, 0.07978844278220976)
    assert_close(np.MetricClass.DELTA, canon['delta'], 0.500398942213911)
    assert_close(np.MetricClass.GAMMA, canon['gamma'], 1.994710404651712)
    assert_close(np.MetricClass.VEGA, canon['vega'], 0.003989420809303424)
    assert_close(np.MetricClass.THETA, canon['theta'], -1.0929920025488833)

    # Case 6: Low vol
    price, canon = run_case('C', 100.0, 100.0, 1.0, 0.0, 0.0, 1e-6)
    assert_close(np.MetricClass.PRICE, price, 3.9894228038406254e-05)
    assert_close(np.MetricClass.DELTA, canon['delta'], 0.5000001994711402)
    assert_close(np.MetricClass.GAMMA, canon['gamma'], 3989.4228040138287)
    assert_close(np.MetricClass.VEGA, canon['vega'], 0.39894228040138285)
    assert_close(np.MetricClass.THETA, canon['theta'], -5.464962745224423e-08)
