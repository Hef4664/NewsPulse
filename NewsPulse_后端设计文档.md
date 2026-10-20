# NewsPulse 后端设计文档

> 一句话定位：NewsPulse 是一个基于 FastAPI + SQLAlchemy（异步）构建的新闻资讯后端服务，提供用户管理、新闻浏览、收藏、浏览历史与 Redis 缓存能力，并对外暴露统一的 RESTful API 与统一 JSON 响应结构。

---

## 1. 项目概述

### 1.1 项目简介

NewsPulse 是一个现代化新闻资讯系统的后端 API 服务，采用异步 Python 框架 FastAPI 开发，使用 MySQL 作为数据库存储，通过 SQLAlchemy ORM 进行数据访问，并以 Redis 作为缓存层。

### 1.2 业务目标

- 为新闻客户端（App / H5 / 小程序）提供统一的新闻数据与用户行为接口。
- 支持用户注册登录、个人信息维护、新闻分类浏览、新闻详情查看、收藏管理与浏览历史管理。
- 借助缓存与异步 IO 提升高并发下的接口响应能力。

### 1.3 功能范围

| 模块 | 核心能力 | 是否需要认证 |
| --- | --- | --- |
| 用户管理 | 注册、登录、获取信息、更新信息、修改密码 | 注册/登录免认证，其余需认证 |
| 新闻 | 分类列表、新闻列表（分页 + 分类筛选）、新闻详情、浏览量统计 | 否 |
| 收藏 | 收藏状态检查、添加、取消、列表、清空 | 是 |
| 浏览历史 | 添加记录、列表、删除单条、清空 | 是 |
| AI 问答 | 客户端直连大模型流式对话（SSE），不经过本服务 | — |
| 缓存 | 新闻详情、新闻列表、分类数据、用户历史记录 | — |

### 1.4 术语说明

| 术语 | 说明 |
| --- | --- |
| FastAPI | 基于 Python 类型注解的高性能异步 Web 框架，自动生成 OpenAPI 文档 |
| SQLAlchemy（异步） | Python 主流 ORM，异步模式下通过 `AsyncSession` 访问数据库 |
| ORM | Object-Relational Mapping，对象关系映射，用 Python 类映射数据库表 |
| CRUD | Create / Read / Update / Delete，数据增删改查操作的统称 |
| Token | 登录后下发的访问令牌，用于标识用户身份 |
| Redis | 内存键值数据库，本文用作缓存层 |
| 软删除 | 数据行保留、以字段标记失效的删除方式 |

---

## 2. 技术栈

| 层次 | 选型 | 说明 |
| --- | --- | --- |
| 后端框架 | FastAPI | 异步、类型友好、自带 OpenAPI 交互文档 |
| 数据存储 | MySQL | 关系型数据，承载用户、新闻、收藏、历史等结构化数据 |
| ORM | SQLAlchemy（异步） | 统一数据模型定义与异步查询 |
| 数据库驱动 | aiomysql | MySQL 的异步驱动，与 SQLAlchemy 异步引擎配合 |
| 密码加密 | passlib + bcrypt | 密码加盐哈希存储，不落明文 |
| 缓存 | Redis | 热点数据缓存，降低数据库压力 |
| 并发模型 | Python asyncio | 单线程事件循环下的高并发 IO |

---

## 3. 系统架构

### 3.1 分层架构

```
客户端（App / H5）
        │  HTTP + JSON
        ▼
┌──────────────────────────────────────┐
│ routers/    路由层：参数接收、鉴权      │
├──────────────────────────────────────┤
│ schemas/    校验层：Pydantic 出入参    │
├──────────────────────────────────────┤
│ crud/       数据访问层：业务数据库操作  │
├──────────────────────────────────────┤
│ models/     模型层：ORM 表结构映射      │
└──────────────────────────────────────┘
        │                    │
        ▼                    ▼
     MySQL               Redis（缓存）
```

### 3.2 请求处理链路

1. 请求进入 `routers/` 对应路由函数。
2. 路由层通过 `schemas/` 中的 Pydantic 模型校验并解析出入参。
3. 需认证的接口从请求头解析 Token 并校验有效性，取得 `user_id`。
4. 查询优先读 Redis 缓存；未命中则调用 `crud/` 访问 MySQL。
5. 查询结果按统一 JSON 结构封装后返回；写操作成功后失效相关缓存。

### 3.3 鉴权链路

- 登录成功 → 生成 Token 并写入 `user_token` 表 → 返回给客户端。
- 客户端后续请求在头部携带 `Authorization: <token>`。
- 服务端校验 Token 是否存在且未过期 → 取出对应用户身份 → 继续执行业务。

---

## 4. 项目结构

```
NewsPulse/                               # 项目根目录
├── crud/                               # 数据访问层（CRUD 操作）
│   ├── favorite.py                     # 收藏相关数据库操作
│   ├── history.py                      # 历史记录相关数据库操作
│   ├── news.py                         # 新闻相关数据库操作
│   └── users.py                        # 用户相关数据库操作
│
├── models/                             # 数据模型定义
│   ├── favorite.py                     # 收藏数据模型
│   ├── history.py                      # 历史记录数据模型
│   ├── news.py                         # 新闻数据模型
│   └── users.py                        # 用户数据模型
│
├── routers/                            # API 路由定义
│   ├── favorite.py                     # 收藏相关 API 路由
│   ├── history.py                      # 历史记录相关 API 路由
│   ├── news.py                         # 新闻相关 API 路由
│   └── users.py                        # 用户相关 API 路由
│
├── schemas/                            # 数据校验模型（Pydantic）
│   ├── favorite.py                     # 收藏数据校验模型
│   ├── history.py                      # 历史记录数据校验模型
│   ├── news.py                         # 新闻数据校验模型
│   └── users.py                        # 用户数据校验模型
│
├── utils/                              # 工具函数目录（鉴权、响应封装、缓存封装等）
│
├── config/                             # 配置相关
│   ├── db_conf.py                      # 数据库配置
│   └── cache_conf.py                   # Redis 缓存配置
│
├── main.py                             # 应用入口文件
└── test_main.http                      # HTTP 接口测试文件
```

---

## 5. 数据库设计

### 5.1 数据表总览

| 序号 | 表名 | 中文名 | 说明 |
| --- | --- | --- | --- |
| 1 | `user` | 用户表 | 用户基本信息（用户名、加密密码、昵称、头像、性别、简介、手机号） |
| 2 | `user_token` | 用户令牌表 | 认证令牌管理，支持过期机制 |
| 3 | `news_category` | 新闻分类表 | 分类名称、排序等 |
| 4 | `news` | 新闻表 | 标题、简介、正文、配图、作者、浏览量、发布时间、所属分类 |
| 5 | `favorite` | 收藏表 | 关联用户与新闻，记录收藏时间 |
| 6 | `history` | 浏览历史表 | 关联用户与新闻，记录浏览时间 |
| 7 | `related_news` | 相关新闻关联表 | `news_id` → `related_news_id` 的自关联，为推荐位提供数据 |
| 8 | `ai_chat` | AI 聊天记录表 | 记录用户提问与 AI 回复，供 AI 问答沉淀历史 |

### 5.2 表关系

```
user 1 ──── n user_token
user 1 ──── n favorite n ──── 1 news n ──── 1 news_category
user 1 ──── n history  n ──── 1 news
```

- `favorite` 与 `history` 对 `(user_id, news_id)` 组合须保证唯一性/去重语义（同一用户对同一新闻只保留一条收藏与一条最新浏览记录）。
- `news.category_id` 外键指向 `news_category.id`。
- `related_news` 的两个外键都指向 `news.id`（自关联），`(news_id, related_news_id)` 唯一，防止重复推荐。
- `ai_chat.user_id` 外键指向 `user.id`，随用户删除级联清理。

### 5.3 字段设计要点

| 表 | 关键字段 | 约束/说明 |
| --- | --- | --- |
| `user` | `username`、`password`、`nickname`、`avatar`、`gender`、`bio`、`phone` | `username` 唯一；`password` 存储 bcrypt 哈希；`gender` 默认 `unknown`；`bio` 默认「这个人很懒，什么都没留下」 |
| `user_token` | `user_id`、`token`、`expires_at` | `token` 唯一索引；`expires_at` 到期后需重新登录获取 |
| `news_category` | `name`、`sort_order` | `name` 唯一；`sort_order` 控制首页分类展示顺序 |
| `news` | `title`、`description`、`content`、`image`、`author`、`views`、`publish_time`、`category_id` | 列表按 `publish_time` 倒序；详情页触发 `views` 自增 |
| `favorite` | `user_id`、`news_id`、`created_at` | `(user_id, news_id)` 组合唯一约束 |
| `history` | `user_id`、`news_id`、`view_time` | 未建组合唯一索引，重复浏览需在应用层去重并更新时间 |
| `related_news` | `news_id`、`related_news_id` | 组合唯一约束，两侧外键均级联删除 |
| `ai_chat` | `user_id`、`message`、`response`、`created_at` | 一问一答一条记录，`created_at` 倒序索引 |

### 5.4 索引设计

- `user.username`：唯一索引（登录高频查询）。
- `user_token.token`：唯一索引（每次鉴权都会查询）。
- `news.publish_time`：倒序普通索引 `idx_publish_time`；`news.category_id` 另有外键索引。（当前库结构**未建** `(category_id, publish_time)` 联合索引，分类页数据量上来后可补。）
- `favorite.user_id`、`history.user_id`：支撑「我的收藏 / 我的历史」按用户分页查询。
- `favorite(user_id, news_id)`：组合唯一索引，防重复；`history` 目前只有 `user_id`、`news_id`、`view_time` 三个单列索引，去重靠应用层实现。

---

## 6. 接口设计规范

### 6.1 基础信息

| 项 | 值 |
| --- | --- |
| 基础 URL | `http://127.0.0.1:8000`（与前端 `src/config/api.js` 的 `baseURL` 一致） |
| 数据格式 | 请求与响应均为 `application/json` |
| 字符编码 | UTF-8 |

### 6.2 响应结构

所有接口返回统一 JSON 结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | integer | 业务状态码，200 表示成功 |
| `message` | string | 结果描述，可直接用于前端提示 |
| `data` | object / array / null | 业务数据，无返回体时为 `null` |

### 6.3 命名约定

- 路径：全小写，多单词直接拼接，资源名用模块名（`/api/user/...`）。
- 路径参数：`snake_case`（如 `{history_id}`）。
- 查询参数与请求体字段：`camelCase`（如 `categoryId`、`pageSize`、`newsId`、`oldPassword`），与前端保持一致。
- 已按 `db/database.sql` 与前端源码核对：数据库统一使用 `snake_case`（`publish_time`、`category_id`、`created_at`）；前端 `NewsItem.vue`、`NewsDetail.vue`、`Favorite.vue`、`History.vue` 读取的是 `publishTime`、`relatedNews`，而 `store/modules/news.js` 用 `categoryId` 传参。**因此序列化层（Pydantic `alias`）需把 snake_case 输出为 camelCase**，否则列表页与详情页的时间字段会显示为空。

### 6.4 认证方式

大部分接口需要认证，通过在请求头中添加 `Authorization` 字段实现：

```
Authorization: token值
```

- 无需认证：用户注册、用户登录、新闻分类、新闻列表、新闻详情。
- 需要认证：用户信息、更新信息、修改密码、收藏全部接口、历史全部接口。

### 6.5 分页约定

- 入参统一为 `page`（默认 1）与 `pageSize`（默认 10，最大 100）。
- 出参统一为 `{ list, total, hasMore }`；前端 `Favorite.vue` 额外读取单条的 `favoriteTime`，`History.vue` 额外读取 `viewTime`。
- 分类列表接口例外，使用 `skip` / `limit`（默认 0 / 100）并直接返回数组。

---

## 7. 接口详情

### 7.1 用户管理模块

#### 7.1.1 用户注册

- **接口地址**：`POST /api/user/register`
- **请求头**：无需认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

- **请求示例**：

```json
{
  "username": "example_user",
  "password": "example_password"
}
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "token": "用户访问令牌",
    "userInfo": {
      "id": 1,
      "username": "example_user",
      "bio": "这个人很懒，什么都没留下",
      "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg"
    }
  }
}
```

- **业务说明**：注册成功即视为登录成功，直接下发 Token；用户名重复需返回业务错误。

#### 7.1.2 用户登录

- **接口地址**：`POST /api/user/login`
- **请求头**：无需认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| username | string | 是 | 用户名 |
| password | string | 是 | 密码 |

- **请求示例**：

```json
{
  "username": "example_user",
  "password": "example_password"
}
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "用户访问令牌",
    "userInfo": {
      "id": 1,
      "username": "example_user",
      "nickname": null,
      "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
      "bio": "这个人很懒，什么都没留下"
    }
  }
}
```

#### 7.1.3 获取用户信息

- **接口地址**：`GET /api/user/info`
- **请求头**：需要认证
- **响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "example_user",
    "nickname": null,
    "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
    "gender": "unknown",
    "bio": "这个人很懒，什么都没留下"
  }
}
```

#### 7.1.4 更新用户信息

- **接口地址**：`PUT /api/user/update`
- **请求头**：需要认证
- **请求参数**（全部可选，按传入字段局部更新）：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| nickname | string | 否 | 昵称 |
| avatar | string | 否 | 头像 URL |
| gender | string | 否 | 性别 |
| bio | string | 否 | 个人简介 |
| phone | string | 否 | 手机号 |

- **请求示例**：

```json
{
  "bio": "这是我的个人简介"
}
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": 1,
    "username": "example_user",
    "nickname": null,
    "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
    "gender": "unknown",
    "bio": "这是我的个人简介"
  }
}
```

#### 7.1.5 修改用户密码

- **接口地址**：`PUT /api/user/password`
- **请求头**：需要认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| oldPassword | string | 是 | 当前密码 |
| newPassword | string | 是 | 新密码 |

- **请求示例**：

```json
{
  "oldPassword": "current_password",
  "newPassword": "new_password"
}
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "密码修改成功",
  "data": null
}
```

- **业务说明**：需校验旧密码；修改成功后建议使该用户旧 Token 失效。

### 7.2 新闻模块

#### 7.2.1 获取新闻分类列表

- **接口地址**：`GET /api/news/categories`
- **请求头**：无需认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| skip | integer | 否 | 跳过的记录数，默认 0 |
| limit | integer | 否 | 返回的记录数限制，默认 100 |

- **请求示例**：

```
GET /api/news/categories
GET /api/news/categories?skip=0&limit=10
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "created_at": "2023-01-01T00:00:00",
      "updated_at": "2023-01-01T00:00:00",
      "name": "科技",
      "sort_order": 0
    }
  ]
}
```

#### 7.2.2 获取新闻列表

- **接口地址**：`GET /api/news/list`
- **请求头**：无需认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| categoryId | integer | 是 | 分类 ID |
| page | integer | 否 | 页码，默认 1 |
| pageSize | integer | 否 | 每页数量，最大 100，默认 10 |

- **请求示例**：

```
GET /api/news/list?categoryId=1
GET /api/news/list?categoryId=1&page=2&pageSize=20
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "publish_time": "2023-01-01T00:00:00",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00",
        "category": null,
        "title": "新闻标题",
        "description": "新闻简介",
        "content": "新闻内容",
        "image": null,
        "author": null,
        "category_id": 1,
        "views": 0
      }
    ],
    "total": 100,
    "hasMore": true
  }
}
```

- **业务说明**：按 `publish_time` 倒序排列；`hasMore = page * pageSize < total`。

#### 7.2.3 获取新闻详情

- **接口地址**：`GET /api/news/detail`
- **请求头**：无需认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| id | integer | 是 | 新闻 ID |

- **请求示例**：

```
GET /api/news/detail?id=1
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "新闻标题",
    "content": "新闻内容",
    "image": null,
    "author": null,
    "publishTime": "2023-01-01T00:00:00",
    "categoryId": 1,
    "views": 1,
    "relatedNews": []
  }
}
```

- **业务说明**：每次访问触发 `views` 自增；同时返回同分类相关新闻 `relatedNews`；详情数据可进 Redis 缓存。

### 7.3 收藏模块

#### 7.3.1 检查新闻收藏状态

- **接口地址**：`GET /api/favorite/check`
- **请求头**：需要认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| newsId | integer | 是 | 新闻 ID |

- **请求示例**：

```
GET /api/favorite/check?newsId=1
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "isFavorite": true
  }
}
```

#### 7.3.2 添加收藏

- **接口地址**：`POST /api/favorite/add`
- **请求头**：需要认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| newsId | integer | 是 | 新闻 ID |

- **请求示例**：

```json
{
  "newsId": 1
}
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "收藏成功",
  "data": {
    "id": 1,
    "userId": 1,
    "newsId": 1,
    "createTime": "2023-01-01T00:00:00"
  }
}
```

- **业务说明**：重复收藏需幂等处理（已收藏则返回提示，不重复插入）。

#### 7.3.3 取消收藏

- **接口地址**：`DELETE /api/favorite/remove`
- **请求头**：需要认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| newsId | integer | 是 | 新闻 ID |

- **请求示例**：

```
DELETE /api/favorite/remove?newsId=1
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "取消收藏成功",
  "data": null
}
```

#### 7.3.4 获取收藏列表

- **接口地址**：`GET /api/favorite/list`
- **请求头**：需要认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | integer | 否 | 页码，默认 1 |
| pageSize | integer | 否 | 每页条数，默认 10，最大 100 |

- **请求示例**：

```
GET /api/favorite/list
GET /api/favorite/list?page=1&pageSize=10
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "title": "新闻标题",
        "description": "",
        "image": "",
        "author": "",
        "publishTime": "2023-01-01T00:00:00",
        "categoryId": 1,
        "views": 1,
        "favoriteTime": "2023-01-01T00:00:00"
      }
    ],
    "total": 1,
    "hasMore": false
  }
}
```

#### 7.3.5 清空所有收藏

- **接口地址**：`DELETE /api/favorite/clear`
- **请求头**：需要认证
- **响应示例**：

```json
{
  "code": 200,
  "message": "成功删除1条收藏记录",
  "data": null
}
```

- **业务说明**：`message` 中回显实际删除条数。

### 7.4 浏览历史模块

#### 7.4.1 添加浏览记录

- **接口地址**：`POST /api/history/add`
- **请求头**：需要认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| newsId | integer | 是 | 新闻 ID |

- **请求示例**：

```json
{
  "newsId": 1
}
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "添加成功",
  "data": {
    "id": 1,
    "userId": 1,
    "newsId": 1,
    "viewTime": "2023-01-01T00:00:00"
  }
}
```

- **业务说明**：同一用户重复浏览同一新闻时应更新 `viewTime` 而非新增记录。

#### 7.4.2 获取浏览历史列表

- **接口地址**：`GET /api/history/list`
- **请求头**：需要认证
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| page | integer | 否 | 页码，默认 1 |
| pageSize | integer | 否 | 每页条数，默认 10，最大 100 |

- **请求示例**：

```
GET /api/history/list
GET /api/history/list?page=1&pageSize=10
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "title": "新闻标题",
        "description": "",
        "image": "",
        "author": "",
        "publishTime": "2023-01-01T00:00:00",
        "categoryId": 1,
        "views": 1,
        "viewTime": "2023-01-01T00:00:00"
      }
    ],
    "total": 1,
    "hasMore": false
  }
}
```

#### 7.4.3 删除单条浏览记录

- **接口地址**：`DELETE /api/history/delete/{history_id}`
- **请求头**：需要认证
- **路径参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| history_id | integer | 是 | 历史记录 ID |

- **请求示例**：

```
DELETE /api/history/delete/1
```

- **响应示例**：

```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

- **业务说明**：只能删除属于当前登录用户的记录，否则按「记录不存在」处理。

#### 7.4.4 清空浏览历史

- **接口地址**：`DELETE /api/history/clear`
- **请求头**：需要认证
- **响应示例**：

```json
{
  "code": 200,
  "message": "清空成功",
  "data": null
}
```

### 7.5 接口总览

| 接口 | 方法 | 认证 | 说明 |
| --- | --- | --- | --- |
| `/api/user/register` | POST | 否 | 用户注册 |
| `/api/user/login` | POST | 否 | 用户登录 |
| `/api/user/info` | GET | 是 | 获取用户信息 |
| `/api/user/update` | PUT | 是 | 更新用户信息 |
| `/api/user/password` | PUT | 是 | 修改用户密码 |
| `/api/news/categories` | GET | 否 | 获取新闻分类列表 |
| `/api/news/list` | GET | 否 | 获取新闻列表 |
| `/api/news/detail` | GET | 否 | 获取新闻详情 |
| `/api/favorite/check` | GET | 是 | 检查新闻收藏状态 |
| `/api/favorite/add` | POST | 是 | 添加收藏 |
| `/api/favorite/remove` | DELETE | 是 | 取消收藏 |
| `/api/favorite/list` | GET | 是 | 获取收藏列表 |
| `/api/favorite/clear` | DELETE | 是 | 清空所有收藏 |
| `/api/history/add` | POST | 是 | 添加浏览记录 |
| `/api/history/list` | GET | 是 | 获取浏览历史列表 |
| `/api/history/delete/{history_id}` | DELETE | 是 | 删除单条浏览记录 |
| `/api/history/clear` | DELETE | 是 | 清空浏览历史 |
| DashScope `/chat/completions` | POST | 第三方 Key | AI 流式问答（浏览器直连，非本服务） |

### 7.6 AI 问答模块

#### 7.6.1 AI 流式对话

- **接口地址**：`https://ws-mq4sk46skvavpo4v.cn-beijing.maas.aliyuncs.com/compatible-mode/v1/chat/completions`（阿里云百炼通义千问专属 MaaS 端点，**非本服务提供**）
- **实现位置**：`frontend/src/views/AIChat.vue`，参数集中在 `frontend/src/config/api.js` 的 `aiChatConfig`
- **请求头**：`Authorization: Bearer <apiKey>`、`Content-Type: application/json`、`X-DashScope-SSE: enable`
- **请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| model | string | 是 | 模型名，当前配置为 `qwen3.8-flash` |
| messages | array | 是 | 对话历史，元素形如 `{ role, content }`，`role` 取 `user` / `assistant` |
| stream | boolean | 是 | 固定为 `true`，走 SSE 流式返回 |

- **请求示例**：

```json
{
  "model": "qwen3.8-flash",
  "messages": [
    { "role": "user", "content": "今天有什么科技新闻？" }
  ],
  "stream": true
}
```

- **响应形态**：SSE 流，逐行 `data: {json}`，取 `choices[0].delta.content` 拼接为完整回复，`data: [DONE]` 结束。

- **现状说明（风险项）**：
  1. 当前由**浏览器直连**大模型服务；API Key 已于 2026-10-20 从源码移除，改为读取 `frontend/.env.local` 的 `VITE_DASHSCOPE_API_KEY`（该文件已被 git 忽略）。但 **`VITE_` 前缀变量会在 `vite build` 时被内联进 `dist/` 产物**，仍可被客户端读取，**迁移目标**是改由本服务代理转发、Key 只放服务端环境变量。
  2. 数据库已建 `ai_chat` 表，但当前对话**不落库**；接入代理后应把每轮问答写入 `ai_chat`，并按 `user_id` 校验归属。
  3. 对话鉴权走的是第三方 Key，与本服务的 `Authorization: <token>` 体系相互独立。

---

## 8. 缓存设计

### 8.1 缓存策略

系统采用 Redis 作为缓存层，对高频访问的数据进行缓存，以提升响应速度并降低数据库压力。

### 8.2 缓存键设计

| 序号 | 缓存内容 | 缓存键 | 过期时间 | 目的 |
| --- | --- | --- | --- | --- |
| 1 | 新闻详情 | `news:detail:{news_id}` | 1 小时 | 加速详情页访问 |
| 2 | 新闻列表 | `news:list:{category_id}:{page}:{size}` | 30 分钟 | 降低首页/分类页查询压力 |
| 3 | 分类数据 | `news:categories` | 2 小时 | 加速导航栏分类加载 |
| 4 | 用户历史记录 | `history:list:{user_id}` | 1 小时 | 提高历史记录访问性能（前端目前直接查库，此项为预留键） |

### 8.3 缓存更新机制

- 数据变更时清除相关缓存，采用**缓存失效**（Cache Invalidation，数据变了就删缓存、下次读取再重建）而非主动更新策略。
- 支持按模式批量清除（如 `news:detail:*`）。
- 写操作（新增/更新/删除新闻、收藏、历史）成功后立即失效对应缓存键。

### 8.4 缓存配置

在 `config/cache_conf.py` 中配置 Redis 连接信息：

```python
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
```

---

## 9. 认证与安全

### 9.1 认证机制

1. 用户登录成功后返回访问令牌（Token）。
2. 需要认证的接口在请求头中添加 `Authorization: token值`。
3. 令牌有效期为 7 天，过期需重新登录。
4. 服务端通过 `user_token` 表校验令牌存在性与有效期，并解析出 `user_id`。

### 9.2 安全要求

- 所有密码均以 `passlib + bcrypt` 加盐哈希存储，禁止明文与可逆加密。
- Token 需具备足够随机性（建议 `secrets` 生成），不得使用可预测的自增 ID 或时间戳。
- 涉及用户私有数据的接口（收藏、历史、用户信息）必须校验数据归属，防止越权访问。
- 数据库与 Redis 连接信息不写入代码仓库，通过配置文件或环境变量注入。

---

## 10. 错误处理

### 10.1 HTTP 状态码

| 状态码 | 场景 |
| --- | --- |
| 200 | 请求成功 |
| 400 | 参数校验失败、业务规则不满足（如用户名已存在） |
| 401 | 未携带令牌或令牌失效/过期 |
| 404 | 资源不存在（新闻、历史记录等） |
| 500 | 服务器内部错误 |

### 10.2 错误响应示例

```json
{
  "code": 401,
  "message": "未登录或登录已过期",
  "data": null
}
```

### 10.3 处理原则

- 统一由异常处理器捕获并转换为统一 JSON 结构，不向客户端暴露堆栈信息。
- 业务异常与系统异常区分处理，业务异常附带可直接展示的 `message`。

---

## 11. 开发规范

- 全部使用异步数据库操作（`async` / `await` + `AsyncSession`），避免阻塞事件循环。
- 所有密码加密存储，任何日志与响应中不得输出密码。
- 接口返回统一 JSON 结构（`code` / `message` / `data`）。
- 分层职责清晰：路由层不直接编写 SQL，数据访问统一收敛在 `crud/`。
- 缓存操作封装为独立函数，便于复用与统一失效。
- 入参校验全部通过 Pydantic 模型完成，禁止在路由函数内手工解析。
- 统一异常处理与统一响应封装由公共工具模块提供。
- 保留 `test_main.http` 作为接口手工调试入口，并保证接口文档与实现同步更新。
- 前端 Axios 拦截层不在本项目内统一封装，鉴权头由各 store 自行拼接（`Authorization: <token>`，不带 `Bearer` 前缀），后端鉴权解析须与此保持一致。
- 前端 `store/modules/news.js` 的 `categories` 会额外追加一个 `id: 10, name: '更多'` 的虚拟分类，后端分类接口不要把 `id = 10` 占作真实分类。

---

## 12. 性能优化

- 使用 Redis 缓存热点数据（详情、列表、分类、历史），显著减少穿透到 MySQL 的查询。
- 异步数据库操作与异步驱动（aiomysql）提升 IO 并发能力。
- 合理的数据库索引设计：新闻表依赖 `publish_time` 倒序索引与外键索引支撑列表查询，用户维度依赖 `user_id` 索引；数据量增长后再补 `(category_id, publish_time)` 联合索引。
- 数据库连接池管理，减少建连开销。
- 分页参数上限（`pageSize ≤ 100`）防止大结果集拖垮服务。

---

## 附录 A：文档合并说明

本文由以下两份原始文档合并而成，以便作为单一完整设计文档使用：

| 来源 | 原文档标题 | 并入位置 |
| --- | --- | --- |
| 后端设计说明文档 | 后端设计说明文档（原项目名已弃用，全文统一为 NewsPulse） | 第 1～5 章、第 8～12 章 |
| 接口规范文档 | API 接口文档 | 第 6 章（接口规范）、第 7 章（接口详情） |

合并处理约定：

1. 项目名称统一为 **NewsPulse**，项目根目录示例同步改为 `NewsPulse/`。
2. 原「API 接口说明」章节中的接口清单表，扩写为第 6 章规范 + 第 7 章逐接口详情（含请求/响应示例），并在 7.5 保留总览表。
3. 已在原文之上补充：分层架构与请求链路、表关系与索引设计、命名约定、错误码表、安全要求。这些内容属于对原文信息的结构化整理，未新增原文未提及的业务功能。
4. 原文存在的不一致项（字段命名 snake_case / camelCase 混用）已按第 6.3 节结论确认，需在序列化层用 alias 统一为 camelCase。
5. 本轮按工作区内的 `db/database.sql` 与 `frontend/src/` 源码二次校准，修正了表清单（新增 `related_news`、`ai_chat`）、令牌过期字段名（`expires_at`）、索引现状、基础 URL（`127.0.0.1:8000`），并新增 7.6 AI 问答模块。
