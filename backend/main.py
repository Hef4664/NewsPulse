"""
NewsPulse 后端服务入口。

本文件仅提供最小可运行入口：一个 FastAPI 应用实例 + 一个健康检查路由。
后续业务路由由开发者在 src/backend/routers/ 下自行编写并挂载。
"""

from fastapi import FastAPI

#导入获取新闻分类的路由
from backend.routers.news import router as news_router

#导入CORS中间件,解决跨域问题
from fastapi.middleware.cors import CORSMiddleware

# 创建 FastAPI 应用实例。
# title / version 会直接体现在自动生成的接口文档（/docs）页面上。
app = FastAPI(
    title="NewsPulse API",
    version="0.1.0",
    description="NewsPulse 新闻资讯平台后端服务",
)
#创建允许访问的域名列表
origins = ["http://localhost:5173"]
#添加中间件
app.add_middleware(
    
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """根路由：用于确认服务已正常启动。

    Returns:
        包含服务名称与运行状态的简单字典。
    """
    return {"service": "NewsPulse API", "status": "running"}


@app.get("/health")
async def health() -> dict[str, str]:
    """健康检查路由：供容器编排或负载均衡探测服务存活状态。

    Returns:
        固定返回 status=ok，后续可在此接入数据库 / Redis 连通性检查。
    """
    return {"status": "ok"}


#挂载获取新闻分类的路由
app.include_router(news_router)