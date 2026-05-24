from ipaddress import ip_address, ip_network

from fastapi import HTTPException, Request

from app.core.config import settings


def require_internal_request(request: Request) -> None:
    client = request.client
    if client is None or not client.host:
        raise HTTPException(status_code=403, detail="Client origin unavailable")

    host = client.host
    try:
        source_ip = ip_address(host)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Invalid client address") from exc

    for network_text in settings.dashboard_internal_network_list:
        if source_ip in ip_network(network_text, strict=False):
            return

    raise HTTPException(status_code=403, detail="Dashboard access is limited to internal networks")
