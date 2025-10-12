import json
import logging
from typing import Any, Dict, Optional

from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_credentials.provider.static_ak import StaticAKCredentialsProvider
from alibabacloud_dypnsapi20170525 import models as dypnsapi_models
from alibabacloud_dypnsapi20170525.client import Client as DypnsapiClient
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
        duplicate_policy_minutes: int = 5,
        code_length: int = 6,
    ) -> None:
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.sign_name = sign_name
        self.template_code = template_code
        self.region_id = region_id
        self.duplicate_policy_minutes = duplicate_policy_minutes
        self.code_length = code_length

        self._client = self._create_client()

    def send_sms(self, phone: str, template_params: Optional[Dict[str, Any]] = None) -> bool:
        """Send SMS using Aliyun Dypns API."""
        template_params = template_params or {}
        request = dypnsapi_models.SendSmsVerifyCodeRequest()
        request.phone_number = phone
        request.sign_name = self.sign_name
        request.template_code = self.template_code
        request.template_param = json.dumps(template_params, ensure_ascii=False)
        request.code_length = len(str(template_params.get("code", ""))) or self.code_length
        request.duplicate_policy = self.duplicate_policy_minutes

        runtime = util_models.RuntimeOptions()
        try:
            response = self._client.send_sms_verify_code_with_options(request, runtime)
        except Exception as error:  # noqa: BLE001
            message = getattr(error, "message", str(error))
            logger.error("Aliyun SMS request failed: %s", message)
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

        logger.error(
            "Aliyun SMS send failed for %s: code=%s, message=%s, request_id=%s",
            phone,
            getattr(body, "code", None),
            getattr(body, "message", None),
            getattr(body, "request_id", None),
        )
        return False

    def _create_client(self) -> DypnsapiClient:
        """Create Alibaba Cloud Dypns client via official SDK."""
        provider = StaticAKCredentialsProvider(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
        )
        credential = CredentialClient(provider=provider)
        config = open_api_models.Config(credential=credential)
        config.endpoint = "dypnsapi.aliyuncs.com"
        config.region_id = self.region_id
        return DypnsapiClient(config)
