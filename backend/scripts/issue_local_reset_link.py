"""Creates a one-time local recovery link and opens it in the user's browser.

Use only for local development when no mail provider is configured. The secret
is never printed or stored in plain text.
"""

import argparse
import webbrowser
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models import PasswordResetToken, User
from app.security import hash_refresh_token, new_refresh_token


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email.lower(), User.is_active.is_(True)).first()
        if not user:
            raise SystemExit("No se encontró una cuenta activa para el correo indicado.")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)).update({PasswordResetToken.used_at: now})
        token = new_refresh_token()
        db.add(PasswordResetToken(user_id=user.id, token_hash=hash_refresh_token(token), expires_at=now + timedelta(minutes=15)))
        db.commit()
        webbrowser.open_new_tab(f"http://localhost:5173/restablecer?token={token}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
