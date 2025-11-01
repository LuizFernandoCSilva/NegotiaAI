import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form
from typing import Optional
from app.utils.response import ok_response, error_response
import logging

router = APIRouter(prefix="/comprovantes", tags=["Comprovantes"])
logger = logging.getLogger(__name__)


@router.post(
    '/upload-auto',
    response_model=dict,
    summary="Upload automático de comprovante",
    description="Extrai CPF automaticamente do comprovante via OCR e valida o pagamento"
)
async def upload_comprovante_automatico(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Rota inteligente: extrai CPF automaticamente do comprovante via OCR.
    O usuário só envia o arquivo, o sistema identifica tudo!
    
    Se session_id for fornecido, valida que o CPF do comprovante corresponde
    ao CPF autenticado na sessão (segurança contra fraude).
    """
    import traceback
    
    try:
        if not file.filename:
            logger.error("ERRO: Filename vazio!")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O comprovante precisa ter um nome de arquivo válido."
            )
        contents = await file.read()
        tamanho = len(contents)
        
        
        if tamanho > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo muito grande. Máximo: 5MB."
            )

        import tempfile
        from pathlib import Path
        
        suffix = Path(file.filename).suffix or '.pdf'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name
        from app.services.comprovante_service import processar_comprovante_from_path
        
        resultado = processar_comprovante_from_path(temp_path, file.filename, validar=True)
        

        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao processar comprovante."
            )
        
        if session_id:
            from app.services.agent_service import get_authenticated_cpf
            
            cpf_sessao = await get_authenticated_cpf(session_id)
            cpf_comprovante = resultado.get('cpf_identificado')
            
            
            if cpf_sessao and cpf_comprovante:
                cpf_sessao_limpo = ''.join(filter(str.isdigit, cpf_sessao))
                cpf_comprovante_limpo = ''.join(filter(str.isdigit, cpf_comprovante))
                
                if cpf_sessao_limpo != cpf_comprovante_limpo:
                    try:
                        import os
                        arquivo_salvo = resultado.get('arquivo_salvo')
                        if arquivo_salvo and os.path.exists(arquivo_salvo):
                            os.unlink(arquivo_salvo)
                        
                        registro_id = resultado.get('registro_id')
                        if registro_id:
                            from app.infrastructure.database.connection import SessionLocal
                            from app.domain.models.database_models import Receipt
                            session = SessionLocal()
                            try:
                                receipt = session.query(Receipt).filter_by(id=registro_id).first()
                                if receipt:
                                    session.delete(receipt)
                                    session.commit()
                            finally:
                                session.close()
                    except Exception as cleanup_error:
                        logger.error(f"Erro ao limpar arquivo/registro: {cleanup_error}")
                    
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "message": f"ATENÇÃO: Este comprovante pertence ao CPF ***{cpf_comprovante_limpo[-3:]} (terminação {cpf_comprovante_limpo[-3:]}), mas você está negociando a dívida do CPF ***{cpf_sessao_limpo[-3:]} (terminação {cpf_sessao_limpo[-3:]}). Por favor, envie o comprovante CORRETO da SUA negociação.",
                            "code": "CPF_MISMATCH",
                            "cpf_esperado": f"***{cpf_sessao_limpo[-3:]}",
                            "cpf_recebido": f"***{cpf_comprovante_limpo[-3:]}"
                        }
                    )
                
            elif cpf_sessao:
                logger.warning("Comprovante sem CPF identificado mas sessão tem CPF autenticado")
            else:
                logger.info("Sessão sem CPF autenticado - pulando validação de segurança")
        else:
            logger.info("Upload sem session_id - pulando validação de segurança")
        
        if 'erro' in resultado:
            erro_tipo = resultado['erro']
            logger.warning(f"Erro detectado: {erro_tipo} - {resultado.get('mensagem')}")
            
            if erro_tipo == 'CPF_NAO_ENCONTRADO':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "message": resultado['mensagem'],
                        "code": "CPF_NAO_ENCONTRADO",
                        "details": resultado.get('detalhes')
                    }
                )
            elif erro_tipo == 'CPF_INVALIDO':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": resultado['mensagem'],
                        "code": "CPF_INVALIDO"
                    }
                )
            elif erro_tipo == 'SEM_BOLETO':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "message": resultado['mensagem'],
                        "code": "SEM_BOLETO"
                    }
                )
            elif erro_tipo == 'VALIDACAO_FALHOU':
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "message": resultado['mensagem'],
                        "code": "VALIDACAO_FALHOU",
                        "details": resultado.get('detalhes')
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=resultado['mensagem']
                )

        
        return ok_response({
            'message': 'Comprovante validado e recebido com sucesso!',
            'cpf_identificado': resultado.get('cpf_identificado'),
            'valor_boleto': resultado.get('valor_boleto', 0.0),
            'registro': resultado
        })

    except HTTPException:
        raise
    except Exception as e:
    
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )

