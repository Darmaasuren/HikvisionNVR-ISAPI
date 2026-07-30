# Hikvision NVR ISAPI Gateway

Hikvision NVR-ийн ISAPI XML интерфейсийг JSON REST API хэлбэрээр ашиглах
FastAPI gateway төсөл.

Энэ төсөл нь:

- NVR төхөөрөмжийг шалгаж, тохиргоог SQLite database-д хадгална.
- Камер болон streaming channel-ийн жагсаалт авна.
- Live RTSP URL үүсгэнэ.
- Playback бичлэг хайж, татна.
- HDD hard болон network interface-ийн мэдээлэл авна.
- NVR-ийн network тохиргоог шинэчилнэ.

## Ажиллагааны ерөнхий урсгал

```text
Client / Postman
       ↓ JSON + API-Key
FastAPI Gateway
       ↓ XML + HTTP Digest Authentication
Hikvision NVR ISAPI
```

NVR-ийн IP, username болон password-ийг анхны setup хүсэлтээр авна. Өгсөн
credential-ээр NVR-тэй амжилттай холбогдсоны дараа SQLite database-д хадгалж,
дараагийн хүсэлтүүдэд database-аас ашиглана.

Одоогоор зөвхөн нэг active NVR хадгална.

## Төслийн бүтэц

```text
.
├── src/
│   ├── app/
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   ├── exception_handlers.py
│   │   ├── security.py
│   │   ├── routers/
│   │   └── schemas/
│   └── gateway/
│       ├── client.py
│       ├── config.py
│       ├── database.py
│       ├── http.py
│       ├── xml_utils.py
│       └── services/
├── postman/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

- `src/app` — FastAPI route, request validation, authentication.
- `src/gateway` — Hikvision HTTP client, XML parser болон бизнес service-үүд.
- `data` — local ажиллуулах үед SQLite database үүсэх хавтас.
- `postman` — API турших Postman collection.

## Шаардлага

Docker ашиглах бол:

- Docker
- Docker Compose
- Gateway ажиллаж буй төхөөрөмжөөс NVR-ийн IP болон HTTP портод хүрдэг байх

Local ажиллуулах бол:

- Python 3.12 буюу түүнээс дээш
- Python virtual environment

## Docker ашиглан ажиллуулах

### 1. API key үүсгэх

```bash
openssl rand -hex 32
```

Үүссэн утгыг `docker-compose.yml` дотор оруулна:

```yaml
environment:
  API_KEY: "энд-шинэ-api-key-оруулна"
```

API key-г Git repository, screenshot болон log-д задруулахгүй.

### 2. Container build хийж асаах

```bash
docker compose up --build -d
```

Container-ийн төлөв шалгах:

```bash
docker compose ps
```

Log харах:

```bash
docker compose logs -f hikvision-nvr
```

Gateway дараах хаяг дээр ажиллана:

```text
http://localhost:8001
```

Swagger UI:

```text
http://localhost:8001/docs
```

### 3. Health шалгах

`/health` endpoint API key шаардахгүй:

```bash
curl http://localhost:8001/health
```

Хариу:

```json
{
  "ok": true,
  "service": "hikvision-gateway"
}
```

## API authentication

`/health`-ээс бусад endpoint дараах header-ийг шаардана:

```http
API-Key: таны-api-key
```

Жишээ:

```bash
curl \
  -H "API-Key: таны-api-key" \
  http://localhost:8001/nvr/status
```

Authentication алдаа:

| HTTP status | Утга |
|---|---|
| `401` | `API-Key` header байхгүй |
| `403` | API key буруу |
| `503` | Container дээр `API_KEY` тохируулаагүй |

Swagger UI-ийн `Authorize` товч дээр API key-г оруулж endpoint-уудаа туршиж
болно.

## NVR анх бүртгэх

Database-д NVR бүртгэлгүй үед:

```bash
curl \
  -H "API-Key: таны-api-key" \
  http://localhost:8001/nvr/status
```

Хариу:

```json
{
  "ok": true,
  "data": {
    "configured": false,
    "source": "database",
    "setup_required": true
  }
}
```

NVR бүртгэх:

```bash
curl -X POST \
  -H "API-Key: таны-api-key" \
  -H "Content-Type: application/json" \
  http://localhost:8001/nvr/setup \
  -d '{
    "ip_address": "192.168.1.125",
    "username": "admin",
    "password": "nvr-password",
    "http_port": 80,
    "rtsp_port": 554
  }'
```

Gateway эхлээд `/ISAPI/System/deviceInfo` endpoint-оор NVR credential-ийг
шалгана. Холболт амжилттай болсон тохиолдолд л config-ийг database-д хадгална.

NVR setup-д зөвхөн private network-ийн IP address зөвшөөрнө. Public, loopback,
link-local, multicast болон reserved IP address-уудыг хориглоно.

## Үндсэн endpoint-ууд

| Method | Endpoint | Тайлбар |
|---|---|---|
| `GET` | `/health` | Gateway ажиллаж байгаа эсэх |
| `GET` | `/nvr/status` | NVR бүртгэл болон холболтын төлөв |
| `POST` | `/nvr/setup` | Active NVR анх бүртгэх |
| `GET` | `/nvr/config` | Хадгалсан NVR config авах |
| `PUT` | `/nvr/config/update` | Active NVR config шинэчлэх |
| `GET` | `/nvr/info` | NVR төхөөрөмжийн мэдээлэл |
| `GET` | `/cameras` | Камерын жагсаалт |
| `GET` | `/streaming/channels` | Streaming channel-ийн мэдээлэл |
| `GET` | `/streams` | Live RTSP URL үүсгэх |
| `GET` | `/playback/search` | Playback бичлэг хайх |
| `POST` | `/playback/download` | Playback бичлэг татах |
| `GET` | `/storage/hdd` | NVR HDD-ийн мэдээлэл |
| `GET` | `/network/interfaces` | Network interface-ийн мэдээлэл |
| `PUT` | `/network/interfaces/{id}/ip-address` | Network тохиргоо шинэчлэх |

## Камерын жагсаалт авах

```bash
curl \
  -H "API-Key: таны-api-key" \
  http://localhost:8001/cameras
```

## Live stream URL авах

```bash
curl \
  -H "API-Key: таны-api-key" \
  "http://localhost:8001/streams?camera_id=1&stream_type=main"
```

`stream_type` нь:

- `main` — үндсэн stream
- `sub` — дэд stream

## Playback хайх

```bash
curl \
  -H "API-Key: таны-api-key" \
  "http://localhost:8001/playback/search?camera_id=1&start_time=2026-07-30T00:00:00%2B00:00&end_time=2026-07-30T01:00:00%2B00:00&stream_type=main"
```

## Network тохиргоо

Static IP тохируулах:

```bash
curl -X PUT \
  -H "API-Key: таны-api-key" \
  -H "Content-Type: application/json" \
  http://localhost:8001/network/interfaces/1/ip-address \
  -d '{
    "ip_address": "192.168.1.124",
    "subnet_mask": "255.255.255.0",
    "default_gateway": "192.168.1.1",
    "primary_dns": "8.8.8.8",
    "secondary_dns": "",
    "addressing_type": "static",
    "ip_version": "v4"
  }'
```

DHCP тохируулах:

```bash
curl -X PUT \
  -H "API-Key: таны-api-key" \
  -H "Content-Type: application/json" \
  http://localhost:8001/network/interfaces/1/ip-address \
  -d '{
    "addressing_type": "dynamic",
    "ip_version": "v4"
  }'
```

> NVR-ийг DHCP горимд оруулсны дараа IP address өөрчлөгдөж болно. Gateway-ийн
> database-д өмнөх IP үлдэх тул DHCP reservation ашиглах эсвэл NVR-ийг шинэ
> IP-аар дахин бүртгэх шаардлагатай.

## Database

Container доторх SQLite database:

```text
/app/data/hikvision_gateway.sqlite3
```

`docker-compose.yml` named volume ашиглана:

```yaml
volumes:
  - hikvision-data:/app/data
```

Container устаж дахин үүссэн ч database хадгалагдана.

Container болон network-ийг зогсоох:

```bash
docker compose down
```

Database volume-тэй нь хамт устгах:

```bash
docker compose down -v
```

> `docker compose down -v` нь хадгалсан NVR config-ийг бүрэн устгана.

## Local development

Virtual environment үүсгэх:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

API key тохируулж server асаах:

```bash
API_KEY="local-development-api-key" \
PYTHONPATH=src \
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Local URL:

```text
http://localhost:8000
```

Local ажиллуулах үед SQLite database project root-ийн дараах замд үүснэ:

```text
data/hikvision_gateway.sqlite3
```

Командыг project root directory-оос ажиллуулна.

## Postman

Collection:

```text
postman/Hikvision_Gateway.postman_collection.json
```

Postman variables:

- `baseUrl` — Docker ашиглаж байгаа бол `http://localhost:8001`
- `apiKey` — Compose-ийн `API_KEY` утга
- `nvrIp`
- `nvrUsername`
- `nvrPassword`

Collection authentication:

```text
Type: API Key
Key: API-Key
Value: {{apiKey}}
Add to: Header
```

`Health Check` request дээр `No Auth` ашиглана.

## Security анхааруулга

- API key болон NVR password-ийг Git-д commit хийхгүй.
- Production орчинд HTTPS reverse proxy ашиглана.
- NVR password одоогоор SQLite database-д plaintext хадгалагддаг.
- `include_password=true` ашиглавал RTSP URL дотор NVR password гарна.
- `/network` endpoint NVR-ийн холболтыг таслах боломжтой тул болгоомжтой ашиглана.
- Gateway-г public internet рүү шууд нээхгүй.
