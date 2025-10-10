from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..mysql.database import get_db, User

router = APIRouter()


@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"message": "登录成功", "user_id": user.id}


@router.get("/query")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


@router.post("/create")
def create_user(username: str, password: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    new_user = User(username=username, password=password)
    db.add(new_user)
    db.commit()
    return {"message": "用户创建成功", "user_id": new_user.id}


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    db.delete(user)
    db.commit()
    return {"message": "用户删除成功"}


@router.post("/change-password")
def change_password(user_id: int, new_password: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新密码
    user.password = new_password
    db.commit()

    return {"message": "密码修改成功"}
