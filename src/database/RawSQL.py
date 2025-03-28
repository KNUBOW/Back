from sqlalchemy.schema import CreateTable
from database.orm import Base, User, Ingredient

# users 테이블 생성 SQL 출력
print(CreateTable(User.__table__).compile(compile_kwargs={"literal_binds": True}))

# ingredients 테이블 생성 SQL 출력
print(CreateTable(Ingredient.__table__).compile(compile_kwargs={"literal_binds": True}))
