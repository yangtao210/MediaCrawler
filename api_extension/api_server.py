# -*- coding: utf-8 -*-
# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

"""
MediaCrawler API 服务
提供REST API接口来调用各平台的爬虫功能
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Optional, List
from enum import Enum

# 添加父目录到路径，以便导入主项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

import config
from database import db
from main import CrawlerFactory

# 创建FastAPI应用
app = FastAPI(
    title="MediaCrawler API",
    description="多平台自媒体数据采集API服务",
    version="1.1.0",
)

# 任务状态管理
task_status = {}


class PlatformEnum(str, Enum):
    """支持的平台"""
    XHS = "xhs"  # 小红书
    DOUYIN = "dy"  # 抖音
    KUAISHOU = "ks"  # 快手
    BILIBILI = "bili"  # B站
    WEIBO = "wb"  # 微博
    TIEBA = "tieba"  # 百度贴吧
    ZHIHU = "zhihu"  # 知乎


class CrawlerTypeEnum(str, Enum):
    """爬取类型"""
    SEARCH = "search"  # 关键词搜索
    DETAIL = "detail"  # 指定帖子详情
    CREATOR = "creator"  # 创作者主页


class LoginTypeEnum(str, Enum):
    """登录方式"""
    QRCODE = "qrcode"  # 二维码登录
    PHONE = "phone"  # 手机号登录
    COOKIE = "cookie"  # Cookie登录


class SaveDataOptionEnum(str, Enum):
    """数据保存方式"""
    CSV = "csv"
    JSON = "json"
    SQLITE = "sqlite"
    MYSQL = "db"
    MONGODB = "mongodb"


class CrawlerRequest(BaseModel):
    """爬虫任务请求参数"""
    platform: PlatformEnum = Field(..., description="平台名称")
    crawler_type: CrawlerTypeEnum = Field(..., description="爬取类型")
    keywords: Optional[str] = Field(None, description="搜索关键词（多个用逗号分隔）")
    note_ids: Optional[List[str]] = Field(None, description="帖子ID列表（detail类型时使用，支持完整URL或纯ID）")
    login_type: LoginTypeEnum = Field(LoginTypeEnum.QRCODE, description="登录方式")
    start_page: int = Field(1, description="起始页码", ge=1)
    max_notes_count: int = Field(15, description="爬取帖子数量", ge=1, le=100)
    enable_comments: bool = Field(True, description="是否爬取评论")
    enable_sub_comments: bool = Field(False, description="是否爬取二级评论")
    save_data_option: SaveDataOptionEnum = Field(SaveDataOptionEnum.JSON, description="数据保存方式")
    cookies: Optional[str] = Field(None, description="Cookie字符串（cookie登录时使用）")

    class Config:
        json_schema_extra = {
            "example": {
                "platform": "xhs",
                "crawler_type": "search",
                "keywords": "Python编程,数据分析",
                "login_type": "qrcode",
                "start_page": 1,
                "max_notes_count": 20,
                "enable_comments": True,
                "enable_sub_comments": False,
                "save_data_option": "json"
            }
        }


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    status: str
    message: str
    created_at: str


class InitDbRequest(BaseModel):
    """初始化数据库请求"""
    db_type: str = Field(..., description="数据库类型：sqlite 或 mysql")

    class Config:
        json_schema_extra = {
            "example": {
                "db_type": "sqlite"
            }
        }


async def run_crawler_task(task_id: str, crawler_params: CrawlerRequest):
    """后台运行爬虫任务"""
    try:
        task_status[task_id] = {
            "status": "running",
            "message": "任务正在执行中...",
            "started_at": datetime.now().isoformat(),
        }

        # 设置配置参数
        config.PLATFORM = crawler_params.platform.value
        config.CRAWLER_TYPE = crawler_params.crawler_type.value
        config.KEYWORDS = crawler_params.keywords or ""
        config.LOGIN_TYPE = crawler_params.login_type.value
        config.START_PAGE = crawler_params.start_page
        config.CRAWLER_MAX_NOTES_COUNT = crawler_params.max_notes_count
        config.ENABLE_GET_COMMENTS = crawler_params.enable_comments
        config.ENABLE_GET_SUB_COMMENTS = crawler_params.enable_sub_comments
        config.SAVE_DATA_OPTION = crawler_params.save_data_option.value
        if crawler_params.cookies:
            config.COOKIES = crawler_params.cookies
        
        # 如果是detail类型，设置帖子ID列表
        if crawler_params.crawler_type == CrawlerTypeEnum.DETAIL and crawler_params.note_ids:
            platform_config_map = {
                "xhs": "XHS_SPECIFIED_NOTE_URL_LIST",
                "dy": "DY_SPECIFIED_ID_LIST",
                "ks": "KS_SPECIFIED_ID_LIST",
                "bili": "BILI_SPECIFIED_ID_LIST",
                "wb": "WEIBO_SPECIFIED_ID_LIST",
                "tieba": "TIEBA_SPECIFIED_ID_LIST",
                "zhihu": "ZHIHU_SPECIFIED_ID_LIST",
            }
            
            platform = crawler_params.platform.value
            if platform in platform_config_map:
                config_name = platform_config_map[platform]
                setattr(config, config_name, crawler_params.note_ids)

        # 创建并启动爬虫
        crawler = CrawlerFactory.create_crawler(platform=config.PLATFORM)
        await crawler.start()

        task_status[task_id] = {
            "status": "completed",
            "message": "任务执行成功",
            "completed_at": datetime.now().isoformat(),
        }

    except Exception as e:
        task_status[task_id] = {
            "status": "failed",
            "message": f"任务执行失败: {str(e)}",
            "failed_at": datetime.now().isoformat(),
        }
    finally:
        # 清理资源
        if config.SAVE_DATA_OPTION in ["db", "sqlite"]:
            await db.close()
        # MongoDB 连接由 MongoDBStoreBase 自动管理，无需手动关闭


@app.get("/", summary="API根路径")
async def root():
    """API服务根路径"""
    return {
        "message": "MediaCrawler API Service",
        "version": "1.1.0",
        "docs_url": "/docs",
        "status": "running"
    }


@app.get("/health", summary="健康检查")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/crawler/start", summary="启动爬虫任务", response_model=TaskResponse)
async def start_crawler(
    crawler_params: CrawlerRequest,
    background_tasks: BackgroundTasks
):
    """
    启动一个爬虫任务
    
    - **platform**: 平台名称（xhs/dy/ks/bili/wb/tieba/zhihu）
    - **crawler_type**: 爬取类型（search/detail/creator）
    - **keywords**: 搜索关键词（search类型必填）
    - **note_ids**: 帖子ID列表（detail类型时使用，支持完整URL或纯ID）
    - **login_type**: 登录方式（qrcode/phone/cookie）
    - **start_page**: 起始页码，默认1
    - **max_notes_count**: 爬取帖子数量，默认15
    - **enable_comments**: 是否爬取评论，默认true
    - **enable_sub_comments**: 是否爬取二级评论，默认false
    - **save_data_option**: 数据保存方式（csv/json/sqlite/db）
    - **cookies**: Cookie字符串（cookie登录时必填）
    """
    
    # 验证参数
    if crawler_params.crawler_type == CrawlerTypeEnum.SEARCH and not crawler_params.keywords:
        raise HTTPException(
            status_code=400,
            detail="关键词搜索类型必须提供keywords参数"
        )
    
    if crawler_params.crawler_type == CrawlerTypeEnum.DETAIL and not crawler_params.note_ids:
        raise HTTPException(
            status_code=400,
            detail="详情爬取类型必须提供note_ids参数（帖子ID列表）"
        )
    
    if crawler_params.login_type == LoginTypeEnum.COOKIE and not crawler_params.cookies:
        raise HTTPException(
            status_code=400,
            detail="Cookie登录方式必须提供cookies参数"
        )
    
    # 生成任务ID
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{crawler_params.platform.value}"
    
    # 添加后台任务
    background_tasks.add_task(run_crawler_task, task_id, crawler_params)
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="任务已创建，正在启动中...",
        created_at=datetime.now().isoformat()
    )


@app.get("/api/v1/task/{task_id}", summary="查询任务状态")
async def get_task_status(task_id: str):
    """
    查询爬虫任务的执行状态
    
    - **task_id**: 任务ID
    """
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "task_id": task_id,
        **task_status[task_id]
    }


@app.get("/api/v1/tasks", summary="获取所有任务列表")
async def get_all_tasks():
    """获取所有任务的状态列表"""
    tasks = []
    for task_id, status in task_status.items():
        tasks.append({
            "task_id": task_id,
            **status
        })
    return {
        "total": len(tasks),
        "tasks": tasks
    }


@app.post("/api/v1/database/init", summary="初始化数据库")
async def init_database(request: InitDbRequest):
    """
    初始化数据库表结构
    
    - **db_type**: 数据库类型（sqlite 或 mysql）
    """
    try:
        if request.db_type not in ["sqlite", "mysql"]:
            raise HTTPException(
                status_code=400,
                detail="数据库类型只支持 sqlite 或 mysql"
            )
        
        await db.init_db(request.db_type)
        
        return {
            "status": "success",
            "message": f"数据库 {request.db_type} 初始化成功",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"数据库初始化失败: {str(e)}"
        )


@app.get("/api/v1/platforms", summary="获取支持的平台列表")
async def get_platforms():
    """获取所有支持的平台列表及说明"""
    return {
        "platforms": [
            {"code": "xhs", "name": "小红书", "features": ["搜索", "详情", "创作者"]},
            {"code": "dy", "name": "抖音", "features": ["搜索", "详情", "创作者"]},
            {"code": "ks", "name": "快手", "features": ["搜索", "详情", "创作者"]},
            {"code": "bili", "name": "哔哩哔哩", "features": ["搜索", "详情", "创作者"]},
            {"code": "wb", "name": "微博", "features": ["搜索", "详情", "创作者"]},
            {"code": "tieba", "name": "百度贴吧", "features": ["搜索", "详情", "创作者"]},
            {"code": "zhihu", "name": "知乎", "features": ["搜索", "详情", "创作者"]},
        ]
    }


@app.get("/api/v1/config", summary="获取当前配置")
async def get_config():
    """获取当前的配置信息"""
    return {
        "platform": config.PLATFORM,
        "crawler_type": config.CRAWLER_TYPE,
        "keywords": config.KEYWORDS,
        "login_type": config.LOGIN_TYPE,
        "save_data_option": config.SAVE_DATA_OPTION,
        "enable_comments": config.ENABLE_GET_COMMENTS,
        "enable_sub_comments": config.ENABLE_GET_SUB_COMMENTS,
        "max_notes_count": config.CRAWLER_MAX_NOTES_COUNT,
    }


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件处理"""
    if config.SAVE_DATA_OPTION in ["db", "sqlite"]:
        await db.close()


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """启动API服务器"""
    print("=" * 60)
    print("MediaCrawler API 服务启动中...")
    print(f"服务地址: http://{host}:{port}")
    print(f"API文档: http://{host}:{port}/docs")
    print(f"健康检查: http://{host}:{port}/health")
    print("=" * 60)
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()

