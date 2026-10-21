from backend.models.news import Category, News
from sqlalchemy import func, select, update
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
#定义从数据库获取某一新闻的方法
async def get_news_detail(db: AsyncSession, news_id: int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()  # 返回单个新闻对象，如果不存在则返回 None   
#定义更新新闻浏览量的方法
async def increase_news_views(db: AsyncSession, news_id: int):
    stmt = (
        update(News)
        .where(News.id == news_id)
        .values(views=News.views + 1)
    )
    result = await db.execute(stmt)
    await db.commit()#将更改提交到数据库
    
    #添加一个更新是否成功的验证,如果更新成功则返回True,否则返回False
    return result.rowcount > 0
#获取同类推荐新闻
async def get_related_news(db: AsyncSession, category_id: int, news_id: int, limit: int = 5):
    stmt = (
        select(News)
        .where(News.category_id == category_id, News.id != news_id)
        .order_by(
            News.views.desc(),#按浏览量倒序排列,推荐浏览量更高的新闻
            News.publish_time.desc()#按发布时间倒序排列,推荐最新的新闻
            ) 
        .limit(limit)
    )
    result = await db.execute(stmt)
    related_news = result.scalars().all()
    #使用列表推导式推导出新闻的核心数据,返回新闻列表
    return [
        {
            "id": news_detail.id,
            "title": news_detail.title,
            "content": news_detail.content,
            "image": news_detail.image,
            "author": news_detail.author,
            "publishTime": news_detail.publish_time,
            "categoryId": news_detail.category_id,
            "views": news_detail.views,
        }
        for news_detail in related_news
    ]
