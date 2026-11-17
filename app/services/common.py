from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError


def commit_or_409(db, detail):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail)
