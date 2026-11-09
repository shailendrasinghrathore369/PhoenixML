from fastapi import HTTPException, status

class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class InvalidTokenError(AuthenticationError):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(detail=detail)

class ExpiredTokenError(AuthenticationError):
    def __init__(self, detail: str = "Token has expired"):
        super().__init__(detail=detail)

class InactiveUserError(HTTPException):
    def __init__(self, detail: str = "Inactive user"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

class AuthorizationError(HTTPException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
