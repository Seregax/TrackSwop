class AppError(Exception):
    """Base application exception"""

    def __init__(self, message: str, user_message: str = None):
        self.message = message
        self.user_message = user_message or message
        super().__init__(message)


class ServiceError(AppError):
    pass


class AuthError(ServiceError):
    pass


class ExportError(ServiceError):
    pass
