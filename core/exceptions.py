class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, message: str = "Recurso não encontrado") -> None:
        super().__init__(message, status_code=404)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Não autenticado") -> None:
        super().__init__(message, status_code=401)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Acesso negado") -> None:
        super().__init__(message, status_code=403)


class ConflictError(AppException):
    def __init__(self, message: str = "Conflito de recursos") -> None:
        super().__init__(message, status_code=409)


class BadRequestError(AppException):
    def __init__(self, message: str = "Requisição inválida") -> None:
        super().__init__(message, status_code=400)
