#导入APIRouter类
from backend.config.db_conf import get_db
from fastapi import APIRouter, Depends

from backend.crud import news 
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession

#创建APIRouter实例
router = APIRouter(prefix = "/api/news",tags = ["news"])


#接口实现流程
#1.模块化路由(根据API接口规范文档进行模块化)
#2.定义模型类(根据数据库表结构定义模型类)
#3.在crud文件夹里创建文件,封装操作数据库的方法
#4.在路由函数中调用crud中的方法
#创建获取分类的路由
@router.get("/categories")
async def get_categories(skip: int = 0, limit: int = 10, db: AsyncSession=Depends(get_db)):
    #调用crud中的get_categories方法获取新闻分类
    categories = await news.get_categories(db, skip, limit)
    
    #返回信息
    return {
        "code": 200,
        "message": "获取分类成功",
        "data": categories
                
    }
#创建获取新闻列表的路由
@router.get("/list")
async def get_news_list(
    category_id: int =Query(..., description="新闻分类ID",alias="categoryId"),
    page: int=1,
    page_size: int=Query(10, description="每页数量",alias="pageSize"),
    db: AsyncSession=Depends(get_db)
):
    #处理分页规则
    offset = (page - 1) * page_size
    #调用crud中的get_news_list方法获取新闻列表
    news_list = await news.get_news_list(db, category_id, offset, page_size)
    #调用crud中的get_news_count方法获取新闻总数
    total = await news.get_news_count(db, category_id)
    #跳过的新闻数量+当前获取的是否小于新闻总数,判断是否有更多新闻
    has_more = (offset + len(news_list)) < total
    return{
        "code": 200,
        "message":"获取新闻列表成功",
        "data": {
            "list":news_list,
            "total":total,
            "hasmore": has_more
        }
    }

#创建获取新闻详情的路由
@router.get("/detail")
async def get_news_detail(news_id: int = Query(..., description="新闻ID",alias="id"), db: AsyncSession = Depends(get_db)):
    #获取新闻详情,浏览量+1
    news_detail = await news.get_news_detail(db, news_id)
    if not news_detail:
        return {
            "code": 404,
            "message": "新闻不存在"
            
        }
    #增加新闻浏览量
    views_res= await news.increase_news_views(db, news_id)
    if not views_res:
        return {
            "code": 404,
            "message": "新闻不存在"
        }
    #获取同类推荐新闻
    related_news = await news.get_related_news(db, news_detail.category_id, news_id)
    return {
  "code": 200,
  "message": "success",
  "data": {
    "id": news_detail.id,
    "title": news_detail.title,
    "content": news_detail.content,
    "image": news_detail.image,
    "author": news_detail.author,
    "publishTime": news_detail.publish_time,
    "categoryId": news_detail.category_id,
    "views": news_detail.views,
    "relatedNews": related_news
  }
}

    