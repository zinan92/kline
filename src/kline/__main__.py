"""Run with: python -m kline"""

import uvicorn

from kline.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "kline.app:create_app",
        factory=True,
        host="0.0.0.0",
        port=settings.port,
        reload=True,
    )
