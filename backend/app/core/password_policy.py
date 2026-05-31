"""Password strength checks shared by register and reset flows."""

from fastapi import HTTPException, status

# Small blocklist — extend as needed; not a substitute for breached-password API.
_COMMON_PASSWORDS = frozenset(
    {
        "password",
        "password1",
        "password123",
        "123456",
        "12345678",
        "123456789",
        "1234567890",
        "qwerty",
        "qwerty123",
        "admin123",
        "letmein",
        "welcome",
        "iloveyou",
        "monkey",
        "dragon",
        "football",
        "baseball",
        "abc123",
        "111111",
        "000000",
        "changeme",
        "secret",
        "master",
        "login",
        "passw0rd",
        "P@ssw0rd",
        "P@ssword1",
    }
)


def assert_password_strength(password: str) -> None:
    """Raise HTTP 400 when password is too weak or on the common-password list."""
    if len(password) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu phải có ít nhất 10 ký tự.",
        )
    if password.lower() in _COMMON_PASSWORDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu quá phổ biến. Vui lòng chọn mật khẩu khác.",
        )
    if password.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu không được chỉ gồm chữ số.",
        )
