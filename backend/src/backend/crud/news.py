from backend.models.news import Category
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

#定义从数据库获取新闻分类的方法
async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 10):
    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
