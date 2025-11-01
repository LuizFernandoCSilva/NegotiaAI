from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import logging
from typing import List, Dict

from app.infrastructure.database.connection import obter_boleto, listar_todos_boletos

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/boletos", tags=["Boletos"])


@router.get("/recentes")
async def listar_boletos_recentes(limit: int = 10) -> List[Dict]:
    try:
        boletos = listar_todos_boletos(limit=limit)
        return boletos if boletos else []
    except Exception as e:
        logger.error(f"Erro ao listar boletos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar boletos: {str(e)}")


@router.get("/download/{id_boleto}")
async def download_boleto(id_boleto: str):
    try:
        boleto = obter_boleto(id_boleto)
        
        if not boleto:
            raise HTTPException(status_code=404, detail="Boleto não encontrado")
        
        boletos_dir = os.path.join(os.getcwd(), "data", "boletos")
        filename = f"boleto_{id_boleto}.pdf"
        file_path = os.path.join(boletos_dir, filename)
        
        if not os.path.exists(file_path):
            logger.error(f"Arquivo não encontrado: {file_path}")
            raise HTTPException(status_code=404, detail="Arquivo PDF não encontrado")
        
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao fazer download do boleto {id_boleto}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar download: {str(e)}")
