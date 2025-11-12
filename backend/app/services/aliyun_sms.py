import json
import logging
from typing import Any, Dict, Optional

from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_credentials.provider.static_ak import StaticAKCredentialsProvider
from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


logger = logging.getLogger(__name__)


class AliyunSMSClient:
    """Aliyun SMS client implemented with official SDK."""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        sign_name: str,
        template_code: str,
        *,
        region_id: str = "cn-hangzhou",
    ) -> None:
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.sign_name = sign_name
        self.template_code = template_code
        self.region_id = region_id

        self._client = self._create_client()

    def send_sms(self, phone: str, template_params: Optional[Dict[str, Any]] = None) -> bool:
        """Send SMS using Aliyun Dypns API."""
        template_params = template_params or {}
        request = dysmsapi_models.SendSmsRequest()
        request.phone_numbers = phone
        request.sign_name = self.sign_name
        request.template_code = self.template_code
        request.template_param = (
            json.dumps(template_params, ensure_ascii=False) if template_params else None
        )

        request_snapshot = {
            "phone_numbers": request.phone_numbers,
            "sign_name": request.sign_name,
            "template_code": request.template_code,
            "template_param": request.template_param,
            "region_id": self.region_id,
        }
        logger.info("Sending Aliyun SMS with request %s", request_snapshot)

        runtime = util_models.RuntimeOptions()
        try:
            response = self._client.send_sms_with_options(request, runtime)
        except Exception as error:  # noqa: BLE001
            message = getattr(error, "message", str(error))
            logger.exception("Aliyun SMS request failed: %s | request=%s", message, request_snapshot)
            if hasattr(error, "data") and getattr(error, "data", None):
                recommend = error.data.get("Recommend")
                if recommend:
                    logger.error("Aliyun SMS recommendation: %s", recommend)
            try:
                UtilClient.assert_as_string(message)
            except Exception:  # noqa: BLE001
                pass
            return False

        body = response.body
        if getattr(body, "code", None) == "OK":
            logger.info("Aliyun SMS sent successfully to %s", phone)
            return True

        response_snapshot: Dict[str, Any]
        if hasattr(body, "to_map"):
            response_snapshot = body.to_map()  # type: ignore[assignment]
        else:
            response_snapshot = {
                "code": getattr(body, "code", None),
                "message": getattr(body, "message", None),
                "request_id": getattr(body, "request_id", None),
            }

        logger.error(
            "Aliyun SMS send failed for %s: code=%s, message=%s, request_id=%s, request=%s, response=%s",
            phone,
            getattr(body, "code", None),
            getattr(body, "message", None),
            getattr(body, "request_id", None),
            request_snapshot,
            response_snapshot,
        )
        return False

    def _create_client(self) -> DysmsapiClient:
        """Create Alibaba Cloud SMS client via official SDK."""
        provider = StaticAKCredentialsProvider(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
        )
        credential = CredentialClient(provider=provider)
        config = open_api_models.Config(credential=credential)
        config.endpoint = "dysmsapi.aliyuncs.com"
        config.region_id = self.region_id
        return DysmsapiClient(config)
