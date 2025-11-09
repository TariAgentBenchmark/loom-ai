"""Payment service exposing Lakala Micropay helper methods."""

from __future__ import annotations

import logging
from typing import Any, Dict

from app.services.lakala_api import LakalaAPIError, LakalaApiClient


class PaymentService:
    """Thin wrapper around LakalaApiClient for FastAPI endpoints."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.lakala_client = LakalaApiClient()

    async def create_lakala_micropay(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call Lakala's micropay API using the unified signing client."""

        try:
            return self.lakala_client.micropay(req_data)
        except LakalaAPIError as exc:
            self.logger.error("创建拉卡拉 Micropay 订单失败: %s", exc)
            raise
