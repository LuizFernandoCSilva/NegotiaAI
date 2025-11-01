from fastapi import APIRouter, HTTPException, status
from app.domain.schemas import ChatRequest, EndSessionRequest
from app.services.agent_service import (
    send_message, end_session as svc_end_session
)

from app.utils.response import ok_response, error_response

router = APIRouter(prefix="", tags=["Chat"])


@router.post(
    '/chat',
    response_model=dict,
    summary="Envia mensagem para o agente",
    description="Processa mensagem do usuário e retorna resposta do agente de negociação"
)
async def chat(request: ChatRequest):
    try:
        user_id = request.user_id
        
        response = await send_message(
            user_id=user_id,
            session_id=request.session_id or '',
            message=request.message,
            llm_config=request.llm_config
        )
        

        final_session_id = response.get('session_id') or request.session_id

        result = ok_response({
            'response': response.get('response'),
            'tool_calls': response.get('tool_calls', []),
            'encerrado': response.get('encerrado', False),  
            'session_id': final_session_id,
            'user_id': user_id
        })
        
        
        return result

    except ValueError as e:
        return error_response(
            message=str(e),
            type="VALIDATION_ERROR"
        )
    except Exception as e:
        return error_response(
            message="Ocorreu um erro interno no servidor.",
            type="INTERNAL_ERROR"
        )


@router.post(
    '/end_session',
    response_model=dict,
    summary="Encerra sessão do usuário",
    description="Finaliza a sessão de conversação do usuário"
)
async def end_session(request: EndSessionRequest):
    
    try:
        ok = await svc_end_session(
            app_name='negotiaai', 
            session_id=request.session_id, 
            user_id='usuario_web'
        )
        
        if ok:
            return ok_response({'message': 'Sessão encerrada com sucesso.'})
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sessão não encontrada."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro interno no servidor."
        )
