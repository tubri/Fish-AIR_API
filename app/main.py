import json
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, APIRouter
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.utils import zipfile_generator

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
router = APIRouter()
app = FastAPI(
)

# configuration - CROS
origins = [
    "http://localhost",
    "http://localhost:8081",
    "http://192.168.13.158:8081",
    "http://192.168.0.5:8081"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])


# custom OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="BGNN API",
        version="alpha 1.0.0",
        description="<p>BGNN API Documentation for developers.</p><img width='500px' src='https://bgnn.tulane.edu/workflow.png' />",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    tags_metadata = [
        {
            "name": "Multimedia",
            "description": "Multimedia information, the core of BGNN data repository ",
            "externalDocs": {
                "description": "Multimedia terms",
                "url": "https://bgnn.tulane.edu/terms/multimeida",
            },
        },
        {
            "name": "Image Quality Metadata",
            "description": "Quality Metadata for images",
            "externalDocs": {
                "description": "Image Quality terms",
                "url": "https://bgnn.tulane.edu/terms/multimeida",
            },
        },
    ]
    app.openapi_tags = tags_metadata
    return app.openapi_schema


app.openapi = custom_openapi


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# @app.post("/users/", response_model=schemas.User)
# def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     db_user = crud.get_user_by_email(db, email=user.email)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     return crud.create_user(db=db, user=user)
#
#
# @router.get("/users/", response_model=List[schemas.User])
# def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = crud.get_users(db, skip=skip, limit=limit)
#     return users
# #
# #
# @app.get("/users/{user_id}", response_model=schemas.User)
# def read_user(user_id: int, db: Session = Depends(get_db)):
#     db_user = crud.get_user(db, user_id=user_id)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user
#
#
# @router.post("/users/{user_id}/items/", response_model=schemas.Item)
# def create_item_for_user(
#     user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
# ):
#     return crud.create_user_item(db=db, item=item, user_id=user_id)


# @app.get("/items/", response_model=List[schemas.Item])
# def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     items = crud.get_items(db, skip=skip, limit=limit)
#     return items

@router.get("/multimedias/", tags=["Multimedia"], response_model=List[schemas.MultimediaExtended])
async def read_multimedias(genus: str = 'Notropis', skip: int = 0, limit: int = 20, zipfile: bool = False,
                           db: Session = Depends(get_db)
                           ):
    '''
        get multimedias and associated (meta)data, like IQ, extended metadata, hirecachy medias
        - param genus: species genus
        - param skip: start index
        - param limit: specify the number of records to return
        - param zipfile: return JSON or Zip file
        - return: multimedia lists(with associated (meta)data)
    '''
    iqs = crud.get_multimedias(db, genus=genus, skip=skip, limit=limit)
    if zipfile:
        path, filename = zipfile_generator(iqs)
        return FileResponse(path=path, filename=filename)
    return iqs

@router.get("/multimedia/", tags=["Multimedia"], response_model=schemas.MultimediaExtended)
async def read_multimedia(arkid: str = 'qs243w0c', db: Session = Depends(get_db)):
    '''
     get multimedia and associated (meta)data, like IQ, extended metadata, hirecachy medias by ARK ID
    :param arkid: ark id
    :return: multimedia entity
    '''
    iqs = crud.get_multimedia(db, ark_id=arkid)
    if iqs is None:
        raise HTTPException(status_code=404, detail="Image Not Found")
    return iqs


@router.get("/iq/", tags=["Image Quality Metadata"], response_model=List[schemas.IQ])
async def read_iqs(skip: int = 0, limit: int = 100, zipfile: bool = False, db: Session = Depends(get_db)):
    '''
        get image quality metadatas
        - param skip: start index
        - param limit: specify the number of records to return
        - param zipfile: return JSON or Zip file
        - return: image quality metadata lists
    '''
    if zipfile:
        path, filename = zipfile_generator()
        return FileResponse(path=path, filename=filename)
    iqs = crud.get_iqs(db, skip=skip, limit=limit)
    return iqs


app.include_router(router)