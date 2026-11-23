# Kalkulator Subnet & VLSM

Aplikasi web (FastAPI + satu halaman HTML) untuk menghitung subnet IPv4 dan alokasi VLSM.

## Menjalankan
```
uv sync --dev
uv run fastapi dev main.py     # buka http://127.0.0.1:8000
uv run pytest -v
```

## API
- `GET /api/subnet?ip=172.16.5.130&prefix=25`
- `POST /api/vlsm` body `{"network":"192.168.1.0/24","kebutuhan_host":[100,50,20,2]}`
- Input salah -> HTTP 400 dengan field `detail`.

Aturan: /31 mengikuti RFC 3021 (2 host, broadcast `null`); /32 = 1 host, broadcast `null`.
