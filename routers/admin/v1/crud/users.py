import json
import bcrypt
import traceback

from uuid import uuid4

from fastapi import HTTPException, status
from jwcrypto import jwk, jwt
from sqlalchemy import or_
from sqlalchemy.orm import Session

from config import config
from libs.utils import generate_id, now, object_as_dict
from models import RoleModel, UserRoleModel, UserModel
from routers.admin.v1.schemas import (
    AdminUserUpdate,
    ChangePassword,
    UserAdd,
    UserLogin,
    UserSignUp,
    UserUpdate,
)


def get_role_by_name(db: Session, name: str):
    return (
        db.query(RoleModel)
        .filter(RoleModel.name == name, RoleModel.is_deleted == False)
        .first()
    )


def get_token(user_id, email):
    claims = {"id": user_id, "email": email, "time": str(now())}

    # Create a signed token with the generated key
    key = jwk.JWK(**config["jwt_key"])
    Token = jwt.JWT(header={"alg": "HS256"}, claims=claims)
    Token.make_signed_token(key)

    # Further encrypt the token with the same key
    encrypted_token = jwt.JWT(
        header={"alg": "A256KW", "enc": "A256CBC-HS512"}, claims=Token.serialize()
    )
    encrypted_token.make_encrypted_token(key)
    token = encrypted_token.serialize()
    return token


def verify_token(db: Session, token: str):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    else:
        try:
            key = jwk.JWK(**config["jwt_key"])
            ET = jwt.JWT(key=key, jwt=token)
            ST = jwt.JWT(key=key, jwt=ET.claims)
            claims = ST.claims
            claims = json.loads(claims)
            db_user = get_user_by_id(db, id=claims["id"])
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return db_user


def _create_password(password):
    password = bytes(password, "utf-8")
    password = bcrypt.hashpw(password, config["salt"])
    password = password.decode("utf-8")
    return password


def get_user_by_id(db: Session, id: str):
    return db.query(UserModel).filter(UserModel.id == id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(UserModel).filter(UserModel.email == email).first()


def sign_up(db: Session, user: UserSignUp):
    id = generate_id()
    user = user.dict()
    email = user["email"]
    db_user = get_user_by_email(db, email=email)
    password = user["password"]
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exist."
        )
    user["password"] = _create_password(password)
    db_user = UserModel(id=id, **user)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    role = get_role_by_name(db=db, name="normal user")
    update_user_role(db, user_id=id, role_id=role.id)
    user["id"] = id
    user["token"] = get_token(id, email)
    return user


def sign_in(db: Session, user: UserLogin):
    db_user = get_user_by_email(db, email=user.email)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    hashed = db_user.password
    hashed = bytes(hashed, "utf-8")
    password = bytes(user.password, "utf-8")
    if not bcrypt.checkpw(password, hashed):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = object_as_dict(db_user)
    user["token"] = get_token(db_user.id, db_user.email)
    return user


def change_password(db: Session, user: ChangePassword, token: str):
    db_user = verify_token(db, token=token)
    try:
        hashed = bytes(db_user.password, "utf-8")
        password = bytes(user.old_password, "utf-8")
        result = bcrypt.checkpw(password, hashed)
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect old password"
        )
    else:
        password = _create_password(user.new_password)
        db_user.password = password
        db_user.updated_at = now()
        db.commit()


def add_user(db: Session, user: UserSignUp):
    id = generate_id()
    user = user.dict()
    email = user["email"]
    db_user = get_user_by_email(db, email=email)
    password = user["password"]
    role_id = user["role"]
    if not db_user:
        user["password"] = _create_password(password)
        del user["role"]
        db_user = UserModel(id=id, **user)
        db.add(db_user)
    db.commit()
    db.refresh(db_user)
    update_user_role(db, user_id=id, role_id=role_id)
    return user


def get_users(
    db: Session, start: int, limit: int, sort_by: str, order: str, search: str
):
    query = db.query(UserModel).filter(UserModel.is_deleted == False)

    if search != "all":
        text = f"""%{search}%"""
        query = query.filter(
            or_(
                UserModel.first_name.like(text),
                UserModel.last_name.like(text),
                UserModel.email.like(text),
            )
        )
        count = query.filter(
            or_(
                UserModel.first_name.like(text),
                UserModel.last_name.like(text),
                UserModel.email.like(text),
            )
        ).count()
    else:
        count = db.query(UserModel).count()

    if sort_by == "first_name":
        if order == "desc":
            query = query.order_by(UserModel.first_name.desc())
        else:
            query = query.order_by(UserModel.first_name)
    elif sort_by == "last_name":
        if order == "desc":
            query = query.order_by(UserModel.last_name.desc())
        else:
            query = query.order_by(UserModel.last_name)
    elif sort_by == "email":
        if order == "desc":
            query = query.order_by(UserModel.email.desc())
        else:
            query = query.order_by(UserModel.email)
    else:
        query = query.order_by(UserModel.created_at.desc())

    results = query.offset(start).limit(limit).all()
    users = []
    for user in results:
        user_role = get_user_role(db, user.id)
        _user = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user_role.role,
        }
        users.append(_user)
    data = {"count": count, "list": users}
    return data


def get_user_role(db: Session, user_id: str):
    role = db.query(UserRoleModel).filter(UserRoleModel.user_id == user_id).first()
    return role


def update_user_role(db: Session, user_id: str, role_id: str):
    db.query(UserRoleModel).filter(UserRoleModel.user_id == user_id).delete()
    id = str(uuid4())
    db_user_role = UserRoleModel(id=id, user_id=user_id, role_id=role_id)
    db.add(db_user_role)
    db.commit()
    return


def is_super_admin(db: Session, user_id: str):
    db_user_role = get_user_role(db, user_id=user_id)
    role = db_user_role.role
    status = True if role.slug == "Super Admin" else False
    return status


def get_user_profile(db: Session, user_id: str):
    db_user = get_user_by_id(db, id=user_id)
    user = object_as_dict(db_user)
    user["role"] = db_user.user_role[0].role
    return user


def get_profile(db: Session, token: str):
    db_user = verify_token(db, token=token)
    return db_user


def update_profile(db: Session, token: str, user: UserUpdate):
    db_user = verify_token(db, token=token)
    db_user.first_name = user.first_name
    db_user.last_name = user.last_name
    db_user.updated_at = now()
    db.commit()
    return db_user


def update_user_profile(db: Session, user_id: str, user: AdminUserUpdate):
    db_user = get_user_by_id(db, id=user_id)
    db_user.first_name = user.first_name
    db_user.last_name = user.last_name
    db.commit()
    db.refresh(db_user)
    if db_user.user_role[0].role.id != user.role_id:
        update_user_role(db, user_id=user_id, role_id=user.role_id)
    db_user = get_user_profile(db, user_id=user_id)
    return db_user


def delete_user(db: Session, user_id: str):
    db_user = get_user_by_id(db, id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    db_user.is_deleted = True
    db.commit()
    return
