from ipaddress import ip_address

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.validators import (
    validate_ip_literal,
    validate_private_nvr_ip,
    validate_subnet_mask,
)


class DownloadRequest(BaseModel):
    playback_uri: str = Field(..., min_length=1)
    filename: str = Field("recording.mp4", min_length=1)


class NetworkAddressRequest(BaseModel):
    ip_address: str = Field(
        "",
        description="New NVR IP address. Leave empty to keep the current value.",
    )
    subnet_mask: str = Field(
        "",
        description="Subnet mask. Leave empty to keep the current value.",
    )
    default_gateway: str = Field(
        "",
        description="Default gateway. Leave empty to keep the current value.",
    )
    primary_dns: str = Field(
        "",
        description="Primary DNS. Leave empty to keep the current value.",
    )
    secondary_dns: str = Field(
        "",
        description="Secondary DNS. Leave empty to keep the current value.",
    )
    addressing_type: str = Field("static", pattern="^(static|dynamic|apipa)$")
    ip_version: str = Field("v4", pattern="^(v4|v6|dual)$")

    @field_validator(
        "ip_address",
        "default_gateway",
        "primary_dns",
        "secondary_dns",
    )
    @classmethod
    def validate_ip_fields(cls, value: str, info) -> str:
        return validate_ip_literal(value, field_name=info.field_name)

    @model_validator(mode="after")
    def validate_network_values(self) -> "NetworkAddressRequest":
        self.subnet_mask = validate_subnet_mask(
            self.subnet_mask,
            ip_version=self.ip_version,
        )

        expected_version = {"v4": 4, "v6": 6}.get(self.ip_version)
        if expected_version is not None:
            for field_name in (
                "ip_address",
                "default_gateway",
                "primary_dns",
                "secondary_dns",
            ):
                value = getattr(self, field_name)
                if value and ip_address(value).version != expected_version:
                    raise ValueError(
                        f"{field_name} must match ip_version={self.ip_version}"
                    )
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ip_address": "",
                    "subnet_mask": "",
                    "default_gateway": "",
                    "primary_dns": "",
                    "secondary_dns": "",
                    "addressing_type": "static",
                    "ip_version": "v4",
                }
            ]
        }
    }


class NvrSetupRequest(BaseModel):
    ip_address: str = Field(..., min_length=1)
    username: str = Field("admin", min_length=1)
    password: str = ""
    http_port: int = Field(80, ge=1, le=65535)
    rtsp_port: int = Field(554, ge=1, le=65535)

    @field_validator("ip_address")
    @classmethod
    def validate_nvr_ip_address(cls, value: str) -> str:
        return validate_private_nvr_ip(value)
