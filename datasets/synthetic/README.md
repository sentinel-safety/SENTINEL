# SENTINEL Synthetic Grooming-Detection Dataset

Reproducible synthetic conversation data for research into online grooming detection. Surface cues only — no explicit content.

## Versions

| Version | Conversations | Seed | Released |
|---------|--------------|------|----------|
| [v1](v1/) | 50 | 424242 | 2026-04-22 |

## License

CC-BY-4.0 with a use-restriction addendum (see [v1/LICENSE](v1/LICENSE)). The dataset may NOT be used to train models that produce content targeting minors.

## Load

```python
import orjson
from pathlib import Path

conversations = [
    orjson.loads(line)
    for line in Path("datasets/synthetic/v1/conversations.jsonl").read_bytes().splitlines()
    if line.strip()
]
```

Each record: `id`, `stage`, `demographics`, `platform`, `communication_style`, `language`, `turns`. Verify integrity by comparing `sha256sum` of `conversations.jsonl` against `v1/manifest.json → sha256_conversations`.

See [v1/DATASHEET.md](v1/DATASHEET.md) for full generation axes and ethics notes, and the [root README](../../README.md) for platform context.
