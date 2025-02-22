"""API服务器

整合所有模块的API路由，包括：
1. 市场数据API
2. 监控API
3. 交易API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .market.market_api import router as market_router
from .monitor.monitor_api import router as monitor_router
from .trading.trading_api import router as trading_router
from src.core.exchange_manager import exchange_manager

app = FastAPI(
    title="量化交易系统",
    description="""
    量化交易系统API文档
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# 设置模板目录
templates = Jinja2Templates(directory="src/templates")

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化交易所连接"""
    print("🚀 正在启动量化交易系统...")
    print("📡 初始化交易所连接...")
    await exchange_manager.initialize()
    print("✅ 交易所连接初始化完成")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """根路径显示系统状态页面"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "量化交易系统"
        }
    )

# 注册各模块的路由
app.include_router(market_router)
app.include_router(monitor_router)
app.include_router(trading_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)