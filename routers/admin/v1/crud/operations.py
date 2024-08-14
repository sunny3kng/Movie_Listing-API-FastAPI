from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from libs.utils import object_as_dict
from models import OperationModel, RoleModel, RoleOperationModel, UserRoleModel

from .users import is_super_admin


def get_operation(db: Session, operation_id: str):
    db_operation = (
        db.query(OperationModel).filter(OperationModel.id == operation_id).first()
    )
    return db_operation

def get_operation_by_name(db: Session, name: str):
    db_operation = (
        db.query(OperationModel).filter(OperationModel.name == name).first()
    )
    return db_operation


def get_operation_by_slug(db: Session, operation_slug: str, parent_id: str):
    db_operation = (
        db.query(OperationModel)
        .filter(
            OperationModel.slug == operation_slug,
            OperationModel.parent_id == 0
        )
        .first()
    )
    return db_operation

def get_operations(
    db: Session, start: int, limit: int, sort_by: str, order: str, search: str
):
    query = db.query(OperationModel)

    if search != "all":
        text = f"""%{search}%"""
        query = query.filter(OperationModel.name.like(text))

    if sort_by == "name":
        if order == "desc":
            query = query.order_by(OperationModel.name.desc())
        else:
            query = query.order_by(OperationModel.name)
    else:
        query = query.order_by(OperationModel.updated_at.desc())

    results = query.offset(start).limit(limit).all()
    count = query.count()
    data = {"count": count, "list": results}
    return data


def get_all_operations(db: Session):
    headings = (
        db.query(OperationModel)
        .filter(OperationModel.parent_id == "0")
        .order_by(OperationModel.order_index)
        .all()
    )
    data = []
    for heading in headings:
        _heading = object_as_dict(heading)
        operations = (
            db.query(OperationModel)
            .filter(OperationModel.parent_id == heading.id)
            .order_by(OperationModel.order_index)
            .all()
        )
        _heading["operations"] = operations
        data.append(_heading)
    return data


def verify_user_operation(db: Session, user_id: str, operation: str):
    super_admin = is_super_admin(db, user_id=user_id)
    if not super_admin:
        db_operations = (
            db.query(UserRoleModel)
            .filter(UserRoleModel.user_id == user_id)
            .join(RoleModel)
            .join(RoleOperationModel)
            .join(OperationModel)
            .filter(OperationModel.slug == operation)
            .first()
        )
        if db_operations is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You don't have permission.",
            )
    return


def verify_user_multiple_operation(db: Session, user_id: str, operation: str):
    super_admin = is_super_admin(db, user_id=user_id)
    if not super_admin:
        db_operations = []
        for operations in operation:

            db_operation = (
                db.query(UserRoleModel)
                .filter(UserRoleModel.user_id == user_id)
                .join(RoleModel)
                .join(RoleOperationModel)
                .join(OperationModel)
                .filter(OperationModel.slug == operations)
                .first()
            )
            db_operations.append(db_operation)

        if all(element is None for element in db_operations):
            raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="You don't have permission.",
            )
    return


def get_user_operation(db: Session, user_id: str):
    super_admin = is_super_admin(db, user_id=user_id)
    headings = (
        db.query(OperationModel)
        .filter(OperationModel.parent_id == "0")
        .order_by(OperationModel.order_index)
        .all()
    )
    all_operations = []
    allowed_menu = []
    for heading in headings:
        if super_admin:
            rows = (
                db.query(OperationModel)
                .filter(OperationModel.parent_id == heading.id)
                .order_by(OperationModel.order_index)
                .all()
            )
        else:
            rows = (
                db.query(OperationModel)
                .filter(OperationModel.parent_id == heading.id)
                .order_by(OperationModel.order_index)
                .join(RoleOperationModel)
                .join(RoleModel)
                .join(UserRoleModel)
                .filter(UserRoleModel.user_id == user_id)
                .all()
            )
        operations = []
        for row in rows:
            operations.append(row.slug)
        all_operations.extend(operations)
        if len(operations) == 0:
            continue
        allowed_menu.append(heading.slug)
    data = {"operations": all_operations, "menu": allowed_menu}
    return data
