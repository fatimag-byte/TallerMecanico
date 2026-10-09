from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, joinedload
from .database import get_db
from .models import Role, User
from .security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Debes iniciar sesión para continuar.")
    try:
        user_id = decode_access_token(credentials.credentials)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error))
    user = db.query(User).options(joinedload(User.roles).joinedload(Role.permissions)).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="La cuenta no existe o está inactiva.")
    return user


def require_permission(permission: str):
    def validator(user: User = Depends(get_current_user)) -> User:
        permissions = {item.code for role in user.roles for item in role.permissions}
        if permission not in permissions:
            raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta acción.")
        return user
    return validator
