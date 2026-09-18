from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_convert_binary_to_hex():
    resp = client.post("/api/convert", json={"value": "1010", "from_base": 2, "to_base": 16})
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "A"
    assert data["decimal_value"] == 10
    assert data["steps"]


def test_convert_decimal_to_binary():
    resp = client.post("/api/convert", json={"value": "255", "from_base": 10, "to_base": 2})
    assert resp.status_code == 200
    assert resp.json()["result"] == "11111111"


def test_convert_negative_number():
    resp = client.post("/api/convert", json={"value": "-255", "from_base": 10, "to_base": 16})
    assert resp.status_code == 200
    assert resp.json()["result"] == "-FF"


def test_convert_hex_negative_to_decimal():
    resp = client.post("/api/convert", json={"value": "-FF", "from_base": 16, "to_base": 10})
    assert resp.status_code == 200
    assert resp.json()["result"] == "-255"
    assert resp.json()["decimal_value"] == -255


def test_convert_lowercase_hex():
    resp = client.post("/api/convert", json={"value": "ff", "from_base": 16, "to_base": 10})
    assert resp.status_code == 200
    assert resp.json()["result"] == "255"


def test_convert_invalid_digit_400():
    resp = client.post("/api/convert", json={"value": "102", "from_base": 2, "to_base": 10})
    assert resp.status_code == 400
    assert "недопустим" in resp.json()["detail"]


def test_convert_empty_value_422():
    resp = client.post("/api/convert", json={"value": "", "from_base": 2, "to_base": 10})
    assert resp.status_code == 422


def test_calculate_add_hex():
    resp = client.post(
        "/api/calculate",
        json={"value1": "FF", "value2": "1", "base": 16, "operation": "add"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"] == "100"
    assert data["result_decimal"] == 256
    assert data["steps"]


def test_calculate_subtract_binary():
    resp = client.post(
        "/api/calculate",
        json={"value1": "1000", "value2": "1", "base": 2, "operation": "subtract"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == "111"


def test_calculate_negative_result():
    resp = client.post(
        "/api/calculate",
        json={"value1": "1", "value2": "10", "base": 10, "operation": "subtract"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == "-9"


def test_calculate_multiply():
    resp = client.post(
        "/api/calculate",
        json={"value1": "F", "value2": "F", "base": 16, "operation": "multiply"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == "E1"


def test_calculate_unknown_operation_400():
    resp = client.post(
        "/api/calculate",
        json={"value1": "1", "value2": "2", "base": 10, "operation": "divide"},
    )
    assert resp.status_code == 400


def test_calculate_invalid_digit_400():
    resp = client.post(
        "/api/calculate",
        json={"value1": "2", "value2": "1", "base": 2, "operation": "add"},
    )
    assert resp.status_code == 400


def test_validate_valid():
    resp = client.post("/api/validate", json={"value": "1A", "base": 16})
    assert resp.status_code == 200
    assert resp.json()["valid"] is True


def test_validate_invalid():
    resp = client.post("/api/validate", json={"value": "2", "base": 2})
    assert resp.status_code == 200
    assert resp.json()["valid"] is False


def test_bases_endpoint():
    resp = client.get("/api/bases")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 35
    assert data[0]["base"] == 2
    assert data[-1]["base"] == 36
    assert data[14]["base"] == 16
    assert "ABCDEF" in data[14]["digits"]


def test_operations_endpoint():
    resp = client.get("/api/operations")
    assert resp.status_code == 200
    ops = resp.json()["operations"]
    assert any(op["id"] == "add" for op in ops)


def test_root_returns_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_app_serves_frontend():
    resp = client.get("/app/")
    assert resp.status_code == 200
    assert "Конвертер систем счисления" in resp.text


def test_manifest_served():
    resp = client.get("/app/manifest.json")
    assert resp.status_code == 200
    assert resp.json()["short_name"] == "Системы"