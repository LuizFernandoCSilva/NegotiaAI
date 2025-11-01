import streamlit as st
import requests
import uuid
from datetime import datetime
import os
import re
import base64

st.set_page_config(
    page_title="ResolveBank - Negociação de Dívidas",
    page_icon="💳",
    layout="centered",
    initial_sidebar_state="expanded"
)

from dotenv import load_dotenv
load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:5000")

st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    [data-testid="stSidebar"] {
        min-width: 300px;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .agent-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    .message-content {
        margin-top: 0.5rem;
    }
    .message-time {
        font-size: 0.75rem;
        color: #666;
        margin-top: 0.25rem;
    }
    .header-container {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .download-button {
        display: inline-block;
        padding: 12px 24px;
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white !important;
        text-decoration: none;
        border-radius: 8px;
        font-weight: bold;
        font-size: 16px;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border: none;
        cursor: pointer;
    }
    .download-button:hover {
        background: linear-gradient(135deg, #45a049 0%, #3d8b40 100%);
        color: white !important;
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)


if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.user_id = str(uuid.uuid4())
    st.session_state.input_key = 0
    st.session_state.atendimento_encerrado = False

if "atendimento_encerrado" not in st.session_state:
    st.session_state.atendimento_encerrado = False
def send_message_to_api(message: str) -> dict:
    try:
        llm_config = st.session_state.get('llm_config', {})
        
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "message": message,
                "session_id": st.session_state.session_id,
                "user_id": st.session_state.user_id,
                "llm_config": llm_config
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("success") and result.get("data", {}).get("session_id"):
            new_session_id = result["data"]["session_id"]
            if new_session_id != st.session_state.session_id:
                st.session_state.session_id = new_session_id
        
        return result
        
    except requests.exceptions.ConnectionError:
        return {
            "error": "Não foi possível conectar ao servidor. Verifique se o backend está rodando."
        }
    except requests.exceptions.Timeout:
        return {
            "error": "A requisição demorou muito tempo. Tente novamente."
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Erro na comunicação com o servidor: {str(e)}"
        }

def end_session():
    try:
        requests.post(
            f"{API_URL}/end_session",
            json={
                "session_id": st.session_state.session_id,
                "user_id": st.session_state.user_id
            },
            timeout=10
        )
    except:
        pass
    
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.user_id = str(uuid.uuid4())
    st.session_state.input_key = 0
    st.session_state.atendimento_encerrado = False 

def extrair_info_boleto(content: str) -> dict:
    info = {
        "tem_boleto": False,
        "id_boleto": None,
        "download_url": None,
        "valor": None,
        "vencimento": None
    }
    
    metadata_pattern = r"<!--\s*METADATA_BOLETO:\s*id=([a-f0-9\-]{36}),\s*url=(/api/v1/boletos/download/[a-f0-9\-]{36})\s*-->"
    id_boleto_pattern = r"id_boleto:\s*([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"
    download_url_pattern = r"download_url:\s*(/api/v1/boletos/download/[a-f0-9\-]{36})"
    uuid_pattern = r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"
    valor_pattern = r"R\$\s*(\d+[.,]\d{2})"
    vencimento_pattern = r"(\d{2}/\d{2}/\d{4})"
    
    metadata_match = re.search(metadata_pattern, content, re.IGNORECASE)
    
    if metadata_match:
        info["tem_boleto"] = True
        info["id_boleto"] = metadata_match.group(1)
        info["download_url"] = metadata_match.group(2)
    else:
        id_boleto_match = re.search(id_boleto_pattern, content, re.IGNORECASE)
        download_url_match = re.search(download_url_pattern, content, re.IGNORECASE)
        uuid_match = re.search(uuid_pattern, content, re.IGNORECASE)
        
        if id_boleto_match:
            info["tem_boleto"] = True
            info["id_boleto"] = id_boleto_match.group(1)
        
        if download_url_match:
            info["tem_boleto"] = True
            info["download_url"] = download_url_match.group(1)
            if not info["id_boleto"]:
                url_id = re.search(r"download/([a-f0-9\-]{36})", download_url_match.group(1))
                if url_id:
                    info["id_boleto"] = url_id.group(1)
        
        if not info["id_boleto"] and uuid_match:
            info["tem_boleto"] = True
            info["id_boleto"] = uuid_match.group(1)
    
    valor_match = re.search(valor_pattern, content, re.IGNORECASE)
    venc_match = re.search(vencimento_pattern, content, re.IGNORECASE)
    
    if valor_match:
        info["valor"] = valor_match.group(1)
    
    if venc_match:
        info["vencimento"] = venc_match.group(1)
    
    return info

def download_boleto(id_boleto: str, filename: str = None):
    try:
        response = requests.get(
            f"{API_URL}/api/v1/boletos/download/{id_boleto}",
            timeout=30
        )
        
        if response.status_code == 200:
            if not filename:
                filename = f"boleto_{id_boleto[:8]}.pdf"
            
            b64 = base64.b64encode(response.content).decode()
            href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-button">📥 Baixar Boleto PDF</a>'
            return href, response.content
        else:
            st.error(f"Erro ao baixar boleto: {response.status_code}")
            return None, None
    except Exception as e:
        st.error(f"Erro ao fazer download: {str(e)}")
        return None, None

def display_message(role: str, content: str, timestamp: str = None):
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M")
    
    if role == "system":
        st.markdown(f"""
            <div style="background-color: #ffe5e5; border: 2px solid #ff6b6b; padding: 15px; border-radius: 10px; margin: 20px 0; text-align: center;">
                <div style="color: #d63031; font-weight: bold; font-size: 1.1em;">
                    {content}
                </div>
                <div style="color: #999; font-size: 0.8em; margin-top: 5px;">{timestamp}</div>
            </div>
        """, unsafe_allow_html=True)
        return
    
    content_limpo = re.sub(r"<!--\s*METADATA_BOLETO:.*?-->", "", content, flags=re.DOTALL)
    content_limpo = re.sub(r"Para baixar o PDF do boleto, use o link abaixo:\s*", "", content_limpo, flags=re.IGNORECASE)
    content_limpo = re.sub(r"id_boleto:\s*[a-f0-9\-]{36}\s*", "", content_limpo, flags=re.IGNORECASE)
    content_limpo = re.sub(r"download_url:\s*/api/v1/boletos/download/[a-f0-9\-]{36}\s*", "", content_limpo, flags=re.IGNORECASE)
    content_limpo = content_limpo.strip()
    
    icon = "👤" if role == "user" else "🤖"
    css_class = "user-message" if role == "user" else "agent-message"
    label = "Você" if role == "user" else "Agente ResolveBank"
    
    st.markdown(f"""
        <div class="chat-message {css_class}">
            <strong>{icon} {label}</strong>
            <div class="message-content">{content_limpo}</div>
            <div class="message-time">{timestamp}</div>
        </div>
    """, unsafe_allow_html=True)
    
    if role == "agent":
        info_boleto = extrair_info_boleto(content)
        if info_boleto["tem_boleto"] and info_boleto["id_boleto"]:
            st.markdown("---")
            
            st.markdown("""
                <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border-left: 5px solid #4caf50; margin: 10px 0;">
                    <h3 style="color: #2e7d32; margin-top: 0;">🧾 Boleto Gerado com Sucesso!</h3>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.markdown("#### 📋 Informações do Boleto")
                if info_boleto["valor"]:
                    st.markdown(f"💰 **Valor:** R$ {info_boleto['valor']}")
                if info_boleto["vencimento"]:
                    st.markdown(f"📅 **Vencimento:** {info_boleto['vencimento']}")
                st.markdown(f"🆔 **ID:** `{info_boleto['id_boleto'][:16]}...`")
            
            with col2:
                st.markdown("#### 📥 Download")
                
                href, pdf_content = download_boleto(info_boleto['id_boleto'])
                if href:
                    st.markdown(href, unsafe_allow_html=True)
                    st.success("✅ Clique no botão acima para baixar")
                else:
                    st.error("❌ Erro ao preparar download")
                
                download_link = f"{API_URL}/api/v1/boletos/download/{info_boleto['id_boleto']}"
                st.markdown(f"<a href='{download_link}' target='_blank' style='font-size: 0.9em;'>🔗 Ou clique aqui para link direto</a>", unsafe_allow_html=True)
            
            st.markdown("---")

st.markdown("""
    <div class="header-container">
        <h1>💳 ResolveBank</h1>
        <p>Negociação de Dívidas</p>
    </div>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("ℹ️ Informações")
    st.markdown(f"""
    **ID da Sessão:**  
    `{st.session_state.session_id[:8]}...`
    
    **Mensagens trocadas:**  
    {len(st.session_state.messages)}
    
    **Status:**  
    🟢 Conectado
    """)
    
    if st.button("🔄 Nova Conversa", use_container_width=True):
        end_session()
        st.rerun()
    
    st.divider()
    
    with st.expander("⚙️ Configurações Avançadas", expanded=False):
        st.markdown("**Parâmetros do LLM**")
        
        st.markdown("**Modelo:**")
        st.code("gemini-2.0-flash-exp", language=None)
        st.caption("📌 Modelo fixo otimizado para negociação")
        
        st.markdown("---")
        
        temperature = st.slider(
            "Temperature:",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            help="Controla a criatividade das respostas (0 = mais conservador, 1 = mais criativo)"
        )
        
        max_tokens = st.number_input(
            "Max Tokens:",
            min_value=256,
            max_value=8192,
            value=2048,
            step=256,
            help="Número máximo de tokens na resposta"
        )
        
        st.session_state.llm_config = {
            "model": "gemini-2.0-flash-exp",
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        st.info(f"🌡️ Temp: {temperature}\n\n📊 Tokens: {max_tokens}")
    
    st.divider()
    
    st.markdown("### 📄 Enviar Comprovante")
    st.markdown("Envie o comprovante de pagamento. O sistema identificará automaticamente seus dados.")
    
    uploaded_file = st.file_uploader(
        "Selecione o comprovante:",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Formatos aceitos: PDF, PNG, JPG (até 5MB)"
    )
    
    if st.button("📤 Enviar Comprovante", use_container_width=True, disabled=not uploaded_file):
        with st.spinner("🔍 Extraindo e validando dados do comprovante..."):
            try:
                files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {'session_id': st.session_state.session_id}
                
                response = requests.post(
                    f"{API_URL}/comprovantes/upload-auto",
                    files=files,
                    data=data,
                    timeout=90
                )
                
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        data = result.get('data', {})
                        st.success("✅ Comprovante validado e enviado com sucesso!")
                        st.info(f"📋 CPF identificado: {data.get('cpf_identificado', 'N/A')}")
                        st.info(f"💰 Valor do boleto: R$ {data.get('valor_boleto', 0):.2f}")
                        
                        try:
                            cpf = data.get('cpf_identificado', '')
                            valor = data.get('valor_boleto', 0)
                            mensagem_upload = f"[SISTEMA] Comprovante recebido com sucesso. CPF: {cpf}, Valor: R$ {valor:.2f}"
                            
                            chat_response = requests.post(
                                f"{API_URL}/chat",
                                json={
                                    "message": mensagem_upload,
                                    "session_id": st.session_state.session_id,
                                    "user_id": st.session_state.user_id
                                }
                            )
                            
                            if chat_response.status_code == 200:
                                chat_result = chat_response.json()
                                if chat_result.get('success'):
                                    agent_message = chat_result['data']['response']
                                    st.session_state.messages.append({"role": "user", "content": "📎 [Comprovante enviado]"})
                                    st.session_state.messages.append({"role": "assistant", "content": agent_message})
                                    st.rerun()
                        except Exception as e_chat:
                            st.warning(f"⚠️ Comprovante salvo, mas não foi possível notificar o agente: {str(e_chat)}")
                            
                    else:
                        error = result.get('error', {})
                        st.error(f"{error.get('message', 'Erro ao enviar')}")
                        
                        if error.get('code') == 'VALIDACAO_FALHOU':
                            detalhes = error.get('details', {})
                            with st.expander("Ver detalhes da validação"):
                                st.write(f"**Score:** {detalhes.get('score', 'N/A')}")
                                validacoes = detalhes.get('validacoes', {})
                                for campo, info in validacoes.items():
                                    status = "✅" if info.get('valido') else "❌"
                                    st.write(f"{status} **{campo}:** {info.get('mensagem')}")
                                    
                elif response.status_code == 404:
                    try:
                        error_data = response.json()
                        detail = error_data.get('detail', {})
                        if isinstance(detail, dict):
                            error_message = detail.get('message', 'CPF não identificado no comprovante')
                            error_code = detail.get('code', 'ERRO_UPLOAD')
                        else:
                            error_message = str(detail)
                            error_code = 'ERRO_UPLOAD'
                        
                        # Notificar o agente sobre o erro para resposta contextualizada
                        if error_code == 'CPF_NAO_ENCONTRADO':
                            mensagem_erro = "[SISTEMA] O usuário tentou enviar um comprovante mas não foi possível identificar um CPF válido no documento. O documento pode estar ilegível, corrompido ou não ser um comprovante de pagamento válido. Por favor, oriente o usuário a verificar o arquivo."
                        elif error_code == 'SEM_BOLETO':
                            mensagem_erro = "[SISTEMA] O usuário tentou enviar um comprovante mas não há boletos cadastrados para o CPF identificado. Informe que ele precisa primeiro gerar um boleto antes de enviar o comprovante de pagamento."
                        else:
                            mensagem_erro = f"[SISTEMA] Erro ao processar comprovante: {error_message}"
                        
                        chat_response = requests.post(
                            f"{API_URL}/chat",
                            json={
                                "message": mensagem_erro,
                                "session_id": st.session_state.session_id,
                                "user_id": st.session_state.user_id
                            }
                        )
                        
                        if chat_response.status_code == 200:
                            chat_result = chat_response.json()
                            if chat_result.get('success'):
                                agent_message = chat_result['data']['response']
                                st.session_state.messages.append({"role": "user", "content": "📎 [Tentativa de envio de comprovante]"})
                                st.session_state.messages.append({"role": "assistant", "content": agent_message})
                                st.rerun()
                        else:
                            # Fallback se o agente não responder
                            st.error(f"❌ {error_message}")
                            if error_code == 'CPF_NAO_ENCONTRADO':
                                st.warning("Não foi possível identificar um CPF válido no documento. Verifique se o arquivo está legível e se é um comprovante válido.")
                            elif error_code == 'SEM_BOLETO':
                                st.info("💡 Você precisa primeiro gerar um boleto antes de enviar o comprovante de pagamento.")
                        
                    except Exception as e_parse:
                        st.error("❌ Não foi possível processar o documento enviado.")
                        st.warning("O arquivo pode estar corrompido ou não ser um comprovante válido.")
                        
                elif response.status_code == 403:
                    try:
                        error_data = response.json()
                        detail = error_data.get('detail', {})
                        if isinstance(detail, dict):
                            message = detail.get('message', 'CPF do comprovante não corresponde à sessão')
                            cpf_esperado = detail.get('cpf_esperado', 'N/A')
                            cpf_recebido = detail.get('cpf_recebido', 'N/A')
                            
                            st.error(f" {message}")
                            st.warning("**Atenção:** Este comprovante pertence a outro CPF!")
                            with st.expander("Ver detalhes"):
                                st.write(f"**CPF da sua negociação:** {cpf_esperado}")
                                st.write(f"**CPF do comprovante enviado:** {cpf_recebido}")
                                st.write("\n**Dica:** Verifique se você enviou o arquivo correto.")
                            
                            mensagem_fraude = f"[SISTEMA] Tentativa de envio de comprovante incorreto. CPF do comprovante ({cpf_recebido}) não corresponde ao CPF autenticado ({cpf_esperado})."
                            
                            chat_response = requests.post(
                                f"{API_URL}/chat",
                                json={
                                    "message": mensagem_fraude,
                                    "session_id": st.session_state.session_id,
                                    "user_id": st.session_state.user_id
                                }
                            )
                            
                            if chat_response.status_code == 200:
                                chat_result = chat_response.json()
                                if chat_result.get('success'):
                                    agent_message = chat_result['data']['response']
                                    st.session_state.messages.append({"role": "user", "content": "📎 [Comprovante incorreto enviado]"})
                                    st.session_state.messages.append({"role": "assistant", "content": agent_message})
                                    st.rerun()
                        else:
                            st.error(f" {detail}")
                    except Exception as e:
                        st.error("Este comprovante não corresponde ao CPF da sua negociação.")
                elif response.status_code == 422:
                    result = response.json()
                    error_message = result.get('error', {}).get('message', 'Validação falhou')
                    st.error(f" {error_message}")
                    
                    try:
                        mensagem_validacao = f"[SISTEMA] Comprovante enviado mas falhou na validação: {error_message}"
                        
                        chat_response = requests.post(
                            f"{API_URL}/chat",
                            json={
                                "message": mensagem_validacao,
                                "session_id": st.session_state.session_id,
                                "user_id": st.session_state.user_id
                            }
                        )
                        
                        if chat_response.status_code == 200:
                            chat_result = chat_response.json()
                            if chat_result.get('success'):
                                agent_message = chat_result['data']['response']
                                st.session_state.messages.append({"role": "user", "content": "📎 [Comprovante inválido]"})
                                st.session_state.messages.append({"role": "assistant", "content": agent_message})
                                st.rerun()
                    except Exception as e_chat:
                        pass
                        
                else:
                    try:
                        error_data = response.json()
                        detail = error_data.get('detail', {})
                        error_msg = detail if isinstance(detail, str) else str(detail)
                        
                        # Notificar o agente sobre o erro genérico
                        mensagem_erro_generico = f"[SISTEMA] Erro ao processar comprovante enviado pelo usuário (código {response.status_code}): {error_msg}"
                        
                        chat_response = requests.post(
                            f"{API_URL}/chat",
                            json={
                                "message": mensagem_erro_generico,
                                "session_id": st.session_state.session_id,
                                "user_id": st.session_state.user_id
                            }
                        )
                        
                        if chat_response.status_code == 200:
                            chat_result = chat_response.json()
                            if chat_result.get('success'):
                                agent_message = chat_result['data']['response']
                                st.session_state.messages.append({"role": "user", "content": "📎 [Erro ao enviar comprovante]"})
                                st.session_state.messages.append({"role": "assistant", "content": agent_message})
                                st.rerun()
                        else:
                            # Fallback
                            st.error(f"❌ Erro ao enviar: {error_msg}")
                            st.warning("⚠️ O documento não pôde ser processado. Tente novamente.")
                    except:
                        st.error(f"❌ Erro ao enviar comprovante (código {response.status_code})")
                        st.warning("⚠️ O documento não pôde ser processado. Tente novamente.")
                    
            except requests.exceptions.Timeout:
                st.error("⏱️ Tempo limite excedido ao enviar o documento.")
                st.info("O servidor demorou muito para responder. Tente novamente em alguns instantes.")
                
            except requests.exceptions.ConnectionError:
                st.error("🔌 Erro de conexão com o servidor.")
                st.info("Verifique sua conexão com a internet e se o servidor está ativo.")
                
            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")
                st.warning("Não foi possível processar o documento enviado.")

    st.divider()
    
    st.markdown("""
    ### Como funciona?
    
    1. Digite sua mensagem
    2. O agente irá te guiar
    3. Forneça seu CPF quando solicitado
    4. Negocie sua dívida
    5. Receba o boleto
    6. Envie o comprovante (sidebar) 👈
    
    ---
    
    ### Precisa de ajuda?
    
    O agente pode ajudar você com:
    - ✅ Consulta de dívidas
    - ✅ Negociação de valores
    - ✅ Parcelamento
    - ✅ Emissão de boletos
    - ✅ Envio de comprovantes
    """)

chat_container = st.container()

with chat_container:
    if len(st.session_state.messages) == 0:
        st.info("👋 Olá! Sou o agente de negociação do ResolveBank. Digite uma mensagem para começar!")
    else:
        for msg in st.session_state.messages:
            display_message(msg["role"], msg["content"], msg.get("timestamp"))
    
    if st.session_state.atendimento_encerrado:
        st.markdown("""
            <div style="background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 5px;">
                <h4 style="color: #856404; margin: 0 0 10px 0;">⚠️ Atendimento Encerrado</h4>
                <p style="color: #856404; margin: 0;">
                    Este atendimento foi finalizado. Para iniciar uma nova negociação, 
                    clique no botão <strong>'Nova Conversa'</strong> na barra lateral esquerda.
                </p>
            </div>
        """, unsafe_allow_html=True)

st.divider()

user_input = st.chat_input(
    "Digite sua mensagem..." if not st.session_state.atendimento_encerrado else "Atendimento encerrado. Use 'Nova Conversa' para continuar.",
    disabled=st.session_state.atendimento_encerrado
)

if user_input and user_input.strip():
    if st.session_state.atendimento_encerrado:
        st.warning("Este atendimento foi encerrado. Por favor, inicie uma nova conversa usando o botão 'Nova Conversa' na barra lateral.")
    else:
        timestamp = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })
        
        with st.spinner("Aguarde, o agente está processando..."):
            response = send_message_to_api(user_input)
            
            if "success" not in response:
                st.error(f"{response.get('error', 'Erro desconhecido')}")
            elif not response.get("success", False):
                error_info = response.get("error", {})
                error_msg = error_info.get("message", "Erro desconhecido") if isinstance(error_info, dict) else str(error_info)
                st.error(f"{error_msg}")
            else:
                data = response.get("data", {})
                agent_response = data.get("response", "Desculpe, não consegui processar sua mensagem.")
                
                if data.get("encerrado", False):
                    st.session_state.atendimento_encerrado = True
                    st.session_state.messages.append({
                        "role": "system",
                        "content": "🔒 **Atendimento Encerrado** - Para nova negociação, clique em 'Nova Conversa'",
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
                
                st.session_state.messages.append({
                    "role": "agent",
                    "content": agent_response,
                    "timestamp": datetime.now().strftime("%H:%M")
                })
        
        st.session_state.input_key += 1
        
        st.rerun()

st.divider()
st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.85rem; padding: 1rem 0;">
        <p>ResolveBank - Agente de Negociação de Dívidas | Desenvolvido com ❤️ usando Streamlit</p>
        <p>ID da Sessão: {session_id}</p>
    </div>
""".format(session_id=st.session_state.session_id[:16]), unsafe_allow_html=True)
