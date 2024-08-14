
from datetime import datetime
from genericpath import exists
from fastapi import APIRouter, BackgroundTasks, File, Form, Header, Response, UploadFile
from fastapi import HTTPException, status, Depends, Path, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from routers.admin.v1 import schemas
from dependencies import get_db
from routers.admin.v1.crud import comments, movies, operations, ratings, roles, users

router = APIRouter()


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=schemas.UserLoginResponse,
    tags=["Authentication"],
)
def sign_in(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = users.sign_in(db, user)
    return db_user


# Users

@router.post(
    "/sign-up",
    response_model=schemas.UserLoginResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
)
def sign_up(
    user: schemas.UserSignUp,
    db: Session = Depends(get_db)
):
    data = users.sign_up(db, user=user)
    return data

@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    tags=["Users"]
)
def change_password(
    user: schemas.ChangePassword,
    token: str = Header(None),
    db: Session = Depends(get_db),
):
    users.change_password(db, user=user, token=token)
    return Response(status_code=status.HTTP_200_OK)


@router.get(
    "/profile",
    status_code=status.HTTP_200_OK,
    response_model=schemas.User,
    tags=["Users"],
)
def get_profile(token: str = Header(None), db: Session = Depends(get_db)):
    data = users.get_profile(db, token=token)
    return data


@router.put(
    "/profile",
    status_code=status.HTTP_200_OK,
    response_model=schemas.User,
    tags=["Users"],
)
def update_profile(
    user: schemas.UserUpdate,
    token: str = Header(None),
    db: Session = Depends(get_db),
):
    data = users.update_profile(db, token=token, user=user)
    return data



@router.get(
    "/users",
    response_model=schemas.AdminUserList,
    tags=["Admin - Users"]
)
def get_users(
    token: str = Header(None),
    start: int = 0,
    limit: int = 10,
    sort_by: str = Query("all", min_length=3, max_length=10),
    order: str = Query("all", min_length=3, max_length=4),
    search: str = Query("all", min_length=1, max_length=50),
    db: Session = Depends(get_db),
):
    db_user = users.verify_token(db, token=token)
    operations.verify_user_operation(db, user_id=db_user.id, operation="List Users")
    data = users.get_users(
        db, start=start, limit=limit, sort_by=sort_by, order=order, search=search
    )
    return data


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    tags=["Admin - Users"]
)
def add_user(
    user: schemas.UserAdd,
    token: str = Header(None),
    db: Session = Depends(get_db)
):
    db_user = users.verify_token(db, token=token)
    operations.verify_user_operation(db, db_user.id, "Add User")
    user_id = users.add_user(db, user=user)
    return user_id


@router.get(
    "/users/{user_id}",
    response_model=schemas.User,
    tags=["Admin - Users"]
)
def get_my_profile(
    token: str = Header(None),
    user_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db)
):
    users.verify_token(db, token=token)
    db_user = users.get_user_profile(db, user_id=user_id)
    return db_user


@router.put(
    "/users/{user_id}",
    response_model=schemas.User,
    tags=["Admin - Users"]
)
def update_profile(
    user: schemas.UserUpdate,
    token: str = Header(None),
    user_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db),
):
    users.verify_token(db, token=token)
    db_user = users.update_user_profile(db, user=user, user_id=user_id)
    return db_user


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    tags=["Admin - Users"]
)
def delete_user(
    token: str = Header(None),
    user_id: str = Path(..., title="User ID", min_length=36, max_length=36),
    db: Session = Depends(get_db),
):
    users.verify_token(db, token=token)
    users.delete_user(db, user_id=user_id)
    return Response(status_code=status.HTTP_200_OK)

# End Users


# Operations
@router.get("/operations/verify", status_code=status.HTTP_200_OK, tags=["Operations"])
def check_user_operation(
    token: str = Header(None),
    operation: str = Query("all", min_length=3, max_length=50),
    db: Session = Depends(get_db),
):
    db_user = users.verify_token(db, token=token)
    operations.verify_user_operation(db, user_id=db_user.id, operation=operation)
    return


@router.get("/operations/all", tags=["Operations"])
def get_all_operations(token: str = Header(None), db: Session = Depends(get_db)):
    users.verify_token(db, token=token)
    data = operations.get_all_operations(db)
    return data


# End Operations


# Roles
@router.get("/roles", response_model=schemas.RoleList, tags=["Roles"])
def get_roles(
    token: str = Header(None),
    start: int = 0,
    limit: int = 10,
    sort_by: str = Query("all", min_length=3, max_length=50),
    order: str = Query("all", min_length=3, max_length=4),
    search: str = Query("all", min_length=1, max_length=50),
    db: Session = Depends(get_db),
):
    db_user = users.verify_token(db, token=token)
    operations.verify_user_operation(db, user_id=db_user.id, operation="List Roles")
    data = roles.get_roles(
        db, start=start, limit=limit, sort_by=sort_by, order=order, search=search
    )
    return data


@router.get("/roles/all", response_model=List[schemas.Role], tags=["Roles"])
def get_all_roles(token: str = Header(None), db: Session = Depends(get_db)):
    users.verify_token(db, token=token)
    data = roles.get_all_roles(db)
    return data


@router.post("/roles", status_code=status.HTTP_201_CREATED, tags=["Roles"])
def add_role(
    role: schemas.RoleAdd, token: str = Header(None), db: Session = Depends(get_db)
):
    db_user = users.verify_token(db, token=token)
    operations.verify_user_operation(db, user_id=db_user.id, operation="Add Role")
    role = roles.add_role(db, role=role)
    return


@router.get("/roles/{role_id}", response_model=schemas.RoleDetails, tags=["Roles"])
def get_role(
    role_id: str = Path(..., title="Role ID", min_length=36, max_length=36),
    token: str = Header(None),
    db: Session = Depends(get_db),
):
    db_user = users.verify_token(db, token=token)
    operations.verify_user_operation(db, user_id=db_user.id, operation="Update Role")
    role = roles.get_role_details(db, role_id=role_id)
    return role


@router.put("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Roles"])
def update_role(
    role: schemas.RoleAdd,
    token: str = Header(None),
    role_id: str = Path(..., title="Role ID", min_length=36, max_length=36),
    db: Session = Depends(get_db),
):
    db_user = users.verify_token(db, token=token)
    operations.verify_user_operation(db, user_id=db_user.id, operation="Update Role")
    role = roles.update_role(db, role_id=role_id, role=role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Roles"]
)
def delete_role(
    token: str = Header(None),
    role_id: str = Path(..., title="Role ID", min_length=36, max_length=36),
    db: Session = Depends(get_db),
):
    db_user = users.verify_token(db, token=token)
    operations.verify_user_operation(db, user_id=db_user.id, operation="Delete Role")
    roles.delete_role(db, role_id=role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# End Roles


@router.get(
    "/movies",
    response_model=schemas.MovieList,
    tags=["Movies"]
)
def get_movies_list(
    start: int = 0,
    limit: int = 10,
    search: str = Query("all", min_length=3, max_length=50),
    sort_by: str = Query("all", min_length=3, max_length=20),
    order: str = Query("all", min_length=3, max_length=5),
    user_id: str = Query("all", min_length=3, max_length=36),
    db: Session = Depends(get_db),
):
    data = movies.get_movie_list(db, start, limit, search, sort_by, order, user_id)
    return data


@router.post(
    "/movies/details",
    response_model=schemas.Movie,
    tags=["Movies"]
)
def add_movie(
    movie: schemas.MovieAdd,
    db: Session = Depends(get_db),
    token: str = Header(None)
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "add movies")
    data = movies.add_movie_detail(db=db, user_id=db_user.id, movie=movie)
    return data


@router.post(
    "/movies/{movie_id}/upload",
    status_code=status.HTTP_200_OK,
    tags=["Movies"]
)
def upload_movie(
    background_tasks: BackgroundTasks,
    movie_id: str = Path(..., min_length=36, max_length=36),
    file: UploadFile = File(...),
    token: str = Header(None),
    db: Session = Depends(get_db),
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "add movies")
    movies.get_movie(db=db, movie_id=movie_id)
    background_tasks.add_task(movies.add_movie, file, movie_id)
    return Response(status_code=status.HTTP_200_OK)

@router.post(
    "/movies/{movie_id}/images",
    status_code=status.HTTP_200_OK,
    tags=["Movies"]
)
def add_movie_image(
    movie_id: str = Path(..., min_length=36, max_length=36),
    is_thumbnail: bool = Form(False),
    file: UploadFile = File(...),
    token: str = Header(None),
    db: Session = Depends(get_db),
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "add movies")    
    movies.add_movie_image(db, file, movie_id, is_thumbnail)
    return Response(status_code=status.HTTP_200_OK)


@router.get(
    "/movies/{movie_id}",
    response_model=schemas.Movie,
    tags=["Movies"]
)
def get_movie(
    movie_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db)
):
    data = movies.get_movie(db, movie_id)
    return data


@router.get(
    "/movies/{movie_id}/downloads",
    response_model=schemas.MovieDownload,
    tags=["Movies"]
)
def download_movie(
    movie_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db)
):
    data = movies.download_movie(db, movie_id)
    return data


@router.put(
    "/movies/{movie_id}",
    response_model=schemas.Movie,
    tags=["Movies"]
)
def update_movie_details(
    movie: schemas.MovieAdd,
    movie_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db),
    token: str = Header(None)
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "update movies")
    data = movies.update_movie_details(db, movie_id, movie)
    return data


@router.put(
    "/movies/{movie_id}/images/{image_id}",
    response_model=schemas.MovieImage,
    tags=["Movies"]
)
def update_movie_image(
    movie_id: str = Path(..., min_length=36, max_length=36),
    image_id: str = Path(..., min_length=36, max_length=36),
    is_thumbnail: bool = Query(False),
    db: Session = Depends(get_db),
    token: str = Header(None)
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "update movies")
    data = movies.update_movie_image(db, movie_id, image_id, is_thumbnail)
    return data


@router.delete(
    "/movies/{movie_id}",
    status_code=status.HTTP_200_OK,
    tags=["Movies"]
)
def delete_movie(
    movie_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db),
    token: str = Header(None)
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "delete movies") 
    movies.delete_movie(db, movie_id)
    return Response(status_code=status.HTTP_200_OK)


@router.delete(
    "/movies/{movie_id}/images/{image_id}",
    status_code=status.HTTP_200_OK,
    tags=["Movies"]
)
def delete_movie_image(
    movie_id: str = Path(..., min_length=36, max_length=36),
    image_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db),
    token: str = Header(None)
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "delete movies") 
    movies.delete_movie_images(db, movie_id, image_id)
    return Response(status_code=status.HTTP_200_OK)


@router.get(
    "/movies/comments",
    response_model=schemas.CommentList,
    tags=["Movies"]
)
def get_comment_list(
    start: int = 0,
    limit: int = 10,
    search: str = Query("all", min_length=3, max_length=30),
    sort_by: str = Query("all", min_length=3, max_length=30),
    order: str = Query("all", min_length=3, max_length=4),
    movie_id: str = Query("all", min_length=3, max_length=36),
    db: Session = Depends(get_db)
):
    data = comments.get_comment_list(
        db=db,
        start=start,
        limit=limit,
        search=search,
        sort_by=sort_by,
        order=order,
        movie_id=movie_id
    )
    return data


@router.post(
    "/movies/comments",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.Comment,
    tags=["Movies"]
)
def add_comment(
    comment: schemas.CommentAdd,
    db: Session = Depends(get_db),
    token: str = Header(None)
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "add comments")
    data = comments.add_comment(db, comment, db_user.id)
    return data


@router.get(
    "/movies/{movie_id}/comments/all",
    response_model=schemas.MovieComment,
    tags=["Movies"]
)
def get_all_comments(
    db: Session = Depends(get_db),
    movie_id: str = Path(..., min_length=36, max_length=36),
):
    data = comments.get_all_comments(db=db, movie_id=movie_id)
    return data


@router.get(
    "/movies/{movie_id}/comments/{comment_id}",
    response_model=schemas.Comment,
    tags=["Movies"]
)
def get_comment(
    movie_id: str = Path(..., min_length=36, max_length=36),
    comment_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db)
):
    data = comments.get_comment(db=db, movie_id=movie_id, comment_id=comment_id)
    return data


@router.put(
    "/movies/{movie_id}/comments/{comment_id}",
    response_model=schemas.Comment,
    tags=["Movies"]
)
def update_comment(
    comment: schemas.CommentUpdate,
    movie_id: str = Path(..., min_length=36, max_length=36),
    comment_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db),
    token: str = Header(None)
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "update comments")
    data = comments.update_comment(db=db, movie_id=movie_id, comment_id=comment_id, comment=comment)
    return data


@router.delete(
    "/movies/{movie_id}/comments/{comment_id}",
    response_model=schemas.Comment,
    tags=["Movies"]
)
def delete_comment(
    movie_id: str = Path(..., min_length=36, max_length=36),
    comment_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db),
    token: str = Header(None)
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "delete comments")
    comments.delete_comment(db=db, movie_id=movie_id, comment_id=comment_id)
    return Response(status_code=status.HTTP_200_OK)


@router.get(
    "/movies/ratings",
    response_model=schemas.RatingList,
    tags=["Movies"]
)
def get_rating_list(
    start: int = 0,
    limit: int = 10,
    search: str = Query("all", min_length=3, max_length=40),
    sort_by: str = Query("all", min_length=3, max_length=40),
    order: str = Query("all", min_length=3, max_length=4),
    movie_id: str = Query("all", min_length=3, max_length=36),
    db: Session = Depends(get_db)
):
    data = ratings.get_rating_list(
        db=db,
        start=start,
        limit=limit,
        search=search,
        sort_by=sort_by,
        order=order,
        movie_id=movie_id
    )
    return data


@router.post(
    "/movies/ratings",
    response_model=schemas.Rating,
    status_code=status.HTTP_201_CREATED,
    tags=["Movies"]
)
def add_rating(
    rating: schemas.RatingAdd,
    token: str = Header(None),
    db: Session = Depends(get_db)
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "add ratings")
    data = ratings.add_rating(db, db_user.id, rating)
    return data


@router.get(
    "/movies/{movie_id}/ratings/all",
    response_model=schemas.MovieRatings,
    tags=["Movies"]
)
def get_all_ratings(
    movie_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db)
):
    data = ratings.get_all_ratings(db, movie_id)
    return data


@router.get(
    "/movies/{movie_id}/ratings/{rating_id}",
    response_model=schemas.Rating,
    tags=["Movies"]
)
def get_rating(
    movie_id: str = Path(..., min_length=36, max_length=36),
    rating_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db)
):
    data = ratings.get_rating(db, movie_id, rating_id)
    return data


@router.put(
    "/movies/{movie_id}/ratings/{rating_id}",
    response_model=schemas.Rating,
    tags=["Movies"]
)
def update_rating(
    rating: schemas.RatingUpdate,
    movie_id: str = Path(..., min_length=36, max_length=36),
    rating_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db),
    token: str = Header(None)
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "update ratings")
    data = ratings.update_rating(db=db, movie_id=movie_id, rating_id=rating_id, rating=rating)
    return data


@router.delete(
    "/movies/{movie_id}/ratings/{rating_id}",
    response_model=schemas.Rating,
    tags=["Movies"]
)
def delete_rating(
    movie_id: str = Path(..., min_length=36, max_length=36),
    rating_id: str = Path(..., min_length=36, max_length=36),
    db: Session = Depends(get_db),
    token: str = Header(None)
):
    db_user = users.verify_token(db, token)
    operations.verify_user_operation(db, db_user.id, "delete ratings")
    ratings.delete_rating(db=db, movie_id=movie_id, rating_id=rating_id)
    return Response(status_code=status.HTTP_200_OK)


@router.get(
    "/files",
    tags=["Files"],
)
async def get_files(
    f: str = Query(..., max_length=100),
):
    if f.startswith("uploads/") and exists(f):
        data = FileResponse(f)
    else:
        data = FileResponse("uploads/default.png")
    return data
