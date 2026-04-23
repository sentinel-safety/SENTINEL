# sentinel-python

Official Python SDK for the SENTINEL behavioral intelligence API.

## Install

```bash
pip install dist/sentinel_python-0.1.0-py3-none-any.whl
```

## Quickstart

```python
from sentinel import SentinelClient

client = SentinelClient(api_key="sk_test_...", base_url="https://api.sentinel.example.com")
result = client.events.message(
    tenant_id="00000000-0000-0000-0000-000000000001",
    conversation_id="00000000-0000-0000-0000-000000000002",
    actor_external_id_hash="a" * 64,
    content="hello",
)
print(result.tier, result.current_score)
```

Full reference: [`docs/sdk-docs/`](../../docs/sdk-docs/). See the [root README](../../README.md) for platform context.
