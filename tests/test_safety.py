import pytest

from ozon_frontend_sourcing_collector.safety import SafetyGate


def test_safety_gate_rejects_wrong_host():
    gate = SafetyGate()
    with pytest.raises(ValueError):
        gate.assert_allowed_url("ozon", "https://example.com/product/1")


def test_safety_gate_limits_requests_per_host():
    gate = SafetyGate(max_requests_per_host_per_run=1)
    gate.register_request("https://www.ozon.ru/search/?text=x")
    with pytest.raises(RuntimeError):
        gate.register_request("https://www.ozon.ru/product/1")


def test_safety_gate_detects_verification_text():
    gate = SafetyGate()
    reasons = gate.inspect_text("请完成安全验证 captcha")
    assert reasons