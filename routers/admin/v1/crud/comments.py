from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from libs.utils import generate_id, now
from routers.admin.v1.crud.movies import get_movie_by_id
from routers.admin.v1.schemas import CommentAdd, CommentUpdate
from models import MovieCommentModel


def get_comment_by_id(db: Session, comment_id: str):
    return db.query(MovieCommentModel).filter(
        MovieCommentModel.id == comment_id,
        MovieCommentModel.is_deleted == False
    ).first()

def get_comment_replies(db: Session, comment_id: str):
    return db.query(MovieCommentModel).filter(MovieCommentModel.parent_id == comment_id, MovieCommentModel.is_deleted == False).all()


def get_comment_list(
    db: Session,
    start: int,
    limit: int,
    search: str,
    sort_by: str,
    order: str,
    movie_id: str
):
    query = db.query(MovieCommentModel).filter(MovieCommentModel.is_deleted == False, MovieCommentModel.parent_id == "0")

    if movie_id != "all":
        query = query.filter(MovieCommentModel.movie_id == movie_id)

    if search != "all":
        text = f"""%{search}%"""
        query = query.filter(MovieCommentModel.text.like(text))

    if sort_by == "text":
        if order == "desc":
            query = query.order_by(MovieCommentModel.text.desc())
        else:
            query = query.order_by(MovieCommentModel.text)
    elif sort_by == "created_at":
        if order == "desc":
            query = query.order_by(MovieCommentModel.created_at.desc())
        else:
            query = query.order_by(MovieCommentModel.created_at)
    else:
        query = query.order_by(MovieCommentModel.created_at.desc())

    count = query.count()
    results = query.offset(start).limit(limit).all()

    for result in results:
        comment_replies = get_comment_replies(db=db, comment_id=result.id)
        result.replies = comment_replies
    
    data = {"count": count, "list": results}
    return data


def add_comment(db: Session, comment: CommentAdd, user_id: str):
    db_movie = get_movie_by_id(db=db, movie_id=comment.movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")
    
    db_comment = MovieCommentModel(
        id=generate_id(),
        text=comment.text,
        parent_id=comment.parent_id,
        movie_id=comment.movie_id,
        user_id=user_id,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comment(db: Session, movie_id: str, comment_id: str):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")

    db_comment = get_comment_by_id(db=db, comment_id=comment_id)
    if db_comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment is not found")

    comment_replies = get_comment_replies(db=db, comment_id=comment_id)
    db_comment.replies = comment_replies
    return db_comment


def get_all_comments(db: Session, movie_id: str):
    db_movie = get_movie_by_id(db, movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie is not found")

    db_comments = (
        db.query(MovieCommentModel)
        .filter(
            MovieCommentModel.movie_id == movie_id,
            MovieCommentModel.is_deleted == False,
            MovieCommentModel.parent_id == "0"
        )
        .all()
    )
    for comment in db_comments:
        comment_replies = get_comment_replies(db=db, comment_id=comment.id)
        comment.replies = comment_replies
    
    db_movie.comments = db_comments
    return db_movie


def update_comment(db: Session, movie_id: str, comment_id: str, comment: CommentUpdate):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movies is not found")
    
    db_comment = get_comment_by_id(db=db, comment_id=comment_id)
    if db_comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment is not found")
    
    db_comment.text = comment.text
    db_comment.updated_at = now()
    db.commit()
    db.refresh(db_comment)
    return db_comment


def delete_comment(db: Session, movie_id:str, comment_id: str):
    db_movie = get_movie_by_id(db=db, movie_id=movie_id)
    if db_movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movies is not found")
    
    db_comment = get_comment_by_id(db=db, comment_id=comment_id)
    if db_comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment is not found")
    
    db_comment.is_deleted = True
    db_comment.updated_at = now()
    db.commit()
    return
