import argparse
import sys

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import User
from app.models.user import ROLE_ADMIN, ROLE_USER


def set_role(username, role):
    with SessionLocal() as db:
        user = db.scalar(select(User).where(func.lower(User.username) == username.lower()))
        if user is None:
            print(f"User '{username}' not found", file=sys.stderr)
            return 1
        user.role = role
        db.commit()
        print(f"User '{user.username}' is now {role}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Grant or revoke the admin role for an existing user")
    parser.add_argument("username")
    parser.add_argument("--revoke", action="store_true", help="make the user a regular user again")
    args = parser.parse_args()
    return set_role(args.username, ROLE_USER if args.revoke else ROLE_ADMIN)


if __name__ == "__main__":
    sys.exit(main())
