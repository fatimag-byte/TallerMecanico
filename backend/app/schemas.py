from datetime import datetime
import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    paternal_surname: str = Field(min_length=2, max_length=100)
    maternal_surname: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str = Field(min_length=10, max_length=25)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

    @field_validator("maternal_surname", mode="before")
    @classmethod
    def normalize_empty_maternal_surname(cls, value: str | None) -> str | None:
        return None if value is None or not str(value).strip() else value

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


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=10, max_length=128)


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


class PermissionResponse(BaseModel):
    id: int
    code: str
    description: str


class RoleRequest(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    description: str = Field(default="", max_length=255)
    permission_ids: list[int] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("El nombre del rol es obligatorio.")
        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("permission_ids")
    @classmethod
    def validate_permission_ids(cls, value: list[int]) -> list[int]:
        if any(item < 1 for item in value):
            raise ValueError("Los permisos seleccionados no son válidos.")
        return list(dict.fromkeys(value))


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str
    permissions: list[PermissionResponse]
    user_count: int
    is_protected: bool


class RoleNameAvailabilityResponse(BaseModel):
    available: bool


class RoleUserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool


class RoleUsersResponse(BaseModel):
    role: RoleResponse
    assigned: list[RoleUserResponse]
    available: list[RoleUserResponse]

class WorkshopRequest(BaseModel):
    name: str = Field(min_length=3,max_length=160); rfc: str = Field(min_length=12,max_length=13); contact_email: EmailStr
    street_and_number: str = Field(min_length=4,max_length=255); neighborhood: str = Field(min_length=2,max_length=150); postal_code: str = Field(pattern=r"^\d{5}$")
    state: str = Field(min_length=2,max_length=80); municipality: str = Field(min_length=2,max_length=120); photo_url: str|None=None
    @field_validator('rfc')
    @classmethod
    def rfc_format(cls,v):
        v=v.strip().upper()
        if not re.fullmatch(r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$",v): raise ValueError('RFC inválido.')
        return v

class WorkshopUpdateRequest(WorkshopRequest):
    is_active: bool

class CustomerRequest(BaseModel):
    first_name:str=Field(min_length=2,max_length=120); paternal_surname:str=Field(min_length=2,max_length=100); maternal_surname:str|None=None
    street_and_number:str=Field(min_length=4,max_length=255); neighborhood:str|None=Field(default=None,max_length=150); postal_code:str|None=Field(default=None,max_length=5); municipality:str=Field(min_length=2,max_length=120); state:str=Field(min_length=2,max_length=80)
    primary_email:EmailStr; secondary_email:EmailStr|None=None; primary_phone:str; secondary_phone:str|None=None
    @field_validator('first_name','paternal_surname','maternal_surname','street_and_number','neighborhood','municipality','state')
    @classmethod
    def clean(cls,v): return ' '.join(v.split()) if v else v
    @field_validator('primary_phone','secondary_phone')
    @classmethod
    def phone(cls,v):
        if v is None:return v
        d=re.sub(r'\D','',v)[-10:]
        if len(d)!=10:raise ValueError('Teléfono de 10 dígitos requerido.')
        return d
    @field_validator('primary_email','secondary_email')
    @classmethod
    def gmail_domain(cls,v):
        if v is None:return v
        domain=str(v).rsplit('@',1)[-1].lower()
        common_gmail_typos={'gmal.com','gamil.com','gmial.com','gmail.co','gmail.con','gmail.comm','gmail.om','gmail,com'}
        if domain in common_gmail_typos or (domain.startswith('gmail') and domain != 'gmail.com'):
            raise ValueError('Revisa el correo de Gmail: debe terminar exactamente en @gmail.com.')
        return v
    @field_validator('postal_code')
    @classmethod
    def postal_code_format(cls,v):
        if v is not None and not re.fullmatch(r'\d{5}', v): raise ValueError('Código postal de 5 dígitos requerido.')
        return v

class VehicleRequest(BaseModel):
    vin:str=Field(min_length=17,max_length=17); make:str=Field(min_length=2,max_length=80); model:str=Field(min_length=1,max_length=100); year:int=Field(ge=1886,le=2100)
    plate:str|None=None; version:str|None=None; color:str|None=None; mileage:int|None=Field(default=None,ge=0)
    @field_validator('vin')
    @classmethod
    def vin_format(cls,v):
        v=re.sub(r'[ -]','',v).upper()
        if not re.fullmatch(r'^[A-HJ-NPR-Z0-9]{17}$',v):raise ValueError('VIN inválido: usa 17 caracteres sin I, O ni Q.')
        return v

class VehicleUpdateRequest(BaseModel):
    """Campos propios de una unidad; nunca cambia su cliente ni taller asociado."""
    model_config = ConfigDict(extra='forbid')
    make: str | None = Field(default=None, min_length=2, max_length=80)
    model: str | None = Field(default=None, min_length=1, max_length=100)
    year: int | None = Field(default=None, ge=1886, le=2100)
    plate: str | None = Field(default=None, min_length=1, max_length=12)
    version: str | None = Field(default=None, max_length=100)
    color: str | None = Field(default=None, max_length=60)
    mileage: int | None = Field(default=None, ge=0)

    @field_validator('make', 'model', 'plate')
    @classmethod
    def required_text(cls, value: str | None):
        if value is None:
            return None
        value = ' '.join(value.split())
        if not value:
            raise ValueError('Este campo es obligatorio.')
        return value

    @field_validator('version', 'color')
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        return ' '.join(value.split()) if value else None

    @model_validator(mode='after')
    def requires_change(self):
        if not self.model_fields_set:
            raise ValueError('Indica al menos un dato para actualizar.')
        return self
