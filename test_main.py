import pytest
from fastapi.testclient import TestClient

from main import alokasi_vlsm, app, hitung_subnet

client = TestClient(app)


@pytest.mark.parametrize("ip,prefix,network,bcast,first,last,host", [
    ("172.16.5.130", 25, "172.16.5.128", "172.16.5.255", "172.16.5.129", "172.16.5.254", 126),
    ("10.0.0.0", 30, "10.0.0.0", "10.0.0.3", "10.0.0.1", "10.0.0.2", 2),
    ("192.168.1.0", 31, "192.168.1.0", None, "192.168.1.0", "192.168.1.1", 2),
    ("192.168.1.5", 32, "192.168.1.5", None, "192.168.1.5", "192.168.1.5", 1),
    ("1.2.3.4", 0, "0.0.0.0", "255.255.255.255", "0.0.0.1", "255.255.255.254", 2**32 - 2),
])
def test_subnet_valid(ip, prefix, network, bcast, first, last, host):
    r = hitung_subnet(ip, prefix)
    assert (r["network"], r["broadcast"], r["first_host"], r["last_host"], r["usable_hosts"]) == (
        network, bcast, first, last, host)


@pytest.mark.parametrize("ip,prefix", [
    ("256.1.1.1", 24), ("192.168.01.1", 24), ("192.168.1", 24), ("abc", 24),
    ("", 24), ("1.1.1.1", 33), ("1.1.1.1", -1), (" 1.1.1.1", 24),
])
def test_subnet_invalid(ip, prefix):
    with pytest.raises(ValueError):
        hitung_subnet(ip, prefix)


def test_vlsm_ok():
    r = alokasi_vlsm("192.168.1.0/24", [20, 100, 2, 50])
    assert [b["network_cidr"] for b in r] == [
        "192.168.1.0/25", "192.168.1.128/26", "192.168.1.192/27", "192.168.1.224/30"]


@pytest.mark.parametrize("net,keb", [
    ("192.168.1.0/24", [200, 100]), ("192.168.1.5/24", [10]),
    ("192.168.1.0/24", []), ("192.168.1.0/24", [0]),
])
def test_vlsm_invalid(net, keb):
    with pytest.raises(ValueError):
        alokasi_vlsm(net, keb)


def test_api():
    assert client.get("/api/subnet?ip=172.16.5.130&prefix=25").json()["network"] == "172.16.5.128"
    assert client.get("/api/subnet?ip=256.1.1.1&prefix=24").status_code == 400
    assert "detail" in client.get("/api/subnet?ip=1.1.1.1&prefix=abc").json()
    ok = client.post("/api/vlsm", json={"network": "192.168.1.0/24", "kebutuhan_host": [100, 50]})
    assert ok.status_code == 200
    bad = client.post("/api/vlsm", json={"network": "192.168.1.0/24", "kebutuhan_host": [200, 100]})
    assert bad.status_code == 400
    assert client.get("/").status_code == 200
