class UserFacingException(Exception):
    """可直接返回给前端的业务提示异常。"""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code
