import shutil

from os import remove
from uuid import uuid4
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy import inspect


def now():
    return datetime.now()


def generate_id():
    id = str(uuid4())
    return id


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def save_file(file: UploadFile, name: str):
    with open(name, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return name


def remove_file(path):
    try:
        remove(path)
    except Exception as e:
        print(e)

