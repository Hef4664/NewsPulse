#导入定义基类,模型类需要的模块
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

#定义基类
class Base(DeclarativeBase):
    #公共属性
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)    
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

#创建模型类(新闻分类)
class Category(Base):
    __tablename__ = "news_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="新闻分类ID")
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="新闻分类名称")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序顺序")

    # __repr__ 是 Python 的一个"特殊方法"（前后各两个下划线），
    # 作用：当你用 print() 打印这个对象、或在调试器里查看它时，
    # Python 会调用这个方法，决定"显示成什么样"。
    # 不定义的话，默认只会显示类似 <backend.models.news.Category object at 0x...>，
    # 看不出这条分类到底是哪一条，排查问题时很不方便。
    # -> str 表示这个函数"返回一个字符串"（type hint 类型提示，写不写都能运行，但有助于读懂代码）。
    def __repr__(self) -> str:
        # f"..." 是 f-string（格式化字符串）：花括号 {} 里的内容会被替换成变量的实际值。
        # 所以打印一条分类时，会显示成：<Category(id=1, name=国内, sort_order=0)>，
        # 一眼就能看出这条记录的三个字段分别是什么。
        # self.id / self.name / self.sort_order 就是取"当前这条对象"自己的三个属性值。
        return f"<Category(id={self.id}, name={self.name}, sort_order={self.sort_order})>"