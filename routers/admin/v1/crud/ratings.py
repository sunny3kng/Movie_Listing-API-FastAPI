from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from libs.utils import generate_id, now
from models import MovieRatingModel
from routers.admin.v1.crud.movies import get_movie_by_id
from routers.admin.v1.schemas import RatingAdd, RatingUpdate



def get_rating_by_id(db: Session, rating_id: str):
    return db.query(MovieRatingModel).filter(MovieRatingModel.id == rating_id, MovieRatingModel.is_deleted == False).first()


def get_rating_list(
    db: Session,
    start: int,
    limit: int,
    search: str,
    sort_by: str,
    order: str,
    movie_id: str
):
    query = db.query(MovieRatingModel).filter(MovieRatingModel.is_deleted == False)

    if movie_id != "all":
        query = query.filter(MovieRatingModel.movie_id == movie_id)
    
    if search != "all":
        text = f"""%{search}%"""
        query = query.filter(MovieRatingModel.text.like(text))
    

    if sort_by == "rating":
        if order=="desc":
            query = query.order_by(MovieRatingModel.score.desc())
        else:
            query = query.order_by(MovieRatingModel.score)
    elif sort_by == "created_at":
        if order=="desc":
            query = query.order_by(MovieRatingModel.created_at.desc())
        else:
            query = query.order_by(MovieRatingModel.created_at)
    else:
        query = query.order_by(MovieRatingModel.created_at.desc())
    
    count = query.count()
    results = query.offset(start).limit(limit).all()
    data = {"count": count, "list": results}
    return data


def add_rating(db: Session, user_id: str, rating: RatingAdd):
    db_movie = get_movie_by_id(db, movie_id=rating.movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")
    
    db_rating = MovieRatingModel(
        id=generate_id(),
        score=rating.score,
        text=rating.text,
        movie_id=rating.movie_id,
        user_id=user_id
    )
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating


def get_rating(db: Session, movie_id: str, rating_id: str):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")

    db_rating = get_rating_by_id(db=db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating is not found")
    
    return db_rating


def get_all_ratings(db: Session, movie_id: str):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")
    
    db_rating = (
        db.query(MovieRatingModel)
        .filter(
            MovieRatingModel.is_deleted == False
        )
        .order_by(MovieRatingModel.created_at.desc())
        .all()
    )
    db_movie.ratings = db_rating
    return db_movie


def update_rating(db: Session, movie_id: str, rating_id: str, rating: RatingUpdate):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")

    db_rating = get_rating_by_id(db=db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating is not found")
    
    db_rating.score = rating.score
    db_rating.text = rating.text
    db_rating.updated_at = now()
    db.add(db_rating)
    db.commit()
    return db_rating


def delete_rating(db: Session, movie_id: str, rating_id: str):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")

    db_rating = get_rating_by_id(db=db, rating_id=rating_id)
    if db_rating is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating is not found")
    
    db_rating.is_deleted = True
    db_rating.updated_at = now()
    db.commit()
    return
