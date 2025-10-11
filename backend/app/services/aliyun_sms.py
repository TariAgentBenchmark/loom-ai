import base64
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx


logger = logging.getLogger(__name__)


class AliyunSMSClient:
    """Lightweight Aliyun SMS API client using RPC-style signature."""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        sign_name: str,
        template_code: str,
        *,
        region_id: str = "cn-hangzhou",
        endpoint: str = "https://dysmsapi.aliyuncs.com",
        timeout: float = 10.0,
    ) -> None:
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.sign_name = sign_name
        self.template_code = template_code
        self.region_id = region_id
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    @staticmethod
    def _percent_encode(value: Any) -> str:
        """RFC 3986 encoding with Aliyun-specific safe characters."""
        return quote(str(value), safe="~")

    def _build_query(self, params: Dict[str, Any]) -> str:
        """Create canonicalized query string."""
        sorted_params = sorted(params.items())
        return "&".join(
            f"{self._percent_encode(k)}={self._percent_encode(v)}"
            for k, v in sorted_params
        )

    def _sign(self, canonical_query: str) -> str:
        """Generate an Aliyun RPC signature."""
        string_to_sign = f"GET&%2F&{self._percent_encode(canonical_query)}"
        key = f"{self.access_key_secret}&"
        digest = hmac.new(
            key.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        return base64.b64encode(digest).decode("utf-8")

    def send_sms(self, phone: str, template_params: Optional[Dict[str, Any]] = None) -> bool:
        """Send an SMS message via Aliyun."""
        template_params = template_params or {}

        payload = {
            "AccessKeyId": self.access_key_id,
            "Action": "SendSms",
            "Format": "JSON",
            "PhoneNumbers": phone,
            "RegionId": self.region_id,
            "SignName": self.sign_name,
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": str(uuid.uuid4()),
            "SignatureVersion": "1.0",
            "TemplateCode": self.template_code,
            "TemplateParam": json.dumps(template_params, ensure_ascii=False),
            "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Version": "2017-05-25",
        }

        canonical_query = self._build_query(payload)
        signature = self._sign(canonical_query)

        signed_query = self._build_query({**payload, "Signature": signature})
        request_url = f"{self.endpoint}/?{signed_query}"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(request_url)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as http_exc:
            logger.error("Aliyun SMS request failed: %s", http_exc)
            return False
        except ValueError as json_exc:
            logger.error("Invalid JSON response from Aliyun SMS: %s", json_exc)
            return False

        if data.get("Code") == "OK":
            logger.info("Aliyun SMS sent successfully to %s", phone)
            return True

        logger.error(
            "Aliyun SMS send failed for %s: code=%s, message=%s",
            phone,
            data.get("Code"),
            data.get("Message"),
        )
        return False
