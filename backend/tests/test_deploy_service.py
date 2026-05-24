from app.integrations.coolify import CoolifyClient


def test_coolify_client_configuration() -> None:
    client = CoolifyClient(
        host="https://coolify.example.com/",
        api_key="secret",
        webhook_url="https://coolify.example.com/api/v1/deploy?uuid=x",
    )

    assert client.host == "https://coolify.example.com"
    assert "uuid=x" in client.webhook_url
