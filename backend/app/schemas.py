from datetime import datetime
import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    paternal_surname: str = Field(min_length=2, max_length=100)
    maternal_surname: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str = Field(min_length=10, max_length=25)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

    @field_validator("name", "paternal_surname", "maternal_surname")
    @classmethod
    def validate_person_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.split())
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]+", value):
            raise ValueError("Utiliza únicamente letras, espacios, apóstrofes o guiones.")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = re.sub(r"[\s()-]", "", value)
        if normalized.startswith("+52"):
            normalized = normalized[3:]
        elif normalized.startswith("52") and len(normalized) == 12:
            normalized = normalized[2:]
        if not normalized.isdigit() or len(normalized) != 10:
            raise ValueError("Ingresa un teléfono mexicano válido de 10 dígitos.")
        return value.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    name: str
    paternal_surname: str | None = None
    maternal_surname: str | None = None
    phone: str | None = None
    email: EmailStr
    roles: list[str]
    permissions: list[str]


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserResponse
