import logging
from typing import Any, Dict, Optional
import asyncio
import io
import os
from datetime import datetime, timedelta
import uuid
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
from reportlab.lib import colors

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

from app.infrastructure.database.connection import (
    init_db,
    listar_boletos as listar_boletos_db,
    obter_cliente,
    obter_plano_a_vista,
    obter_plano_por_parcelas,
    obter_plano_por_valor,
    obter_planos,
    registrar_boleto,
)
from app.utils.cpfValidate import validar_cpf, normalizar_cpf
from app.utils.response import criar_response_error, criar_response_ok
from app.core.config import AppConfig, LLMConfig  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
init_db()

APP_NAME = AppConfig.APP_NAME
BASE_DIR = AppConfig.PROMPTS_DIR

llm_model = LLMConfig.MODEL  

def _validar_e_normalizar_cpf(cpf: Optional[str]) -> Dict[str, Any]:
    if not cpf:
        return {"ok": False, "error": criar_response_error("CPF não informado.", "CPF_EMPTY")}
    if not validar_cpf(cpf):
        return {"ok": False, "error": criar_response_error("CPF inválido.", "INVALID_CPF")}
    cpf_limpo = normalizar_cpf(cpf)
    return {"ok": True, "cpf": cpf_limpo}

async def autenticar_cliente(cpf: str) -> Dict[str, Any]:
    v = _validar_e_normalizar_cpf(cpf)
    if not v["ok"]:
        return v["error"]

    cpf_limpo = v["cpf"]

    cliente = obter_cliente(cpf_limpo)

    if not cliente:
        data = {
            "autenticado": False,
            "cpf": cpf_limpo,
            "nome": None,
            "mensagem": "CPF não encontrado na base do ResolveBank."
        }
        return criar_response_ok(data)

    data = {
        "autenticado": True,
        "cpf": cpf_limpo,
        "nome": cliente.get("nome"),
        "mensagem": f"Autenticado com sucesso como {cliente.get('nome')}."
    }
    return criar_response_ok(data)


async def consultar_divida(cpf: str) -> Dict[str, Any]:
    v = _validar_e_normalizar_cpf(cpf)
    if not v["ok"]:
        return v["error"]

    cpf_limpo = v["cpf"]
    
    cliente = obter_cliente(cpf_limpo)

    if not cliente:
        data = {
            "nome": "Cliente não encontrado",
            "divida_total": 0.0,
            "perfil": "desconhecido"
        }
        return criar_response_ok(data)

    data = {
        "nome": cliente.get("nome"),
        "divida_total": float(cliente.get("divida_total", 0.0)),
        "perfil": cliente.get("perfil", "desconhecido")
    }
    return criar_response_ok(data)


async def proposta_avista(cpf: str) -> Dict[str, Any]:
    v = _validar_e_normalizar_cpf(cpf)
    if not v["ok"]:
        return v["error"]

    cpf_limpo = v["cpf"]
    proposta = obter_plano_a_vista(cpf_limpo)

    if not proposta:
        data = {
            "id_plano": "nenhum",
            "parcelas": 1,
            "valor_parcela": 0.0,
            "total_pago": 0.0,
            "desconto_percent": 0.0,
        }
        return criar_response_ok(data)

    data = {
        "id_plano": proposta.get("id_plano"),
        "parcelas": int(proposta.get("parcelas", 1)),
        "valor_parcela": float(proposta.get("valor_parcela", 0.0)),
        "total_pago": float(proposta.get("total_pago", 0.0)),
        "desconto_percent": float(proposta.get("desconto_percent", 0.0)),
    }
    return criar_response_ok(data)


async def proposta_por_parcelas(cpf: str, qtd_parcelas: int) -> Dict[str, Any]:
    v = _validar_e_normalizar_cpf(cpf)
    if not v["ok"]:
        return v["error"]

    if not isinstance(qtd_parcelas, int) or qtd_parcelas <= 0:
        return criar_response_error("Quantidade de parcelas inválida. Deve ser inteiro positivo.", "INVALID_PARCELAS")

    cpf_limpo = v["cpf"]
    proposta = obter_plano_por_parcelas(cpf_limpo, qtd_parcelas)

    if not proposta:
        planos = obter_planos(cpf_limpo)
        if planos:
            mais_proximo = min(planos, key=lambda p: abs(int(p.get("parcelas", 0)) - qtd_parcelas))
            resultado = {
                "error": "no_exact_match",
                "requested_parcelas": qtd_parcelas,
                "closest": {
                    "id_plano": mais_proximo.get("id_plano"),
                    "parcelas": int(mais_proximo.get("parcelas", 0)),
                    "valor_parcela": float(mais_proximo.get("valor_parcela", 0.0)),
                    "total_pago": float(mais_proximo.get("total_pago", 0.0)),
                    "desconto_percent": float(mais_proximo.get("desconto_percent", 0.0)),
                },
            }
            return criar_response_ok(resultado)
        else:
            return criar_response_error("Nenhum plano disponível para este CPF.", "NO_PLANS_AVAILABLE")

    data = {
        "id_plano": proposta.get("id_plano"),
        "parcelas": int(proposta.get("parcelas", 0)),
        "valor_parcela": float(proposta.get("valor_parcela", 0.0)),
        "total_pago": float(proposta.get("total_pago", 0.0)),
        "desconto_percent": float(proposta.get("desconto_percent", 0.0)),
    }
    return criar_response_ok(data)


async def proposta_por_valor(cpf: str, valor_parcela_desejado: float) -> Dict[str, Any]:
    v = _validar_e_normalizar_cpf(cpf)
    if not v["ok"]:
        return v["error"]

    try:
        valor_solicitado = float(valor_parcela_desejado)
    except (TypeError, ValueError):
        return criar_response_error("Valor da parcela inválido.", "INVALID_VALOR")

    cpf_limpo = v["cpf"]
    plano = obter_plano_por_valor(cpf_limpo, valor_solicitado)

    if not plano:
        return criar_response_error("Não encontrei plano próximo a este valor.", "NO_PLAN_CLOSE_TO_VALUE")

    diferenca = abs(float(plano.get("valor_parcela", 0.0)) - valor_solicitado)
    if diferenca > 5.0:
        return criar_response_ok({
            "error": "no_exact_match",
            "valor_solicitado": valor_solicitado,
            "closest": {
                "id_plano": plano.get("id_plano"),
                "parcelas": int(plano.get("parcelas", 0)),
                "valor_parcela": float(plano.get("valor_parcela", 0.0)),
                "total_pago": float(plano.get("total_pago", 0.0)),
                "desconto_percent": float(plano.get("desconto_percent", 0.0))
            }
        })

    data = {
        "id_plano": plano.get("id_plano"),
        "parcelas": int(plano.get("parcelas", 0)),
        "valor_parcela": float(plano.get("valor_parcela", 0.0)),
        "total_pago": float(plano.get("total_pago", 0.0)),
        "desconto_percent": float(plano.get("desconto_percent", 0.0))
    }
    return criar_response_ok(data)


def _criar_pdf_boleto_bytes(
    cpf: str,
    linha_digitavel: str,
    valor: float,
    vencimento: datetime,
    id_boleto: Optional[str] = None,
    nome_beneficiario: str = "Empresa Exemplo",
    observacao: str = "Boleto gerado para fins de teste (fictício)."
) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left_margin = 15 * mm
    right_margin = 15 * mm
    top = height - 20 * mm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(left_margin, top, nome_beneficiario)
    c.setFont("Helvetica", 9)
    c.drawString(left_margin, top - 14, f"Documento: Boleto Fictício  •  ID: {id_boleto or '-'}")
    c.setStrokeColor(colors.grey)
    c.line(left_margin, top - 18, width - right_margin, top - 18)

    y = top - 36
    c.setFont("Helvetica", 10)
    c.drawString(left_margin, y, f"CPF do pagador: {cpf}")
    y -= 14
    c.drawString(left_margin, y, f"Vencimento: {vencimento.strftime('%d/%m/%Y') if isinstance(vencimento, datetime) else str(vencimento)}")
    y -= 14
    valor_formatado = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    c.drawString(left_margin, y, f"Valor: {valor_formatado}")
    y -= 20

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(left_margin, y, observacao)
    y -= 26

    c.setFont("Helvetica-Bold", 12)
    txt_width = c.stringWidth(linha_digitavel, "Helvetica-Bold", 12)
    c.drawString((width - txt_width) / 2, y, linha_digitavel)
    y -= 26

    try:
        barcode_value = ''.join(ch for ch in linha_digitavel if ch.isdigit())
        barcode = code128.Code128(barcode_value, barHeight=20*mm, barWidth=0.4)
        barcode_x = left_margin
        barcode_y = y - 20*mm
        barcode.drawOn(c, barcode_x, barcode_y)
    except Exception:
        c.setStrokeColor(colors.red)
        c.rect(left_margin, y - 20*mm, width - left_margin - right_margin, 20*mm, stroke=1, fill=0)

    c.setFont("Helvetica", 8)
    rodape_y = 30 * mm
    c.setFillColor(colors.grey)
    c.drawString(left_margin, rodape_y + 8, "Instruções: Este é um boleto fictício gerado para testes. Não possui validade bancária.")
    c.setFillColor(colors.black)

    c.setFont("Helvetica", 7)
    c.drawRightString(width - right_margin, rodape_y + 25, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

async def gerar_boleto_pdf_bytes(
    cpf: str,
    id_plano: str,
    linha_digitavel: str,
    valor: float,
    dias_vencimento: int = 7,
    id_boleto: Optional[str] = None
) -> Dict[str, Any]:
    v = _validar_e_normalizar_cpf(cpf)
    if not v["ok"]:
        return v["error"]
    
    cpf_limpo = v["cpf"]
    
    if not id_plano:
        return criar_response_error("ID do plano não informado.", "PLAN_ID_REQUIRED")

    id_boleto = str(uuid.uuid4())
    
    vencimento = datetime.now() + timedelta(days=dias_vencimento)
    filename = f"boleto_{id_boleto}.pdf"

    try:
        pdf_bytes = await asyncio.to_thread(
            _criar_pdf_boleto_bytes,
            cpf_limpo,
            linha_digitavel,
            valor,
            vencimento,
            id_boleto
        )

        boletos_dir = os.path.join(os.getcwd(), "data", "boletos")
        os.makedirs(boletos_dir, exist_ok=True)
        
        save_path = os.path.join(boletos_dir, filename)
        
        with open(save_path, "wb") as f:
            f.write(pdf_bytes)

        boleto_registrado = registrar_boleto(
            cpf=cpf_limpo,
            id_plano=id_plano,
            linha_digitavel=linha_digitavel,
            data_vencimento=vencimento,
            valor_total=valor,
            id_boleto=id_boleto
        )
        
        if not boleto_registrado:
            return criar_response_error("Falha ao registrar boleto no banco de dados.", "DB_ERROR")

        data = {
            "id_boleto": boleto_registrado.get("id_boleto"),
            "filename": filename,
            "download_url": f"/api/v1/boletos/download/{boleto_registrado.get('id_boleto')}",
            "valor": valor,
            "vencimento": vencimento.strftime("%d/%m/%Y"),
            "linha_digitavel": linha_digitavel,
            "mensagem": "Boleto gerado com sucesso! Use o link de download para baixar o PDF."
        }
        
        logger.info(f"Boleto gerado: {id_boleto} | CPF: {cpf_limpo} | Valor: R$ {valor:.2f}")
        return criar_response_ok(data)
        
    except Exception as e:
        logger.error(f"Erro ao gerar boleto: {e}")
        return criar_response_error(f"Erro ao gerar PDF do boleto: {str(e)}", "PDF_GENERATION_ERROR")


async def listar_boletos(cpf: str) -> Dict[str, Any]:
    v = _validar_e_normalizar_cpf(cpf)
    if not v["ok"]:
        return v["error"]

    cpf_limpo = v["cpf"]
    boletos = listar_boletos_db(cpf_limpo)

    boletos_formatados = [
        {
            "id_boleto": b.get("id_boleto"),
            "valor": float(b.get("valor_total", b.get("valor_parcela", 0.0))),
            "status": b.get("status", "pendente"),
            "vencimento": b.get("data_vencimento", ""),
            "linha_digitavel": b.get("linha_digitavel", ""),
        }
        for b in boletos or []
    ]

    return criar_response_ok({"boletos": boletos_formatados})


async def encerrar_atendimento(motivo: str = "cliente solicitou") -> Dict[str, Any]:
    mensagem = ""
    if "transfer" in motivo.lower() or "atendente" in motivo.lower():
        mensagem = "Transferindo para um atendente humano. Aguarde um momento..."
    else:
        mensagem = "Atendimento encerrado. Foi um prazer ajudá-lo!"
    
    data = {
        "encerrado": True,
        "motivo": motivo,
        "mensagem": mensagem
    }
    
    return criar_response_ok(data)

def _carregar_arquivo(nome_arquivo: str, pasta: str = None) -> str:
    if pasta:
        caminho = BASE_DIR / pasta / nome_arquivo
    else:
        caminho = BASE_DIR / nome_arquivo
    
    try:
        return caminho.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Erro ao carregar arquivo {caminho}: {e}")
        return ""


root_agent = Agent(
    name=APP_NAME,
    model=llm_model,
    description=_carregar_arquivo("description_agente_negociacao.txt"),
    instruction=_carregar_arquivo("instruction_agente_negociacao.txt"),
    generate_content_config=types.GenerateContentConfig(
        temperature=0.0,
        max_output_tokens=2048
    ),
    tools=[
        FunctionTool(func=autenticar_cliente),
        FunctionTool(func=consultar_divida),
        FunctionTool(func=proposta_avista),
        FunctionTool(func=proposta_por_parcelas),
        FunctionTool(func=proposta_por_valor),
        FunctionTool(func=gerar_boleto_pdf_bytes),
        FunctionTool(func=listar_boletos),
        FunctionTool(func=encerrar_atendimento),
    ],
)

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=InMemorySessionService(),
)

