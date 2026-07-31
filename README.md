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
| `GET` | `/storage/hdd` | NVR HDD hard-ийн мэдээлэл |
| `GET` | `/network/interfaces` | Network interface-ийн мэдээлэл |
| `PUT` | `/network/interfaces/{id}/ip-address` | Network тохиргоо шинэчлэх |
