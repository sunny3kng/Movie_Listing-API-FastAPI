from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(50))
    password = Column(String(255), nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    user_role = relationship("UserRoleModel", backref="user")


class UserRoleModel(Base):
    __tablename__ = "user_roles"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"))
    role_id = Column(String(36), ForeignKey("roles.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class RoleModel(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True)
    slug = Column(String(50))
    name = Column(String(50))
    editable = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    user_role = relationship("UserRoleModel", backref="role")
    role_operation = relationship("RoleOperationModel", backref="role")


class RoleOperationModel(Base):
    __tablename__ = "role_operations"

    id = Column(String(36), primary_key=True)
    role_id = Column(String(36), ForeignKey("roles.id"))
    operation_id = Column(String(36), ForeignKey("operations.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class OperationModel(Base):
    __tablename__ = "operations"

    id = Column(String(36), primary_key=True)
    slug = Column(String(50))
    name = Column(String(50))
    order_index = Column(Integer)
    parent_id = Column(String(36), default="0")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    role_operation = relationship("RoleOperationModel", backref="operation")


class MovieModel(Base):
    __tablename__ = "movies"

    id = Column(String(36), primary_key=True)
    title = Column(String(80), nullable=False)
    description = Column(Text(), nullable=True)
    path = Column(String(80))
    year = Column(Integer)
    user_id = Column(String(36), ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    user = relationship("UserModel", backref="movies")


class MovieImageModel(Base):
    __tablename__ = "movie_images"

    id = Column(String(36), primary_key=True)
    name = Column(String(60))
    path = Column(String(80))
    is_thumbnail = Column(Boolean, default=False)
    movie_id = Column(String(36), ForeignKey("movies.id"))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    movie = relationship("MovieModel", backref="movie_images")


class MovieRatingModel(Base):
    __tablename__ = "movie_ratings"

    id = Column(String(36), primary_key=True)
    score = Column(Integer)
    text = Column(Text(), nullable=True)
    movie_id = Column(String(36), ForeignKey("movies.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    movie = relationship("MovieModel", backref="movie_ratings")
    user = relationship("UserModel", backref="movie_ratings")



class MovieCommentModel(Base):
    __tablename__ = "movie_comments"

    id = Column(String(36), primary_key=True)
    text = Column(Text(), nullable=True)
    parent_id = Column(String(36), default="0")
    movie_id = Column(String(36), ForeignKey("movies.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)

    movie = relationship("MovieModel", backref="movie_comments")
    user = relationship("UserModel", backref="movie_comments")
