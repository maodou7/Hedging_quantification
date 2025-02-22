from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .system_status import router as system_router

app = FastAPI(
    title="量化交易系统",
    description="量化交易系统API接口",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(system_router)

@app.get("/")
async def root():
    return {"message": "量化交易系统API服务正在运行"} 