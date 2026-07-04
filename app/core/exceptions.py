class AppException(Exception):
    def __init__(self, status_code: int, detail: str, error_code: str | None = None):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


class NotFoundException(AppException):
    def __init__(self, detail: str = "Not found"):
        super().__init__(404, detail, "NOT_FOUND")


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(401, detail, "UNAUTHORIZED")


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(403, detail, "FORBIDDEN")


class ConflictException(AppException):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(409, detail, "CONFLICT")


class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(400, detail, "BAD_REQUEST")
