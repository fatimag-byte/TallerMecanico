from datetime import datetime, timedelta, timezone
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from .config import get_settings
from .database import Base, engine, get_db
from .dependencies import get_current_user, require_permission
from .models import Permission, RefreshToken, Role, User
from .schemas import AuthResponse, ForgotPasswordRequest, LoginRequest, RefreshRequest, RegisterRequest, UserResponse
from .security import create_access_token, hash_password, hash_refresh_token, new_refresh_token, verify_password

app = FastAPI(title="Taller Mecánico API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def seed_roles(db: Session):
    permissions = {
        "users:read": "Consultar usuarios", "users:manage": "Administrar usuarios y roles",
        "workorders:read": "Consultar órdenes", "workorders:write": "Crear y editar órdenes",
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
    technician = db.query(Role).filter_by(name="tecnico").first()
    if not technician:
        technician = Role(name="tecnico", description="Operación del taller")
        technician.permissions = db.query(Permission).filter(Permission.code.in_(["workorders:read", "workorders:write"])).all()
        db.add(technician)
    db.commit()


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_roles(db)
    finally:
        db.close()


def user_response(user: User) -> UserResponse:
    roles = [role.name for role in user.roles]
    permissions = sorted({permission.code for role in user.roles for permission in role.permissions})
    return UserResponse(id=user.id, name=user.name, paternal_surname=user.paternal_surname, maternal_surname=user.maternal_surname, phone=user.phone, email=user.email, roles=roles, permissions=permissions)


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


@app.get("/api/auth/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user_response(user)


@app.get("/api/users", response_model=list[UserResponse])
def list_users(_: User = Depends(require_permission("users:read")), db: Session = Depends(get_db)):
    users = db.query(User).options(joinedload(User.roles).joinedload(Role.permissions)).order_by(User.created_at.desc()).all()
    return [user_response(user) for user in users]
