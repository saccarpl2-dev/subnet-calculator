"""Kalkulator Subnet & VLSM (IPv4). Perhitungan memakai operasi bitwise."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Kalkulator Subnet & VLSM")


def _ip_ke_int(ip: str) -> int:
    if not isinstance(ip, str):
        raise ValueError("IP harus berupa teks")
    bagian = ip.split(".")
    if len(bagian) != 4:
        raise ValueError("IP harus terdiri dari tepat 4 oktet")
    nilai = 0
    for b in bagian:
        if not (b.isascii() and b.isdigit()):
            raise ValueError(f"Oktet '{b}' bukan angka desimal")
        if len(b) > 1 and b[0] == "0":
            raise ValueError(f"Oktet '{b}' tidak boleh diawali angka nol")
        if int(b) > 255:
            raise ValueError(f"Oktet '{b}' di luar rentang 0-255")
        nilai = (nilai << 8) | int(b)
    return nilai


def _int_ke_ip(n: int) -> str:
    return ".".join(str((n >> s) & 255) for s in (24, 16, 8, 0))


def _cek_prefix(prefix) -> int:
    if isinstance(prefix, bool) or not isinstance(prefix, int):
        raise ValueError("Prefix harus bilangan bulat")
    if not 0 <= prefix <= 32:
        raise ValueError("Prefix harus antara 0 dan 32")
    return prefix


def hitung_subnet(ip: str, prefix: int) -> dict:
    prefix = _cek_prefix(prefix)
    alamat = _ip_ke_int(ip)
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    network = alamat & mask  # AND dengan subnet mask
    bcast = network | (~mask & 0xFFFFFFFF)
    if prefix == 32:
        first = last = alamat
        bcast_s, host = None, 1
    elif prefix == 31:  # RFC 3021
        first, last, bcast_s, host = network, bcast, None, 2
    else:
        first, last, bcast_s = network + 1, bcast - 1, _int_ke_ip(bcast)
        host = 2 ** (32 - prefix) - 2
    return {
        "mask": _int_ke_ip(mask),
        "network": _int_ke_ip(network),
        "broadcast": bcast_s,
        "first_host": _int_ke_ip(first),
        "last_host": _int_ke_ip(last),
        "usable_hosts": host,
    }


def alokasi_vlsm(network_cidr: str, kebutuhan_host: list[int]) -> list[dict]:
    if not isinstance(network_cidr, str) or network_cidr.count("/") != 1:
        raise ValueError("Network harus berformat CIDR, contoh 192.168.1.0/24")
    ip_s, pre_s = network_cidr.split("/")
    if not (pre_s.isascii() and pre_s.isdigit()):
        raise ValueError("Prefix harus bilangan bulat")
    prefix = _cek_prefix(int(pre_s))
    awal = _ip_ke_int(ip_s)
    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    if awal & mask != awal:
        raise ValueError("Bukan alamat jaringan yang valid untuk prefix tersebut")
    if not kebutuhan_host:
        raise ValueError("Daftar kebutuhan host tidak boleh kosong")
    if any(isinstance(k, bool) or not isinstance(k, int) or k < 1 for k in kebutuhan_host):
        raise ValueError("Setiap kebutuhan host harus bilangan bulat >= 1")

    akhir = awal + 2 ** (32 - prefix)
    sekarang, hasil = awal, []
    for k in sorted(kebutuhan_host, reverse=True):
        bit = 2
        while 2**bit < k + 2:
            bit += 1
        ukuran, p = 2**bit, 32 - bit
        if p < prefix or sekarang + ukuran > akhir:
            raise ValueError("Blok jaringan tidak cukup untuk seluruh kebutuhan")
        info = hitung_subnet(_int_ke_ip(sekarang), p)
        hasil.append({"kebutuhan": k, "network_cidr": f"{info['network']}/{p}", **info})
        sekarang += ukuran
    return hasil


class VlsmIn(BaseModel):
    network: str
    kebutuhan_host: list[int]


@app.get("/api/subnet")
def api_subnet(ip: str = "", prefix: str = ""):
    try:
        if not (prefix.isascii() and prefix.lstrip("-").isdigit()):
            raise ValueError("Prefix harus bilangan bulat")
        return hitung_subnet(ip, int(prefix))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/vlsm")
def api_vlsm(data: VlsmIn):
    try:
        return alokasi_vlsm(data.network, data.kebutuhan_host)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/", response_class=HTMLResponse)
def index():
    return (Path(__file__).parent / "index.html").read_text(encoding="utf-8")
