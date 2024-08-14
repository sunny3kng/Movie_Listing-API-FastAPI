from typing import List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, Field, validator
from email_validator import EmailNotValidError, validate_email

from datetime import datetime

# from models import GenderEnum, StatusEnum


# Admin Users


class UserLoginResponse(BaseModel):
    id: str = Field(min_length=36, max_length=36)
    first_name: str = Field(min_length=3, max_length=50)
    last_name: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=50)
    token: str

    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email: str = Field(min_length=5, max_length=50)
    password: str = Field(min_length=3, max_length=50)

    @validator("email")
    def valid_email(cls, email):
        try:
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
            )


class UserSignUp(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=60)
    last_name : str = Field(..., min_length=2, max_length=60)
    email: str = Field(min_length=5, max_length=50)
    password: str = Field(min_length=3, max_length=50)

    @validator("email")
    def valid_email(cls, email):
        try:
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
            )
        


class ChangePassword(BaseModel):
    old_password: str = Field(min_length=3, max_length=50)
    new_password: str = Field(min_length=3, max_length=50)



class UserAdd(BaseModel):
    first_name: str = Field(min_length=3, max_length=50)
    last_name: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=50)
    password: str = Field(min_length=5, max_length=50)
    role: str = Field(min_length=36, max_length=36)

    @validator("email")
    def valid_email(cls, email):
        try:
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
            )
    

class UserUpdate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=60)
    last_name : str = Field(..., min_length=2, max_length=60)


class User(BaseModel):
    id: str
    first_name: str
    last_name: str
    email:str

    class Config:
        orm_mode = True


class Role(BaseModel):
    id: str
    name: str
    editable: bool

    class Config:
        orm_mode = True


class RoleList(BaseModel):
    count: int
    list: List[Role]

    class Config:
        orm_mode = True


class RoleAdd(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    operations: List[str] = Field(description="Operation Id")

    @validator("operations")
    def valid_operations(cls, operations):
        if len(operations) > 0:
            return operations
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Ensure operations has at least 1 operation id.",
            )


class RoleDetails(BaseModel):
    id: str
    name: str
    operations: List[str] = Field(description="Operation Id")


class AdminUser(BaseModel):
    id: str = Field(min_length=36, max_length=36)
    first_name: str = Field(min_length=3, max_length=50)
    last_name: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=50)
    role: Role

    class Config:
        orm_mode = True


class AdminUserList(BaseModel):
    count: int
    list: List[AdminUser]

    class Config:
        orm_mode = True


class AdminUserUpdate(BaseModel):
    first_name: str = Field(min_length=3, max_length=50)
    last_name: str = Field(min_length=3, max_length=50)
    role_id: str = Field(min_length=36, max_length=36, description="Role Id")


class MovieImage(BaseModel):
    id: str
    name: str
    path: str
    is_thumbnail: bool
    movie_id: str

    class Config:
        orm_mode = True


class MovieAdd(BaseModel):
    title: str = Field(..., min_length=2, max_length=70)
    description: str
    year: int


class Movie(BaseModel):
    id: str
    title: str
    description: str
    year: int
    user: User
    images: List[MovieImage] = []

    class Config:
        orm_mode = True


class MovieResponse(BaseModel):
    id: str
    title: str
    description: str
    year: int
    user: User
    thumbnail: Optional[MovieImage] = None

    class Config:
        orm_mode = True


class MovieDownload(BaseModel):
    id: str
    title: str
    description: str
    path: str
    year: str

    class Config:
        orm_mode = True


class MovieList(BaseModel):
    count: int
    list: List[MovieResponse] = []

    class Config:
        orm_mode = True


class CommentAdd(BaseModel):
    text: str = Field(..., min_length=2)
    movie_id: str = Field(..., min_length=36, max_length=36)
    parent_id: str = Field("0", max_length=36)


class Reply(BaseModel):
    id: str
    text: str
    created_at: datetime
    user: User

    class Config:
        orm_mode = True


class Comment(BaseModel):
    id: str
    text: str
    created_at: datetime
    user: User
    replies: List[Reply] = []

    class Config:
        orm_mode = True


class MovieComment(Movie):
    comments: List[Comment] = []

    class Config:
        orm_mode = True


class CommentList(BaseModel):
    count: int
    list: List[Comment] = []

    class Config:
        orm_mode = True


class CommentUpdate(BaseModel):
    text: str = Field(..., min_length=2)



class RatingAdd(BaseModel):
    score: int
    text: Optional[str] = None
    movie_id: str


class Rating(BaseModel):
    id: str
    score: int
    text: Optional[str] = None
    movie: Movie
    user: User

    class Config:
        orm_mode = True


class MovieRatings(Movie):
    ratings: List[Rating] = []

    class Config:
        orm_mode = True


class RatingList(BaseModel):
    count: int
    list: List[Rating] = []

    class Config:
        orm_mode = True


class RatingUpdate(BaseModel):
    score: int
    text: Optional[str] = None
