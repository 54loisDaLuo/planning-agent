from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# MySQL数据库连接 - 支持环境变量
DATABASE_URL = os.getenv(
    "DATABASE_URL", "mysql+pymysql://root:root@localhost:3306/planning_agent"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(50))


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#!/usr/bin/env python3
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)


def init_database():
    create_tables()
    print("数据库表创建成功")

    db = SessionLocal()
    try:
        # 创建默认测试用户
        test_user = db.query(User).filter(User.username == "admin").first()
        if not test_user:
            test_user = User(username="admin", password="admin123")
            db.add(test_user)
            db.commit()
            print("默认用户创建成功")
            print("用户名: admin")
            print("密码: admin123")
        else:
            print("默认用户已存在")
    except Exception as e:
        print(f"初始化数据库时出错: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
