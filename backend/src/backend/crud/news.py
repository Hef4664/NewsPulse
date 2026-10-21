from backend.models.news import Category, News
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

#定义从数据库获取新闻分类的方法
async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 10):
    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

#定义从数据库获取新闻列表的方法
async def get_news_list(db: AsyncSession, category_id: int, skip=0, limit=10):
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
#定义从数据库获取某一新闻分类的新闻总数的方法
async def get_news_count(db: AsyncSession, category_id: int):
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalar_one() #保证新闻总数只返回一个值