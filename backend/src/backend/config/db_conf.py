#导入需要的模块
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine,async_sessionmaker

#将数据库的URI,定义为常量
DATABASE_URL = "mysql+aiomysql://root:Fhe041214.@localhost:3306/news_app?charset=utf8mb4"

#创建异步数据库引擎引擎
async_engine = create_async_engine(
    DATABASE_URL, #数据库URI
    echo=True,  # 打印SQL日志
    pool_size=10,  #连接池大小
    max_overflow=20,  #最大溢出连接数
    
)

#创建异步会话工厂
AsyncSessionLocal  = async_sessionmaker(
    bind=async_engine,  #绑定数据库引擎
    expire_on_commit=False,  #提交后不失效
    class_=AsyncSession,  #使用异步会话类
)
#创建依赖项,用来获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session  #返回数据库会话
            await session.commit()  #提交事务
        except Exception :
            await session.rollback()  #回滚事务
            raise  #抛出异常
        finally:
            await session.close()  #关闭会话    