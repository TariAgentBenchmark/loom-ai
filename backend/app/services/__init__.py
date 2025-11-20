__all__ = [
    "ai_client",
    "AuthService",
    "ProcessingService",
    "CreditService",
    "FileService",
    "PaymentService",
    "lakala_counter_service",
    "PaymentMethods",
    "BusinessTypes",
    "CardTypes",
]


def __getattr__(name):
    if name == "ai_client":
        from .ai_client import ai_client as _ai_client

        return _ai_client
    if name == "AuthService":
        from .auth_service import AuthService as _AuthService

        return _AuthService
    if name == "ProcessingService":
        from .processing_service import ProcessingService as _ProcessingService

        return _ProcessingService
    if name == "CreditService":
        from .credit_service import CreditService as _CreditService

        return _CreditService
    if name == "FileService":
        from .file_service import FileService as _FileService

        return _FileService
    if name == "PaymentService":
        from .payment_service import PaymentService as _PaymentService

        return _PaymentService
    if name == "lakala_counter_service":
        from .lakala_counter_service import lakala_counter_service as _lakala_counter_service

        return _lakala_counter_service
    if name == "PaymentMethods":
        from .lakala_counter_service import PaymentMethods as _PaymentMethods

        return _PaymentMethods
    if name == "BusinessTypes":
        from .lakala_counter_service import BusinessTypes as _BusinessTypes

        return _BusinessTypes
    if name == "CardTypes":
        from .lakala_counter_service import CardTypes as _CardTypes

        return _CardTypes
    raise AttributeError(f"module 'app.services' has no attribute {name!r}")
