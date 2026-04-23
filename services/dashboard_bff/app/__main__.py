# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uvicorn

from services.dashboard_bff.app.main import create_app

app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "services.dashboard_bff.app.__main__:app",
        host="0.0.0.0",  # noqa: S104
        port=8009,
        reload=False,
    )
