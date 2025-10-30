__all__ = [
    "ai_client",
    "AuthService",
    "ProcessingService",
    "CreditService",
    "FileService",
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
    raise AttributeError(f"module 'app.services' has no attribute {name!r}")
