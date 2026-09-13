from sqlalchemy.orm import DeclarativeBase

# 声明性基础类，所有模型类都继承自这个类
# 这个类的作用是提供一个基础的模型类，其他模型类可以继承自这个类，
# 并且可以自动获取数据库连接
# 这个类的作用是提供一个基础的模型类，其他模型类可以继承自这个类，
# 并且可以自动获取数据库连接
class Base(DeclarativeBase):
    pass