"""Lakala Micropay API client translated from the official Java demo."""

from __future__ import annotations

import base64
import json
import logging
import secrets
import string
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.core.config import settings


class LakalaAPIError(RuntimeError):
    """Raised when the Lakala OpenAPI responds with an error."""


@dataclass(slots=True)
class LakalaResponseVerification:
    """Carries response headers needed for signature verification."""

    app_id: str
    serial_no: str
    timestamp: str
    nonce: str
    signature: str


class LakalaApiClient:
    """Python implementation of the Lakala SHA256withRSA signing process."""

    _NONCE_CHARSET = string.ascii_letters + string.digits

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        app_id: Optional[str] = None,
        serial_no: Optional[str] = None,
        merchant_no: Optional[str] = None,
        term_no: Optional[str] = None,
        private_key_path: Optional[str] = None,
        response_certificate_path: Optional[str] = None,
        notify_certificate_path: Optional[str] = None,
        version: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.base_url = (base_url or settings.lakala_api_base_url).rstrip("/")
        self.schema = settings.lakala_api_schema
        self.version = version or settings.lakala_api_version
        self.app_id = app_id or settings.lakala_app_id
        self.serial_no = serial_no or settings.lakala_serial_no
        self.merchant_no = merchant_no or settings.lakala_merchant_no
        self.term_no = term_no or settings.lakala_term_no
        self.timeout = timeout or settings.lakala_default_timeout

        self._private_key = self._load_private_key(
            private_key_path or settings.lakala_private_key_path
        )
        self._response_certificate = self._load_certificate(
            response_certificate_path or settings.lakala_certificate_path
        )
        self._notify_certificate = self._load_certificate(
            notify_certificate_path
            or settings.lakala_notify_certificate_path
            or response_certificate_path
            or settings.lakala_certificate_path
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def create_counter_order(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create payment order in Aggregated Payment Gateway.
        Endpoint: /api/v3/ccss/counter/order/special_create
        """

        payload = self._build_standard_payload(req_data)
        return self._request("/api/v3/ccss/counter/order/special_create", payload)

    def query_counter_order(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query payment order status.
        Endpoint: /api/v3/ccss/counter/order/query
        """

        payload = self._build_standard_payload(req_data)
        return self._request("/api/v3/ccss/counter/order/query", payload)

    def close_counter_order(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Close payment order.
        Endpoint: /api/v3/ccss/counter/order/close
        """

        payload = self._build_standard_payload(req_data)
        return self._request("/api/v3/ccss/counter/order/close", payload)

    def call(
        self,
        api_path: str,
        req_data: Dict[str, Any],
        *,
        inject_defaults: bool = True,
    ) -> Dict[str, Any]:
        """Call any Lakala OpenAPI endpoint with the same signing scheme."""

        payload = (
            self._build_standard_payload(req_data)
            if inject_defaults
            else self._build_payload_wrapper(req_data)
        )
        return self._request(api_path, payload)

    def verify_async_notify(
        self,
        *,
        timestamp: str,
        nonce: str,
        body: str,
        signature: str,
    ) -> bool:
        """Verify signatures for asynchronous notifications."""

        message = f"{timestamp}\n{nonce}\n{body}\n"
        return self._verify_signature(
            signature,
            message.encode("utf-8"),
            certificate=self._notify_certificate,
        )

    # ------------------------------------------------------------------
    # Request plumbing
    # ------------------------------------------------------------------
    def _request(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Build JSON body once so the same bytes are used for signing + transport
        body_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        timestamp = str(int(time.time()))
        nonce = self._generate_nonce()
        authorization = self._build_authorization(body_str, timestamp, nonce)

        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"{self.schema} {authorization}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            response = requests.post(
                url,
                data=body_str.encode("utf-8"),
                timeout=self.timeout,
                headers=headers,
            )
        except requests.RequestException as exc:
            raise LakalaAPIError(f"Lakala API request failed: {exc}") from exc

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise LakalaAPIError(
                f"Lakala API HTTP error {response.status_code}: {response.text}"
            ) from exc

        body_text = response.text
        verification = self._extract_verification_headers(response)
        if not self._verify_signature(
            verification.signature,
            self._response_signature_plaintext(verification, body_text).encode(
                "utf-8"
            ),
            certificate=self._response_certificate,
        ):
            raise LakalaAPIError("Lakala API signature verification failed")

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise LakalaAPIError(f"Lakala API returned invalid JSON: {body_text}") from exc

        return data

    def _build_standard_payload(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        merged_data = {k: v for k, v in (req_data or {}).items()}
        merged_data.setdefault("merchant_no", self.merchant_no)
        merged_data.setdefault("term_no", self.term_no)

        return self._build_payload_wrapper(merged_data)

    def _build_payload_wrapper(self, req_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "req_time": datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "version": self.version,
            "out_org_code": self.app_id,
            "req_data": req_data,
        }

    # ------------------------------------------------------------------
    # Signing helpers
    # ------------------------------------------------------------------
    def _build_authorization(self, body: str, timestamp: str, nonce: str) -> str:
        message = (
            f"{self.app_id}\n{self.serial_no}\n{timestamp}\n{nonce}\n{body}\n"
        )
        signature = self._sign(message.encode("utf-8"))

        return (
            f'appid="{self.app_id}",'
            f'serial_no="{self.serial_no}",'
            f'timestamp="{timestamp}",'
            f'nonce_str="{nonce}",'
            f'signature="{signature}"'
        )

    def _sign(self, message: bytes) -> str:
        signature = self._private_key.sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")

    def _verify_signature(
        self,
        signature_b64: str,
        message: bytes,
        *,
        certificate: x509.Certificate,
    ) -> bool:
        try:
            certificate.public_key().verify(
                base64.b64decode(signature_b64),
                message,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Lakala signature verification failed: %s", exc)
            return False

    @staticmethod
    def _response_signature_plaintext(
        verification: LakalaResponseVerification,
        body: str,
    ) -> str:
        return (
            f"{verification.app_id}\n"
            f"{verification.serial_no}\n"
            f"{verification.timestamp}\n"
            f"{verification.nonce}\n"
            f"{body}\n"
        )

    def _extract_verification_headers(
        self,
        response: requests.Response,
    ) -> LakalaResponseVerification:
        headers = response.headers
        required = {
            "Lklapi-Appid": None,
            "Lklapi-Serial": None,
            "Lklapi-Timestamp": None,
            "Lklapi-Nonce": None,
            "Lklapi-Signature": None,
        }

        for key in required:
            value = headers.get(key)
            if not value:
                raise LakalaAPIError(f"Missing Lakala response header: {key}")
            required[key] = value.strip()

        return LakalaResponseVerification(
            app_id=required["Lklapi-Appid"],
            serial_no=required["Lklapi-Serial"],
            timestamp=required["Lklapi-Timestamp"],
            nonce=required["Lklapi-Nonce"],
            signature=required["Lklapi-Signature"],
        )

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _load_private_key(path: str):
        file_path = Path(path).expanduser()
        if not file_path.exists():
            raise LakalaAPIError(f"Private key file not found: {file_path}")

        try:
            key_bytes = file_path.read_bytes()
            return serialization.load_pem_private_key(key_bytes, password=None)
        except Exception as exc:  # noqa: BLE001
            raise LakalaAPIError(
                f"Unable to load Lakala private key from {file_path}"
            ) from exc

    @staticmethod
    def _load_certificate(path: Optional[str]):
        if not path:
            raise LakalaAPIError("Certificate path is not configured")

        file_path = Path(path).expanduser()
        if not file_path.exists():
            raise LakalaAPIError(f"Certificate file not found: {file_path}")

        try:
            cert_bytes = file_path.read_bytes()
            return x509.load_pem_x509_certificate(cert_bytes)
        except ValueError:
            # Retry as DER
            cert_bytes = file_path.read_bytes()
            return x509.load_der_x509_certificate(cert_bytes)
        except Exception as exc:  # noqa: BLE001
            raise LakalaAPIError(
                f"Unable to load Lakala certificate from {file_path}"
            ) from exc

    @classmethod
    def _generate_nonce(cls, length: int = 32) -> str:
        return "".join(secrets.choice(cls._NONCE_CHARSET) for _ in range(length))
