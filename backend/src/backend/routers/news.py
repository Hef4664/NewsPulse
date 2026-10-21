#导入APIRouter类
from backend.config.db_conf import get_db
from fastapi import APIRouter, Depends

from backend.crud import news 
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