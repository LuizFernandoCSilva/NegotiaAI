from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints.chat_routes import router as chat_router
from app.api.v1.endpoints.comprovante_routes_auto import router as comprovante_router
from app.api.v1.endpoints.download_boletos import router as boletos_router
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NegotiaAI - API de Negociação de Dívidas",
    description="API para interação com agente de negociação inteligente usando LLM (Google Gemini)",
    version="1.0.0",
    contact={
        "name": "LuizF",
        "email": "luiz.fernandocsilva17@gmail.com"
    },
    docs_url="/api/docs", 
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(comprovante_router)
app.include_router(boletos_router)


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "BancoAgil API - Agente de Negociação",
        "version": "1.0.0",
        "docs": "/api/docs",
        "redoc": "/api/redoc"
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)