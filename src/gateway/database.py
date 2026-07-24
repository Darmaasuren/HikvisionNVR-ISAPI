from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
from typing import Any


DEFAULT_DB_PATH = Path("data/hikvision_gateway.sqlite3")


@dataclass(frozen=True)
class StoredNvrConfig:
    serial_number: str
    device_name: str
    model: str
    ip_address: str
    username: str
    password: str
    http_port: int
    rtsp_port: int
    created_at: str
    updated_at: str


def get_database_path() -> Path:
    return Path(os.getenv("HIKVISION_DB_PATH") or DEFAULT_DB_PATH)


def _connect() -> sqlite3.Connection:
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_database() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS nvr_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                serial_number TEXT NOT NULL DEFAULT '',
                device_name TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT '',
                ip_address TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                http_port INTEGER NOT NULL DEFAULT 80,
                rtsp_port INTEGER NOT NULL DEFAULT 554,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def _row_to_config(row: sqlite3.Row | None) -> StoredNvrConfig | None:
    if row is None:
        return None

    return StoredNvrConfig(
        serial_number=row["serial_number"],
        device_name=row["device_name"],
        model=row["model"],
        ip_address=row["ip_address"],
        username=row["username"],
        password=row["password"],
        http_port=row["http_port"],
        rtsp_port=row["rtsp_port"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def get_active_nvr_config() -> StoredNvrConfig | None:
    init_database()

    with _connect() as connection:
        row = connection.execute(
            """
            SELECT serial_number, device_name, model, ip_address, username, password,
                   http_port, rtsp_port, created_at, updated_at
            FROM nvr_config
            WHERE id = 1
            """
        ).fetchone()

    return _row_to_config(row)


def save_active_nvr_config(
    *,
    ip_address: str,
    username: str,
    password: str,
    http_port: int,
    rtsp_port: int,
    serial_number: str = "",
    device_name: str = "",
    model: str = "",
) -> StoredNvrConfig:
    init_database()
    now = datetime.now(timezone.utc).isoformat()
    existing = get_active_nvr_config()
    created_at = existing.created_at if existing is not None else now

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO nvr_config (
                id, serial_number, device_name, model, ip_address, username, password,
                http_port, rtsp_port, created_at, updated_at
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                serial_number = excluded.serial_number,
                device_name = excluded.device_name,
                model = excluded.model,
                ip_address = excluded.ip_address,
                username = excluded.username,
                password = excluded.password,
                http_port = excluded.http_port,
                rtsp_port = excluded.rtsp_port,
                updated_at = excluded.updated_at
            """,
            (
                serial_number,
                device_name,
                model,
                ip_address,
                username,
                password,
                http_port,
                rtsp_port,
                created_at,
                now,
            ),
        )

    saved = get_active_nvr_config()
    if saved is None:
        raise RuntimeError("Failed to save active NVR config")
    return saved


def update_active_nvr_ip(ip_address: str) -> bool:
    init_database()
    now = datetime.now(timezone.utc).isoformat()

    with _connect() as connection:
        cursor = connection.execute(
            """
            UPDATE nvr_config
            SET ip_address = ?, updated_at = ?
            WHERE id = 1
            """,
            (ip_address, now),
        )

    return cursor.rowcount > 0


def public_config(config: StoredNvrConfig) -> dict[str, Any]:
    return {
        "serial_number": config.serial_number,
        "device_name": config.device_name,
        "model": config.model,
        "ip_address": config.ip_address,
        "username": config.username,
        "http_port": config.http_port,
        "rtsp_port": config.rtsp_port,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }
