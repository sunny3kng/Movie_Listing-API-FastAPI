from typing import List
from fastapi import UploadFile, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import SessionLocal
from libs.utils import generate_id, now, remove_file, save_file
from models import MovieImageModel, MovieModel
from routers.admin.v1.schemas import MovieAdd




def get_movie_by_id(db: Session, movie_id: str):
    return db.query(MovieModel).filter(MovieModel.id == movie_id, MovieModel.is_deleted == False).first()


def get_movie_images(db: Session, movie_id: str):
    db_images = db.query(MovieImageModel).filter(MovieImageModel.movie_id == movie_id, MovieImageModel.is_deleted == False).all()
    return db_images

def get_movie_thumbnail(db: Session, movie_id: str):
    db_image = db.query(MovieImageModel).filter(MovieImageModel.movie_id == movie_id, MovieImageModel.is_deleted == False, MovieImageModel.is_thumbnail == True).first()
    return db_image


def get_movie_image_by_id(db: Session, movie_id: str, image_id: str):
    db_image = (
        db.query(MovieImageModel)
        .filter(
            MovieImageModel.movie_id == movie_id,
            MovieImageModel.id == image_id
        )
        .first()
    )
    return db_image


def get_movie_list(
    db: Session,
    start: int,
    limit: int,
    search: str,
    sort_by: str,
    order: str,
    user_id: str
):
    query = db.query(MovieModel).filter(MovieModel.is_deleted == False)

    if user_id != "all":
        query = query.filter(MovieModel.user_id == user_id)
    
    if search != "all":
        text = f"""%{search}%"""
        query = query.filter(
            or_(
                MovieModel.title.like(text),
                MovieModel.description.like(text),
                MovieModel.year.like(text)
            )
        )
    
    if sort_by == "title":
        if order == "desc":
            query = query.order_by(MovieModel.title.desc())
        else:
            query = query.order_by(MovieModel.title)
    elif sort_by == "year":
        if order == "desc":
            query = query.order_by(MovieModel.year.desc())
        else:
            query = query.order_by(MovieModel.year)
    if sort_by == "created_at":
        if order == "desc":
            query = query.order_by(MovieModel.created_at.desc())
        else:
            query = query.order_by(MovieModel.created_at)
    else:
        query = query.order_by(MovieModel.created_at.desc())
    
    count = query.count()
    results = query.offset(start).limit(limit).all()
    for result in results:
        result.thumbnail = get_movie_thumbnail(db, result.id)

    data = {"count": count, "list": results}
    return data


def add_movie(file: UploadFile, movie_id: str):
    db = SessionLocal()
    db_movie = get_movie_by_id(db, movie_id)
    if db_movie.path:
        remove_file(db_movie.path)
    try:
        extention = ".mkv" if file.content_type == "video/x-matroska" else f".{file.content_type.split('/')[1]}"
        path = "uploads/movies/" + generate_id() + extention
        save_file(file, path)
    except Exception as e:
        print(e)
        return

    db_movie.path = path
    db_movie.updated_at = now()
    db.commit()
    db.refresh(db_movie)
    return


def add_movie_detail(db: Session, user_id: str, movie: MovieAdd):
    db_movie = MovieModel(
        id=generate_id(),
        title=movie.title,
        description=movie.description,
        year=movie.year,
        user_id=user_id
    )
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie


# def add_movie_images(files: List[UploadFile], movie_id: str):
#     db = SessionLocal()
#     for no, file in enumerate(files, start=1):
#         file_name = file.filename
#         try:
#             extention = ".jpg" if file.content_type == "image/jpeg" else f".{file.content_type.split('/')[1]}"
#             path = "uploads/images/" + generate_id() + extention
#             save_file(file, path)
#         except Exception as e:
#             print(e)
        
#         is_thumbnail = True if no == 1 else False
#         db_imgs = MovieImageModel(
#             id=generate_id(),
#             name=file_name,
#             path=path,
#             is_thumbnail=is_thumbnail,
#             movie_id=movie_id
#         )
#         db.add(db_imgs)
#     db.commit()
#     return


def add_movie_image(db: Session, file: UploadFile, movie_id: str, is_thumbnail: bool):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")

    db_images = get_movie_images(db=db, movie_id=movie_id)
    if len(db_images) >= 6:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="maximum 6 images allowed")
    file_name = file.filename
    try:
        extention = ".jpg" if file.content_type == "image/jpeg" else f".{file.content_type.split('/')[1]}"
        path = "uploads/images/" + generate_id() + extention
        save_file(file, path)
    except Exception as e:
        print(e)

    db_imgs = MovieImageModel(
        id=generate_id(),
        name=file_name,
        path=path,
        is_thumbnail=is_thumbnail,
        movie_id=movie_id
    )
    db.add(db_imgs)
    db.commit()
    return


def get_movie(db: Session, movie_id: str):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")
    db_movie.images = get_movie_images(db=db, movie_id=movie_id)
    return db_movie


def download_movie(db: Session, movie_id: str):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")
    return db_movie


def update_movie_details(db: Session, movie_id: str, movie: MovieAdd):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")
    
    db_movie.title = movie.title
    db_movie.description = movie.description
    db_movie.year = movie.year
    db.commit()
    db.refresh(db_movie)
    return db_movie


def update_movie_image(db: Session, movie_id: str, image_id: str, is_thumbnail: bool):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")
    
    db_image = get_movie_image_by_id(db, movie_id, image_id)
    if db_image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image is not found")
    
    db_image.is_thumbnail = is_thumbnail
    db_image.updated_at = now()
    db.commit()
    db.refresh(db_image)
    return db_image


def delete_movie_images(db: Session, movie_id: str, image_id: str):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")
    
    db_image = get_movie_image_by_id(db, movie_id, image_id)
    if db_image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image is not found")
    remove_file(db_image.path)
    db.delete(db_image)
    db.commit()
    return


def delete_movie(db: Session, movie_id: str):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")

    remove_file(db_movie.path)
    db_movie.is_deleted = True
    db_movie.updated_at = now()
    db.commit()
    return
