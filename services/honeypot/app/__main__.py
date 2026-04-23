# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uvicorn

from shared.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "services.honeypot.app.main:create_app",
        host="0.0.0.0",  # noqa: S104
        port=8010,
        factory=True,
        log_config=None,
        reload=settings.env == "dev",
    )


if __name__ == "__main__":
    main()
