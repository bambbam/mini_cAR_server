import bcrypt
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from interface.router.auth import get_current_user

from interface.router.auth import get_tokens, TOKEN
from infrastructure.repository import schemas, model
from infrastructure.repository.base import get_db

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/")
async def get_user(user = Depends(get_current_user)):
    return user


class CreateUser(schemas.User):
    car_id: str
    password: str


@router.post("/")
async def create_user(user: CreateUser, db: Session = Depends(get_db)):
    is_exist_user = db.query(model.User).filter(model.User.email == user.email).first()
    if is_exist_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 유저입니다.")

    is_exist_car = db.query(model.Car).filter(model.Car.id == user.car_id).first()
    if not is_exist_car:
        raise HTTPException(status_code=400, detail="등록되지 않은 자동차입니다.")
    
    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    created_user = model.User(id=user.id, email=user.email, password=hashed_password, car_id=user.car_id)
    db.add(created_user)
    db.commit()
    return created_user


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    print(form_data)
    user: model.User = (
        db.query(model.User).filter(model.User.email == form_data.username).first()
    )
    if not user:
        raise HTTPException(status_code=400, detail="존재하지 않는 유저입니다.")
    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    if bcrypt.checkpw(user.password.encode("utf-8"), hashed_password):
        access_token = get_tokens(user)[0]
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")
