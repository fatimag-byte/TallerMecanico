from datetime import datetime, timedelta, timezone
from functools import lru_cache
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session, joinedload
from .config import get_settings
from .database import get_db
from .dependencies import get_current_user, require_permission
from .models import AuditLog, Customer, PasswordResetToken, Permission, RefreshToken, Role, User, Vehicle, VehiclePhoto, Workshop
from .schemas import AuthResponse, CustomerRequest, ForgotPasswordRequest, LoginRequest, PermissionResponse, RefreshRequest, RegisterRequest, ResetPasswordRequest, RoleNameAvailabilityResponse, RoleRequest, RoleResponse, RoleUserResponse, RoleUsersResponse, UserResponse, VehicleRequest, VehicleUpdateRequest, WorkshopRequest, WorkshopUpdateRequest
from .security import create_access_token, hash_password, hash_refresh_token, new_refresh_token, verify_password

app = FastAPI(title="Taller Mecánico API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health", include_in_schema=False)
def health_check(db: Session = Depends(get_db)):
    """Read-only health check for Railway, including database connectivity."""
    db.execute(text("SELECT 1"))
    return {"status": "ok"}

POSTAL_API = "https://cp.terio.dev"

def _postal(path: str, query: dict | None = None) -> dict:
    """Consulta SEPOMEX normalizado sin exponer al proveedor al navegador."""
    url = f"{POSTAL_API}{path}" + (f"?{urlencode(query)}" if query else "")
    request = Request(url, headers={"User-Agent": "AutoGestion-Taller/1.0 (postal lookup)"})
    for attempt in range(2):
        try:
            with urlopen(request, timeout=10) as response:
                import json
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                raise HTTPException(404, "No encontramos información para este código postal.")
            if attempt == 1:
                raise HTTPException(503, "No pudimos consultar las localidades. Intenta nuevamente.")
        except (URLError, TimeoutError):
            if attempt == 1:
                raise HTTPException(503, "No pudimos consultar las localidades. Intenta nuevamente.")

@lru_cache(maxsize=64)
def _states() -> list[dict]:
    return [{"id": x["codigo_estado"], "name": x["estado"]} for x in _postal("/v1/estados").get("datos", [])]

@app.get("/api/ubicaciones/estados")
def location_states(_: User = Depends(require_permission("workshops:manage"))):
    return _states()

@lru_cache(maxsize=128)
def _municipalities(state_id: str) -> list[dict]:
    return [{"id": x["codigo_municipio"], "name": x["municipio"]} for x in _postal(f"/v1/estados/{state_id}/municipios").get("datos", [])]

@app.get("/api/ubicaciones/municipios")
def location_municipalities(estado_id: str, _: User = Depends(require_permission("workshops:manage"))):
    return _municipalities(estado_id)

@app.get("/api/ubicaciones/localidades")
def location_settlements(estado_id: str, municipio_id: str, _: User = Depends(require_permission("workshops:manage"))):
    rows = _postal("/v1/buscar", {"texto": next((x["name"] for x in _municipalities(estado_id) if x["id"] == municipio_id), ""), "limite": 50}).get("datos", [])
    return [{"id": x["clave_asentamiento"], "name": x["asentamiento"], "postal_code": x["codigo_postal"], "type": x["tipo_asentamiento"]} for x in rows if x.get("codigo_estado") == estado_id and x.get("codigo_municipio") == municipio_id]

@app.get("/api/ubicaciones/codigo-postal/{postal_code}")
def location_postal_code(postal_code: str, _: User = Depends(require_permission("workshops:manage"))):
    if not postal_code.isdigit() or len(postal_code) != 5:
        raise HTTPException(422, "El código postal debe tener cinco dígitos.")
    rows = _postal(f"/v1/codigos-postales/{postal_code}").get("datos", [])
    if not rows:
        raise HTTPException(404, "No encontramos información para este código postal.")
    first = rows[0]
    return {"state": {"id": first["codigo_estado"], "name": first["estado"]}, "municipality": {"id": first["codigo_municipio"], "name": first["municipio"]}, "settlements": [{"id": x["clave_asentamiento"], "name": x["asentamiento"], "postal_code": x["codigo_postal"], "type": x["tipo_asentamiento"]} for x in rows]}

def _validate_geography(state: str, municipality: str, neighborhood: str | None, postal_code: str | None) -> None:
    """Rejects only an explicitly inconsistent SEPOMEX combination."""
    if not neighborhood or not postal_code:
        return
    rows = _postal(f"/v1/codigos-postales/{postal_code}").get("datos", [])
    target = (state.casefold(), municipality.casefold(), neighborhood.casefold())
    if not any((row.get("estado", "").casefold(), row.get("municipio", "").casefold(), row.get("asentamiento", "").casefold()) == target for row in rows):
        raise HTTPException(422, "La combinación de estado, municipio, colonia y código postal no es válida.")


def seed_roles(db: Session):
    permissions = {
        "users:read": "Consultar usuarios", "users:manage": "Administrar usuarios y roles",
        "workorders:read": "Consultar órdenes", "workorders:write": "Crear y editar órdenes", "customers:manage": "Administrar clientes", "workshops:manage": "Administrar talleres", "vehicles:manage": "Administrar vehículos",
    }
    for code, description in permissions.items():
        if not db.query(Permission).filter_by(code=code).first():
            db.add(Permission(code=code, description=description))
    db.flush()
    admin = db.query(Role).filter_by(name="administrador").first()
    if not admin:
        admin = Role(name="administrador", description="Acceso completo")
        admin.permissions = db.query(Permission).all()
        db.add(admin)
    else:
        admin.permissions = db.query(Permission).all()
    technician = db.query(Role).filter_by(name="tecnico").first()
    if not technician:
        technician = Role(name="tecnico", description="Operación del taller")
        technician.permissions = db.query(Permission).filter(Permission.code.in_(["workorders:read", "workorders:write"])).all()
        db.add(technician)
    receptionist = db.query(Role).filter_by(name="recepcionista").first()
    receptionist_permissions = db.query(Permission).filter(
        Permission.code.in_(["customers:manage", "workshops:manage", "vehicles:manage"])
    ).all()
    if not receptionist:
        receptionist = Role(name="recepcionista", description="Atención a clientes y registro operativo")
        receptionist.permissions = receptionist_permissions
        db.add(receptionist)
    else:
        receptionist.permissions = receptionist_permissions
    db.commit()


@app.on_event("startup")
def startup():
    db = next(get_db())
    try:
        seed_roles(db)
    finally:
        db.close()


def user_response(user: User) -> UserResponse:
    roles = [role.name for role in user.roles]
    permissions = sorted({permission.code for role in user.roles for permission in role.permissions})
    return UserResponse(id=user.id, name=user.name, paternal_surname=user.paternal_surname, maternal_surname=user.maternal_surname, phone=user.phone, email=user.email, roles=roles, permissions=permissions)


def permission_response(permission: Permission) -> PermissionResponse:
    return PermissionResponse(id=permission.id, code=permission.code, description=permission.description)


def role_response(role: Role) -> RoleResponse:
    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=[permission_response(permission) for permission in sorted(role.permissions, key=lambda item: item.code)],
        user_count=len(role.users),
        is_protected=role.name.casefold() == "administrador",
    )


def role_by_id(role_id: int, db: Session) -> Role:
    role = db.query(Role).options(joinedload(Role.permissions), joinedload(Role.users)).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="El rol solicitado no existe.")
    return role


def role_user_response(user: User) -> RoleUserResponse:
    return RoleUserResponse(id=user.id, name=user.name, email=user.email, is_active=user.is_active)


def role_users_response(role: Role, db: Session) -> RoleUsersResponse:
    assigned = sorted(role.users, key=lambda user: (user.name.casefold(), user.email.casefold()))
    assigned_ids = [user.id for user in assigned]
    available_query = db.query(User).filter(~User.id.in_(assigned_ids)) if assigned_ids else db.query(User)
    available = available_query.order_by(User.name, User.email).all()
    return RoleUsersResponse(
        role=role_response(role),
        assigned=[role_user_response(user) for user in assigned],
        available=[role_user_response(user) for user in available],
    )


def validate_role_permissions(payload: RoleRequest, db: Session) -> list[Permission]:
    permissions = db.query(Permission).filter(Permission.id.in_(payload.permission_ids)).all() if payload.permission_ids else []
    if len(permissions) != len(payload.permission_ids):
        raise HTTPException(status_code=422, detail="Uno o más permisos seleccionados no existen.")
    return permissions


def validate_role_name(payload: RoleRequest, db: Session, excluded_id: int | None = None) -> None:
    normalized = payload.name.casefold()
    query = db.query(Role).filter(func.lower(func.trim(Role.name)) == normalized)
    if excluded_id is not None:
        query = query.filter(Role.id != excluded_id)
    if query.first():
        raise HTTPException(status_code=409, detail="Ya existe un rol con ese nombre.")


def session_response(user: User, db: Session) -> AuthResponse:
    access_token, expires_at = create_access_token(user.id)
    refresh = new_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hash_refresh_token(refresh), expires_at=datetime.now(timezone.utc) + timedelta(days=get_settings().refresh_token_days)))
    db.commit()
    return AuthResponse(access_token=access_token, refresh_token=refresh, expires_at=expires_at, user=user_response(user))


@app.post("/api/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Ya existe una cuenta registrada con este correo.")
    try:
        role_name = "administrador" if db.query(User).count() == 0 else "tecnico"
        role = db.query(Role).options(joinedload(Role.permissions)).filter_by(name=role_name).one()
        user = User(name=payload.name, paternal_surname=payload.paternal_surname, maternal_surname=payload.maternal_surname, phone=payload.phone, email=email, password_hash=hash_password(payload.password), roles=[role])
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No fue posible registrar la cuenta: el correo ya está en uso.")
    return session_response(user, db)


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.roles).joinedload(Role.permissions)).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Tu cuenta está inactiva. Contacta al administrador.")
    return session_response(user, db)


@app.post("/api/auth/refresh", response_model=AuthResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    stored = db.query(RefreshToken).options(joinedload(RefreshToken.user).joinedload(User.roles).joinedload(Role.permissions)).filter_by(token_hash=hash_refresh_token(payload.refresh_token)).first()
    now = datetime.now(timezone.utc)
    if not stored or stored.revoked_at or stored.expires_at.replace(tzinfo=timezone.utc) <= now or not stored.user.is_active:
        raise HTTPException(status_code=401, detail="Tu sesión venció. Inicia sesión nuevamente.")
    stored.revoked_at = now  # rotación: cada refresh sólo puede utilizarse una vez
    db.commit()
    return session_response(stored.user, db)


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)):
    stored = db.query(RefreshToken).filter_by(token_hash=hash_refresh_token(payload.refresh_token)).first()
    if stored and not stored.revoked_at:
        stored.revoked_at = datetime.now(timezone.utc)
        db.commit()


@app.post("/api/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Respuesta idéntica para cualquier correo: evita enumerar cuentas.
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user and user.is_active:
        # Integrar aquí el proveedor de correo con un enlace de un solo uso.
        pass
    return {"message": "Si existe una cuenta con ese correo, recibirás las instrucciones de recuperación."}


@app.post("/api/auth/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == hash_refresh_token(payload.token),
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > now,
    ).first()
    if not reset:
        raise HTTPException(status_code=400, detail="El enlace de recuperación es inválido o venció.")
    user = db.query(User).filter(User.id == reset.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=400, detail="El enlace de recuperación es inválido o venció.")
    user.password_hash = hash_password(payload.password)
    reset.used_at = now
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).update({RefreshToken.revoked_at: now})
    db.commit()


@app.get("/api/auth/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user_response(user)


@app.get("/api/users", response_model=list[UserResponse])
def list_users(_: User = Depends(require_permission("users:read")), db: Session = Depends(get_db)):
    users = db.query(User).options(joinedload(User.roles).joinedload(Role.permissions)).order_by(User.created_at.desc()).all()
    return [user_response(user) for user in users]


@app.get("/api/permissions", response_model=list[PermissionResponse])
def list_permissions(_: User = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    return [permission_response(permission) for permission in db.query(Permission).order_by(Permission.code).all()]


@app.get("/api/roles/check-name", response_model=RoleNameAvailabilityResponse)
def check_role_name(name: str = "", _: User = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    normalized = " ".join(name.split())
    if len(normalized) < 2:
        return RoleNameAvailabilityResponse(available=False)
    exists = db.query(Role.id).filter(func.lower(func.trim(Role.name)) == normalized.casefold()).first()
    return RoleNameAvailabilityResponse(available=not bool(exists))


@app.get("/api/roles", response_model=list[RoleResponse])
def list_roles(_: User = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    roles = db.query(Role).options(joinedload(Role.permissions), joinedload(Role.users)).order_by(Role.name).all()
    return [role_response(role) for role in roles]


@app.get("/api/roles/{role_id}", response_model=RoleResponse)
def get_role(role_id: int, _: User = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    return role_response(role_by_id(role_id, db))


@app.get("/api/roles/{role_id}/users", response_model=RoleUsersResponse)
def list_role_users(role_id: int, _: User = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    return role_users_response(role_by_id(role_id, db), db)


@app.post("/api/roles/{role_id}/users/{user_id}", response_model=RoleUsersResponse)
def assign_user_to_role(role_id: int, user_id: int, _: User = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    role = role_by_id(role_id, db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="El usuario solicitado no existe.")
    if any(item.id == user.id for item in role.users):
        raise HTTPException(status_code=409, detail="El usuario ya está asociado a este rol.")
    role.users.append(user)
    db.commit()
    return role_users_response(role_by_id(role.id, db), db)


@app.delete("/api/roles/{role_id}/users/{user_id}", response_model=RoleUsersResponse)
def remove_user_from_role(role_id: int, user_id: int, _: User = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    role = role_by_id(role_id, db)
    user = next((item for item in role.users if item.id == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="El usuario no está asociado a este rol.")
    if role.name.casefold() == "administrador" and user.is_active and sum(1 for item in role.users if item.is_active) <= 1:
        raise HTTPException(status_code=409, detail="No se puede retirar al último Administrador activo.")
    role.users.remove(user)
    db.commit()
    return role_users_response(role_by_id(role.id, db), db)


@app.post("/api/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleRequest, _: User = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    validate_role_name(payload, db)
    role = Role(name=payload.name, description=payload.description, permissions=validate_role_permissions(payload, db))
    try:
        db.add(role)
        db.commit()
        db.refresh(role)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un rol con ese nombre.")
    return role_response(role_by_id(role.id, db))


@app.put("/api/roles/{role_id}", response_model=RoleResponse)
def update_role(role_id: int, payload: RoleRequest, _: User = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    role = role_by_id(role_id, db)
    validate_role_name(payload, db, excluded_id=role.id)
    permissions = validate_role_permissions(payload, db)
    if role.name.casefold() == "administrador":
        codes = {permission.code for permission in permissions}
        if not {"users:read", "users:manage"}.issubset(codes):
            raise HTTPException(status_code=409, detail="El rol administrador debe conservar los permisos de consulta y administración de usuarios.")
    try:
        role.name = payload.name
        role.description = payload.description
        role.permissions = permissions
        db.commit()
        db.refresh(role)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="No fue posible actualizar el rol.")
    return role_response(role_by_id(role.id, db))


@app.delete("/api/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, _: User = Depends(require_permission("users:manage")), db: Session = Depends(get_db)):
    role = role_by_id(role_id, db)
    if role.name.casefold() == "administrador":
        raise HTTPException(status_code=409, detail="El rol administrador está protegido y no se puede eliminar.")
    if role.users:
        raise HTTPException(status_code=409, detail="No se puede eliminar un rol que tiene usuarios asociados.")
    db.delete(role)
    db.commit()

def _audit(db, kind, entity_id, action, user_id, details=None):
    db.add(AuditLog(entity_type=kind, entity_id=entity_id, action=action, actor_id=user_id, details=details))
def _workshop(id,db):
    x=db.query(Workshop).filter(Workshop.id==id,Workshop.is_active.is_(True)).first()
    if not x: raise HTTPException(404,'Taller activo no encontrado.')
    return x
def _customer_data(x,workshop): return {"id":x.id,"workshop_id":x.workshop_id,"workshop_name":workshop.name,"first_name":x.first_name,"paternal_surname":x.paternal_surname,"maternal_surname":x.maternal_surname,"street_and_number":x.street_and_number,"neighborhood":x.neighborhood,"postal_code":x.postal_code,"municipality":x.municipality,"state":x.state,"primary_email":x.primary_email,"secondary_email":x.secondary_email,"primary_phone":x.primary_phone,"secondary_phone":x.secondary_phone,"is_active":x.is_active,"created_at":x.created_at,"updated_at":x.updated_at}

def _customer_contact_matches(db, workshop_id, payload, exclude_id=None):
    """Finds contact conflicts without exposing the record that owns them."""
    emails = {str(payload.primary_email).casefold()}
    if payload.secondary_email:
        emails.add(str(payload.secondary_email).casefold())
    phones = {payload.primary_phone}
    if payload.secondary_phone:
        phones.add(payload.secondary_phone)
    customer_filters = [func.lower(Customer.primary_email).in_(emails), func.lower(Customer.secondary_email).in_(emails), Customer.primary_phone.in_(phones), Customer.secondary_phone.in_(phones)]
    query = db.query(Customer).filter(Customer.workshop_id == workshop_id, or_(*customer_filters))
    if exclude_id is not None:
        query = query.filter(Customer.id != exclude_id)
    customers = query.all()
    user_conflict = db.query(User.id).filter(or_(func.lower(User.email).in_(emails), User.phone.in_(phones))).first() is not None
    return customers, user_conflict

def _vehicle_data(x, customer, workshop, db):
    return {"id": x.id, "workshop_id": x.workshop_id, "workshop_name": workshop.name, "customer_id": x.customer_id,
            "customer_name": " ".join(filter(None, [customer.first_name, customer.paternal_surname, customer.maternal_surname])),
            "vin": x.vin, "plate": x.plate, "make": x.make, "model": x.model, "year": x.year,
            "version": x.version, "color": x.color, "mileage": x.mileage, "is_active": x.is_active,
            "created_at": x.created_at, "updated_at": x.updated_at, "photo_count": db.query(VehiclePhoto.id).filter(VehiclePhoto.vehicle_id == x.id).count()}

def _vehicle_or_404(vehicle_id, db):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle: raise HTTPException(404, "Vehículo no encontrado.")
    return vehicle

def _image_type(content: bytes, declared_type: str | None) -> str | None:
    if content.startswith(b"\xff\xd8\xff"): return "image/jpeg"
    if content.startswith(b"\x89PNG\r\n\x1a\n"): return "image/png"
    if len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP": return "image/webp"
    return None

def _workshop_data(x):
    return {"id":x.id,"name":x.name,"rfc":x.rfc,"contact_email":x.contact_email,"street_and_number":x.street_and_number,"neighborhood":x.neighborhood,"postal_code":x.postal_code,"state":x.state,"municipality":x.municipality,"photo_url":x.photo_url,"is_active":x.is_active,"created_at":x.created_at}

@app.get('/api/workshops')
def workshops(search:str='', status_filter:str='todos', _:User=Depends(require_permission('workshops:manage')),db:Session=Depends(get_db)):
    q = db.query(Workshop)
    if status_filter == 'activos': q = q.filter(Workshop.is_active.is_(True))
    if status_filter == 'inactivos': q = q.filter(Workshop.is_active.is_(False))
    if search:
        term = f'%{search.strip()}%'
        q = q.filter(or_(Workshop.name.ilike(term), Workshop.rfc.ilike(term), Workshop.contact_email.ilike(term), Workshop.municipality.ilike(term), Workshop.state.ilike(term)))
    return [_workshop_data(x) for x in q.order_by(Workshop.created_at.desc())]
@app.post('/api/workshops',status_code=201)
def create_workshop(p:WorkshopRequest,user:User=Depends(require_permission('workshops:manage')),db:Session=Depends(get_db)):
    key=' '.join(p.name.split()).casefold()
    if db.query(Workshop.id).filter(or_(Workshop.name_normalized==key,Workshop.rfc==p.rfc)).first():raise HTTPException(409,'Taller duplicado.')
    _validate_geography(p.state, p.municipality, p.neighborhood, p.postal_code)
    try:
        x=Workshop(**p.model_dump(),name_normalized=key,created_by_id=user.id);db.add(x);db.flush();_audit(db,'workshop',x.id,'create',user.id);db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Ya existe un taller con ese nombre o RFC.')
    except DataError:
        db.rollback()
        raise HTTPException(422, 'No fue posible guardar la fotografía seleccionada. Elige otra imagen válida.')
    return _workshop_data(x)

@app.put('/api/workshops/{workshop_id}')
def update_workshop(workshop_id: int, p: WorkshopUpdateRequest, user: User = Depends(require_permission('workshops:manage')), db: Session = Depends(get_db)):
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(404, 'Taller no encontrado.')
    if not workshop.is_active:
        raise HTTPException(409, 'El taller está inactivo. Actívalo antes de modificar su información.')
    normalized_name = ' '.join(p.name.split()).casefold()
    duplicate = db.query(Workshop.id).filter(Workshop.id != workshop_id, or_(Workshop.name_normalized == normalized_name, Workshop.rfc == p.rfc)).first()
    if duplicate:
        raise HTTPException(409, 'Ya existe otro taller con ese nombre o RFC.')
    address_changed = any(getattr(workshop, field) != getattr(p, field) for field in ('state', 'municipality', 'neighborhood', 'postal_code'))
    if address_changed:
        _validate_geography(p.state, p.municipality, p.neighborhood, p.postal_code)
    data = p.model_dump()
    try:
        for key, value in data.items():
            setattr(workshop, key, value)
        workshop.name_normalized = normalized_name
        _audit(db, 'workshop', workshop.id, 'update', user.id)
        db.commit()
        db.refresh(workshop)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Ya existe otro taller con ese nombre o RFC.')
    except DataError:
        db.rollback()
        raise HTTPException(422, 'No fue posible guardar la fotografía seleccionada. Elige otra imagen válida.')
    return _workshop_data(workshop)

@app.patch('/api/workshops/{workshop_id}/status')
def deactivate_workshop(workshop_id: int, user: User = Depends(require_permission('workshops:manage')), db: Session = Depends(get_db)):
    if not any(role.name.casefold() == 'administrador' for role in user.roles):
        raise HTTPException(403, 'Solo un administrador puede desactivar talleres.')
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(404, 'Taller no encontrado.')
    if not workshop.is_active:
        raise HTTPException(409, 'Este taller ya se encuentra inactivo.')
    if db.query(Vehicle.id).filter(Vehicle.workshop_id == workshop.id).first():
        raise HTTPException(409, 'No se puede desactivar este taller porque tiene vehículos registrados.')
    workshop.is_active = False
    _audit(db, 'workshop', workshop.id, 'deactivate', user.id)
    db.commit()
    return _workshop_data(workshop)

@app.get('/api/customers')
def customers(workshop_id:int|None=None,search:str='',status_filter:str='todos',_:User=Depends(require_permission('customers:manage')),db:Session=Depends(get_db)):
    q=db.query(Customer)
    if workshop_id is not None:
        _workshop(workshop_id,db)
        q=q.filter(Customer.workshop_id==workshop_id)
    if status_filter=='activos':q=q.filter(Customer.is_active.is_(True))
    if status_filter=='inactivos':q=q.filter(Customer.is_active.is_(False))
    if search:q=q.filter(or_(Customer.first_name.ilike(f'%{search}%'),Customer.primary_email.ilike(f'%{search}%'),Customer.primary_phone.like(f'%{search}%')))
    workshop_map = {item.id: item for item in db.query(Workshop).all()}
    return [_customer_data(x, workshop_map[x.workshop_id]) for x in q.order_by(Customer.created_at.desc()) if x.workshop_id in workshop_map]

@app.post('/api/customers/duplicates')
def customer_duplicates(workshop_id:int, p:CustomerRequest, exclude_id:int|None=None, _:User=Depends(require_permission('customers:manage')),db:Session=Depends(get_db)):
    _workshop(workshop_id, db)
    q = db.query(Customer).filter(Customer.workshop_id == workshop_id)
    if exclude_id is not None: q = q.filter(Customer.id != exclude_id)
    name_match = q.filter(func.lower(Customer.first_name) == p.first_name.casefold(), func.lower(Customer.paternal_surname) == p.paternal_surname.casefold()).all()
    contact_match, user_conflict = _customer_contact_matches(db, workshop_id, p, exclude_id)
    exact_ids = {x.id for x in contact_match}
    return {"exact": [_customer_data(x, _workshop(x.workshop_id, db)) for x in contact_match], "possible": [_customer_data(x, _workshop(x.workshop_id, db)) for x in name_match if x.id not in exact_ids], "contact_in_use": user_conflict or bool(contact_match)}
@app.post('/api/customers',status_code=201)
def create_customer(workshop_id:int,p:CustomerRequest,user:User=Depends(require_permission('customers:manage')),db:Session=Depends(get_db)):
    w=_workshop(workshop_id,db);d=p.model_dump();d['primary_email']=str(p.primary_email).lower();d['secondary_email']=str(p.secondary_email).lower() if p.secondary_email else None
    _validate_geography(p.state, p.municipality, p.neighborhood, p.postal_code)
    contact_matches, user_conflict = _customer_contact_matches(db, w.id, p)
    if contact_matches or user_conflict:raise HTTPException(409,'El correo electrónico o teléfono ya está registrado. Verifica los datos para continuar.')
    x=Customer(workshop_id=w.id,created_by_id=user.id,**d);db.add(x);db.flush();_audit(db,'customer',x.id,'create',user.id);db.commit();return _customer_data(x,w)
@app.put('/api/customers/{customer_id}')
def update_customer(customer_id:int,workshop_id:int,p:CustomerRequest,user:User=Depends(require_permission('customers:manage')),db:Session=Depends(get_db)):
    w=_workshop(workshop_id,db);x=db.query(Customer).filter(Customer.id==customer_id,Customer.workshop_id==w.id).first()
    if not x:raise HTTPException(404,'Cliente no encontrado en el taller.')
    d=p.model_dump();d['primary_email']=str(p.primary_email).lower();d['secondary_email']=str(p.secondary_email).lower() if p.secondary_email else None
    _validate_geography(p.state, p.municipality, p.neighborhood, p.postal_code)
    contact_matches, user_conflict = _customer_contact_matches(db, w.id, p, x.id)
    if contact_matches or user_conflict: raise HTTPException(409,'El correo electrónico o teléfono ya está registrado. Verifica los datos para continuar.')
    for k,v in d.items():setattr(x,k,v)
    x.updated_by_id=user.id;_audit(db,'customer',x.id,'update',user.id);db.commit();return _customer_data(x,w)
@app.patch('/api/customers/{customer_id}/status')
def customer_status(customer_id:int,workshop_id:int,active:bool,user:User=Depends(require_permission('customers:manage')),db:Session=Depends(get_db)):
    w=_workshop(workshop_id,db);x=db.query(Customer).filter(Customer.id==customer_id,Customer.workshop_id==w.id).first()
    if not x:raise HTTPException(404,'Cliente no encontrado.')
    x.is_active=active;x.updated_by_id=user.id;_audit(db,'customer',x.id,'activate' if active else 'deactivate',user.id);db.commit();return _customer_data(x,w)
@app.post('/api/vehicles',status_code=201)
def create_vehicle(workshop_id:int,customer_id:int,p:VehicleRequest,user:User=Depends(require_permission('vehicles:manage')),db:Session=Depends(get_db)):
    w=_workshop(workshop_id,db);c=db.query(Customer).filter(Customer.id==customer_id,Customer.workshop_id==w.id,Customer.is_active.is_(True)).first()
    if not c:raise HTTPException(409,'Cliente activo no disponible en este taller.')
    if db.query(Vehicle.id).filter(Vehicle.vin==p.vin).first():raise HTTPException(409,'VIN ya registrado.')
    x=Vehicle(workshop_id=w.id,customer_id=c.id,created_by_id=user.id,**p.model_dump());db.add(x);db.flush();_audit(db,'vehicle',x.id,'create',user.id);db.commit();return {"id":x.id,"vin":x.vin}

@app.get('/api/vehicles')
def list_vehicles(workshop_id:int|None=None, customer_id:int|None=None, search:str='', status_filter:str='todos', _:User=Depends(require_permission('vehicles:manage')), db:Session=Depends(get_db)):
    q = db.query(Vehicle)
    if workshop_id is not None: q = q.filter(Vehicle.workshop_id == workshop_id)
    if customer_id is not None: q = q.filter(Vehicle.customer_id == customer_id)
    if status_filter == 'activos': q = q.filter(Vehicle.is_active.is_(True))
    if status_filter == 'inactivos': q = q.filter(Vehicle.is_active.is_(False))
    if search:
        term = f'%{search.strip()}%'
        q = q.join(Customer, Customer.id == Vehicle.customer_id).filter(or_(Vehicle.vin.ilike(term), Vehicle.plate.ilike(term), Vehicle.make.ilike(term), Vehicle.model.ilike(term), Customer.first_name.ilike(term), Customer.paternal_surname.ilike(term)))
    rows = q.order_by(Vehicle.created_at.desc()).all()
    workshops = {x.id:x for x in db.query(Workshop).all()}; customers = {x.id:x for x in db.query(Customer).all()}
    return [_vehicle_data(x, customers[x.customer_id], workshops[x.workshop_id], db) for x in rows if x.customer_id in customers and x.workshop_id in workshops]

@app.get('/api/vehicles/check-vin')
def check_vehicle_vin(vin:str, _:User=Depends(require_permission('vehicles:manage')), db:Session=Depends(get_db)):
    normalized = re.sub(r'[ -]', '', vin).upper()
    vehicle = db.query(Vehicle).filter(Vehicle.vin == normalized).first()
    return {"vin": normalized, "duplicate": bool(vehicle), "vehicle_id": vehicle.id if vehicle else None}

@app.get('/api/vehicles/{vehicle_id}')
def get_vehicle(vehicle_id:int, _:User=Depends(require_permission('vehicles:manage')), db:Session=Depends(get_db)):
    x = _vehicle_or_404(vehicle_id, db); customer = db.query(Customer).filter(Customer.id == x.customer_id).first(); workshop = db.query(Workshop).filter(Workshop.id == x.workshop_id).first()
    data = _vehicle_data(x, customer, workshop, db)
    data['owner'] = {
        "name": data["customer_name"], "primary_email": customer.primary_email, "secondary_email": customer.secondary_email,
        "primary_phone": customer.primary_phone, "secondary_phone": customer.secondary_phone,
        "address": ", ".join(filter(None, [customer.street_and_number, customer.neighborhood, customer.municipality, customer.state, f"CP {customer.postal_code}" if customer.postal_code else None]))
    }
    data['photos'] = [{"id": photo.id, "filename": photo.filename, "url": f"/api/vehicles/photos/{photo.id}"} for photo in db.query(VehiclePhoto).filter(VehiclePhoto.vehicle_id == x.id).all()]
    return data

@app.put('/api/vehicles/{vehicle_id}')
def update_vehicle(vehicle_id: int, payload: VehicleUpdateRequest, user: User = Depends(require_permission('vehicles:manage')), db: Session = Depends(get_db)):
    allowed_roles = {'administrador', 'recepcionista'}
    if not any(role.name.casefold() in allowed_roles for role in user.roles):
        raise HTTPException(403, 'Solo Administrador o Recepcionista puede actualizar vehículos.')
    vehicle = _vehicle_or_404(vehicle_id, db)
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(vehicle, field, value)
    vehicle.updated_by_id = user.id
    _audit(db, 'vehicle', vehicle.id, 'update', user.id)
    db.commit()
    db.refresh(vehicle)
    customer = db.query(Customer).filter(Customer.id == vehicle.customer_id).first()
    workshop = db.query(Workshop).filter(Workshop.id == vehicle.workshop_id).first()
    return _vehicle_data(vehicle, customer, workshop, db)

@app.patch('/api/vehicles/{vehicle_id}/status')
def set_vehicle_status(vehicle_id:int, active:bool, user:User=Depends(require_permission('vehicles:manage')), db:Session=Depends(get_db)):
    if not any(role.name.casefold() == 'administrador' for role in user.roles): raise HTTPException(403, 'Sólo Administrador puede desactivar vehículos.')
    x = _vehicle_or_404(vehicle_id, db); x.is_active = active; _audit(db, 'vehicle', x.id, 'activate' if active else 'deactivate', user.id); db.commit()
    return {"id":x.id, "is_active":x.is_active}

@app.post('/api/vehicles/{vehicle_id}/photos', status_code=201)
async def upload_vehicle_photos(vehicle_id:int, files:list[UploadFile] = File(...), user:User=Depends(require_permission('vehicles:manage')), db:Session=Depends(get_db)):
    vehicle = _vehicle_or_404(vehicle_id, db)
    if not vehicle.is_active: raise HTTPException(409, 'No se pueden agregar fotografías a un vehículo inactivo.')
    if not files: raise HTTPException(422, 'Selecciona al menos una fotografía.')
    for file in files:
        content = await file.read()
        detected = _image_type(content, file.content_type)
        if len(content) > 15 * 1024 * 1024: raise HTTPException(413, f'{file.filename or "Archivo"} supera 15 MB.')
        if not detected: raise HTTPException(422, f'{file.filename or "Archivo"} no es una imagen JPG, PNG o WebP válida.')
        db.add(VehiclePhoto(vehicle_id=vehicle.id, filename=(file.filename or 'vehiculo').strip()[:255], content_type=detected, content=content, created_by_id=user.id))
    db.flush(); _audit(db, 'vehicle', vehicle.id, 'add_photo', user.id); db.commit()
    return {"uploaded": len(files)}

@app.delete('/api/vehicles/{vehicle_id}/photos/{photo_id}', status_code=204)
def delete_vehicle_photo(vehicle_id: int, photo_id: int, user: User = Depends(require_permission('vehicles:manage')), db: Session = Depends(get_db)):
    vehicle = _vehicle_or_404(vehicle_id, db)
    photo = db.query(VehiclePhoto).filter(VehiclePhoto.id == photo_id, VehiclePhoto.vehicle_id == vehicle.id).first()
    if not photo:
        raise HTTPException(404, 'Fotografía no encontrada.')
    db.delete(photo)
    _audit(db, 'vehicle', vehicle.id, 'remove_photo', user.id)
    db.commit()

@app.get('/api/vehicles/photos/{photo_id}')
def vehicle_photo(photo_id:int, _:User=Depends(require_permission('vehicles:manage')), db:Session=Depends(get_db)):
    photo = db.query(VehiclePhoto).filter(VehiclePhoto.id == photo_id).first()
    if not photo: raise HTTPException(404, 'Fotografía no encontrada.')
    return Response(content=photo.content, media_type=photo.content_type, headers={"Cache-Control": "private, max-age=3600"})
