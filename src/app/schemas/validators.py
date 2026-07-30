from ipaddress import IPv4Network, ip_address


def validate_ip_literal(value: str, *, field_name: str) -> str:
    if not value:
        return value

    try:
        ip_address(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid IP address") from exc
    return value


def validate_private_nvr_ip(value: str) -> str:
    validate_ip_literal(value, field_name="ip_address")
    address = ip_address(value)

    if (
        not address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
        or address.is_reserved
    ):
        raise ValueError(
            "ip_address must be a private network address and cannot be "
            "loopback, link-local, multicast, unspecified, or reserved"
        )
    return value


def validate_subnet_mask(value: str, *, ip_version: str) -> str:
    if not value:
        return value

    if ip_version == "v4":
        try:
            IPv4Network(f"0.0.0.0/{value}")
        except ValueError as exc:
            raise ValueError("subnet_mask must be a valid IPv4 subnet mask") from exc
        return value

    if ip_version == "v6":
        try:
            prefix_length = int(value)
        except ValueError as exc:
            raise ValueError(
                "subnet_mask must be an IPv6 prefix length between 0 and 128"
            ) from exc
        if not 0 <= prefix_length <= 128:
            raise ValueError(
                "subnet_mask must be an IPv6 prefix length between 0 and 128"
            )
        return value

    # Dual mode accepts either an IPv4 dotted netmask or an IPv6 prefix length.
    try:
        IPv4Network(f"0.0.0.0/{value}")
        return value
    except ValueError:
        pass

    try:
        prefix_length = int(value)
    except ValueError as exc:
        raise ValueError(
            "subnet_mask must be an IPv4 subnet mask or IPv6 prefix length"
        ) from exc
    if not 0 <= prefix_length <= 128:
        raise ValueError(
            "subnet_mask must be an IPv4 subnet mask or IPv6 prefix length"
        )
    return value
