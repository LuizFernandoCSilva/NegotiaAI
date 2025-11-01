import uuid
import logging
import asyncio
from typing import Optional
from app.infrastructure.llm.agent import runner
from app.core.config import AppConfig
from app.core.config import LLMConfig as ServerLLMConfig
from app.domain.schemas.chat_schemas import LLMConfig as RequestLLMConfig

logger = logging.getLogger(__name__)


class SessionManager:
    
    def __init__(self):
        self._sessions = set()
        self._session_users: dict[str, str] = {}
        self._ended_sessions = set()
    
    def add(self, session_id: str, user_id: str | None = None):
        self._sessions.add(session_id)
        if user_id:
            self._session_users[session_id] = user_id
    
    def remove(self, session_id: str):
        self._sessions.discard(session_id)
        self._session_users.pop(session_id, None)
        self._ended_sessions.discard(session_id)
    
    def has(self, session_id: str) -> bool:
        return session_id in self._sessions
    
    def clear(self):
        self._sessions.clear()
        self._session_users.clear()
        self._ended_sessions.clear()

    def get_user(self, session_id: str) -> str | None:
        return self._session_users.get(session_id)
    
    def mark_ended(self, session_id: str):
        """Marca uma sessão como encerrada"""
        self._ended_sessions.add(session_id)
    
    def is_ended(self, session_id: str) -> bool:
        """Verifica se uma sessão foi encerrada"""
        return session_id in self._ended_sessions


session_manager = SessionManager()

_llm_config_lock = asyncio.Lock()


async def ensure_session(app_name: str, session_id: str = None, user_id: str = 'usuario_web') -> str:
    """
    Garante que existe uma sessão válida. 
    Se session_id for None ou não existir, cria uma nova.
    Retorna o session_id (existente ou novo).
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    
    resolved_user = session_manager.get_user(session_id) or user_id

    try:
        await runner.session_service.get_session(
            app_name=app_name,
            session_id=session_id,
            user_id=resolved_user,
        )
        session_manager.add(session_id, resolved_user)
        return session_id
    except Exception:
        try:
            await runner.session_service.create_session(
                app_name=app_name,
                session_id=session_id,
                user_id=resolved_user,
            )
            session_manager.add(session_id, resolved_user)
            return session_id
        except Exception as e:
            if "already exists" in str(e).lower():
                session_manager.add(session_id, resolved_user)
                return session_id
            raise


async def end_session(app_name: str, session_id: str, user_id: str) -> bool:
    """
    Encerra sessão se existir. 
    Retorna True se foi encerrada, False se não existia.
    """
    if session_manager.has(session_id):
        await runner.session_service.delete_session(
            app_name=app_name,
            session_id=session_id,
            user_id=user_id
        )
        session_manager.remove(session_id)
        return True
    return False


async def get_authenticated_cpf(session_id: str, user_id: str | None = None) -> str | None:
    """
    Busca o CPF autenticado na sessão atual.
    Percorre o histórico da sessão procurando pela chamada de autenticar_cliente.
    
    Args:
        session_id: ID da sessão
        user_id: ID do usuário (opcional)
        
    Returns:
        CPF autenticado ou None se não houver autenticação
    """
    try:
        resolved_user = user_id or session_manager.get_user(session_id) or 'usuario_web'
        
        session = await runner.session_service.get_session(
            app_name=AppConfig.APP_NAME,
            session_id=session_id,
            user_id=resolved_user,
        )
        
        if not session:
            logger.warning(f"Sessão não encontrada: {session_id}")
            return None
        
        if hasattr(session, 'content') and session.content:
            for message in session.content:
                if hasattr(message, 'parts'):
                    for part in message.parts:
                        if hasattr(part, 'function_response'):
                            func_response = part.function_response
                            if hasattr(func_response, 'name') and func_response.name == 'autenticar_cliente':
                                if hasattr(func_response, 'response') and func_response.response:
                                    response_data = func_response.response
                                    if isinstance(response_data, dict):
                                        data = response_data.get('data', {})
                                        if data.get('autenticado') and data.get('cpf'):
                                            cpf = data.get('cpf')
                                            logger.info(f"CPF autenticado encontrado na sessão: {cpf}")
                                            return cpf
        
        logger.warning(f"Nenhum CPF autenticado encontrado na sessão {session_id}")
        return None
        
    except Exception as e:
        logger.error(f"Erro ao buscar CPF da sessão: {e}", exc_info=True)
        return None


def _parse_events(events):
    """
    Processa eventos retornados por runner.run.
    Retorna dict com 'response' (texto), 'tool_calls' (lista de nomes de ferramentas) e 'encerrado' (bool).
    """
    resposta = None
    tool_calls = []
    encerrado = False
    boleto_info = None  # Armazena informações do boleto gerado
    
    for event in events:
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts') and event.content.parts:
                for part in event.content.parts:
                    # Captura function_call
                    if hasattr(part, 'function_call') and part.function_call:
                        if hasattr(part.function_call, 'name') and part.function_call.name:
                            tool_name = part.function_call.name
                            tool_calls.append(tool_name)
                            if tool_name == 'encerrar_atendimento':
                                encerrado = True
                    
                    # Captura function_response de gerar_boleto_pdf_bytes
                    if hasattr(part, 'function_response') and part.function_response:
                        logger.info(f"🔍 Detectado function_response: {getattr(part.function_response, 'name', 'UNKNOWN')}")
                        if hasattr(part.function_response, 'name') and part.function_response.name == 'gerar_boleto_pdf_bytes':
                            logger.info(f"✅ É gerar_boleto_pdf_bytes!")
                            if hasattr(part.function_response, 'response') and part.function_response.response:
                                        response_data = part.function_response.response
                                        
                                        data = {}
                                        if isinstance(response_data, dict):
                                            data = response_data.get('data', {})
                                        else:
                                            try:
                                                import json
                                                parsed = json.loads(response_data)
                                                if isinstance(parsed, dict):
                                                    data = parsed.get('data', {})
                                            except Exception:
                                                pass

                                        if data.get('id_boleto') and data.get('download_url'):
                                            boleto_info = {
                                                'id_boleto': data['id_boleto'],
                                                'download_url': data['download_url']
                                            }
                                            logger.info(f"Boleto capturado: {boleto_info['id_boleto']}")
                    
                    # Captura texto da resposta
                    if hasattr(part, 'text') and part.text:
                        text = part.text.strip()
                        if text and not text.startswith('```tool_outputs'):
                            resposta = text
    
    # Se boleto foi gerado e não está na resposta, injeta as informações
    if boleto_info and resposta:
        if 'id_boleto:' not in resposta and 'download_url:' not in resposta:
            # Adiciona as informações após "Boleto gerado com sucesso!"
            if 'Boleto gerado com sucesso' in resposta:
                injection = f"\n\nid_boleto: {boleto_info['id_boleto']}\ndownload_url: {boleto_info['download_url']}\n"
                resposta = resposta + injection
                logger.info(f"Metadados do boleto injetados na resposta")
    
    return {
        'response': resposta or 'O agente não retornou uma resposta final.',
        'tool_calls': tool_calls,
        'encerrado': encerrado
    }


async def send_message(user_id: str, session_id: str, message: str, llm_config: Optional[RequestLLMConfig] = None) -> dict:
    """
    Envia mensagem ao agente e retorna o resultado.

    Comportamento:
    - Garante que a sessão exista (cria se necessário).
    - Se `llm_config` for fornecido, aplica validações mínimas e aplica a configuração
      apenas para esta execução (restaura em seguida).
    - Protege a alteração temporária com um lock assíncrono para evitar race conditions.

    Retorna dicionário com chaves: 'response', 'tool_calls', 'encerrado', 'session_id'.
    """
    import uuid
    from google.genai import types
    from google.adk.errors.already_exists_error import AlreadyExistsError

    if session_id and session_manager.is_ended(session_id):
        return {
            "response": "Este atendimento foi encerrado. Por favor, inicie uma nova conversa.",
            "encerrado": True,
            "session_id": session_id,
        }

    if not session_id:
        session_id = str(uuid.uuid4())

    try:
        try:
            await runner.session_service.create_session(
                app_name=AppConfig.APP_NAME,
                session_id=session_id,
                user_id=user_id,
            )
        except AlreadyExistsError:
            pass
        except Exception as e:
            logger.warning(f"Erro ao criar sessão (continuando): {e}")

        user_msg = types.Content(role="user", parts=[types.Part(text=message)])

        per_call_cfg: Optional[types.GenerateContentConfig] = None
        if llm_config is not None:
            try:
                incoming = llm_config.dict() if hasattr(llm_config, "dict") else dict(llm_config)
            except Exception:
                incoming = {}

            def _to_float(v, default):
                try:
                    return float(v)
                except Exception:
                    return default

            def _to_int(v, default):
                try:
                    return int(v)
                except Exception:
                    return default

            defaults = {
                "model": getattr(ServerLLMConfig, "MODEL", None),
                "temperature": getattr(ServerLLMConfig, "TEMPERATURE", 0.0),
                "max_output_tokens": getattr(ServerLLMConfig, "MAX_TOKENS", 2048),
            }

            temp = _to_float(incoming.get("temperature", defaults["temperature"]), defaults["temperature"])
            temp = max(0.0, min(1.0, temp))

            max_out = incoming.get("max_output_tokens", incoming.get("max_tokens", defaults["max_output_tokens"]))
            max_out = _to_int(max_out, defaults["max_output_tokens"]) or defaults["max_output_tokens"]
            max_allowed = getattr(ServerLLMConfig, "MAX_TOKENS", 4096)
            max_out = max(1, min(max_allowed, max_out))

            model = incoming.get("model") or defaults["model"]
            whitelist = getattr(AppConfig, "llm_allowed_models", None)
            if whitelist is not None and model not in whitelist:
                logger.warning(f"Modelo '{model}' não permitido; usando '{defaults['model']}'")
                model = defaults["model"]

            try:
                per_call_cfg = types.GenerateContentConfig(temperature=temp, max_output_tokens=max_out)
            except Exception as e:
                logger.warning(f"Não foi possível criar GenerateContentConfig: {e}")

        events_list = []
        if per_call_cfg is not None:
            try:
                async with _llm_config_lock:
                    prev = getattr(runner.agent, "generate_content_config", None)
                    try:
                        setattr(runner.agent, "generate_content_config", per_call_cfg)
                        async for ev in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_msg):
                            events_list.append(ev)
                    finally:
                        try:
                            setattr(runner.agent, "generate_content_config", prev)
                        except Exception:
                            logger.exception("Erro ao restaurar generate_content_config")
            except Exception as e:
                logger.error(f"Erro executando runner com config personalizada: {e}", exc_info=True)
                async for ev in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_msg):
                    events_list.append(ev)
        else:
            async for ev in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_msg):
                events_list.append(ev)

        result = _parse_events(events_list)
        result["session_id"] = session_id
        session_manager.add(session_id, user_id)

        if result.get("encerrado"):
            session_manager.mark_ended(session_id)
            logger.info(f"Sessão {session_id} marcada como encerrada")

        return result

    except Exception:
        logger.exception("Erro no send_message")
        fallback_session = str(uuid.uuid4())
        return {
            "response": "Olá! Tenho uma proposta para quitarmos sua dívida do cartão ResolveBank. Podemos conversar?",
            "tool_calls": [],
            "session_id": fallback_session,
        }


