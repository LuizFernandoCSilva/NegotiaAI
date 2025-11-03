import uuid
import re
import logging
from app.infrastructure.database.connection import registrar_comprovante, listar_boletos
from app.utils.comprovante_validator import get_validator
from app.utils.cpfValidate import validar_cpf
from app.core.config import AppConfig
from backend.app.utils.verifyDueDate import verificar_data_vencimento

logger = logging.getLogger(__name__)


UPLOAD_DIR = AppConfig.COMPROVANTES_DIR
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def secure_filename(filename: str) -> str:
    filename = filename.replace('\\', '_').replace('/', '_')
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename.strip('._')


def processar_comprovante_from_path(temp_path: str, original_filename: str, validar: bool = True) -> dict | None:
    from pathlib import Path
    import os
    
    temp_path_obj = Path(temp_path)
    
    try:
        validator = get_validator()

        try:
            texto_extraido = validator.extrair_texto(str(temp_path_obj)) or ''
        except Exception:
            texto_extraido = ''

        cpf_extraido = validator.extrair_cpf_do_comprovante(str(temp_path_obj))
        data_pagamento = validator.extrair_data_do_pagamento(str(temp_path_obj))
        data_vencimento_doc = validator.extrair_data_de_vencimento(str(temp_path_obj))

        if not cpf_extraido:
            texto_debug = texto_extraido[:500] if texto_extraido else ''
            os.unlink(temp_path)

            if not validator.tesseract_available:
                return {
                    'erro': 'CPF_NAO_ENCONTRADO',
                    'mensagem': 'Não foi possível identificar o CPF no comprovante. O Tesseract OCR não está instalado.',
                    'detalhes': {
                        'texto_extraido': texto_debug
                    }
                }

            return {
                'erro': 'CPF_NAO_ENCONTRADO',
                'mensagem': 'Não foi possível identificar o CPF no comprovante enviado.',
                'detalhes': {
                    'texto_extraido': texto_debug
                }
            }

        if not validar_cpf(cpf_extraido):
            os.unlink(temp_path)
            return {
                'erro': 'CPF_INVALIDO',
                'mensagem': f'O CPF extraído ({cpf_extraido}) é inválido.'
            }

        boletos = listar_boletos(cpf=cpf_extraido)

        if not boletos:
            os.unlink(temp_path)
            return {
                'erro': 'SEM_BOLETO',
                'mensagem': f'Não encontramos boletos cadastrados para o CPF {cpf_extraido}.'
            }

        boleto = boletos[0]
        valor_boleto = boleto.get('valor_total') or boleto.get('valor', 0.0)
        data_vencimento_boleto = boleto.get('data_vencimento')

        try:
            if data_vencimento_doc:
                if data_pagamento and data_pagamento.date() > data_vencimento_doc.date():
                    os.unlink(temp_path)
                    dias_atraso = (data_pagamento.date() - data_vencimento_doc.date()).days
                    return {
                        'erro': 'BOLETO_VENCIDO',
                        'mensagem': f'Pagamento com atraso não é permitido. O comprovante indica pagamento em {data_pagamento.strftime("%d/%m/%Y")}, que é {dias_atraso} dia(s) após o vencimento ({data_vencimento_doc.strftime("%d/%m/%Y")}).' 
                    }

                banco_venc = boleto.get('data_vencimento')
                banco_dt = None
                try:
                    from datetime import datetime as _dt
                    if isinstance(banco_venc, str):
                        try:
                            banco_dt = _dt.fromisoformat(banco_venc)
                        except Exception:
                            try:
                                banco_dt = _dt.strptime(banco_venc.split('T')[0], '%Y-%m-%d')
                            except Exception:
                                try:
                                    banco_dt = _dt.strptime(banco_venc, '%d/%m/%Y')
                                except Exception:
                                    banco_dt = None
                    elif hasattr(banco_venc, 'date'):
                        banco_dt = banco_venc
                except Exception:
                    banco_dt = None

                if banco_dt:
                    if data_vencimento_doc.date() != banco_dt.date():
                        os.unlink(temp_path)
                        return {
                            'erro': 'VENCIMENTO_DIVERGENTE',
                            'mensagem': f'Data de vencimento no documento ({data_vencimento_doc.strftime("%d/%m/%Y")}) diverge da data cadastrada ({banco_dt.strftime("%d/%m/%Y")}).'
                        }

            venc_ok = verificar_data_vencimento(boleto.get('data_vencimento'), data_pagamento)
            if not venc_ok:
                os.unlink(temp_path)
                return {
                    'erro': 'BOLETO_VENCIDO',
                    'mensagem': f'O boleto associado ao CPF {cpf_extraido} está vencido. Pagamento com atraso não é permitido.'
                }
        except Exception:
            logger.exception("Erro ao verificar data de vencimento do comprovante")
        
        if validar:
            validacao = validator.validar_comprovante(
                caminho_arquivo=str(temp_path_obj),
                cpf_esperado=cpf_extraido,
                valor_esperado=valor_boleto,
                data_vencimento_esperada=data_vencimento_boleto
            )

            if not validacao['valido']:
                os.unlink(temp_path)
                return {
                    'erro': 'VALIDACAO_FALHOU',
                    'mensagem': f"Comprovante inválido. {validacao.get('mensagem', '')}",
                    'detalhes': validacao.get('detalhes')
                }
        
        filename = secure_filename(original_filename)
        final_name = f"{cpf_extraido}_{uuid.uuid4()}_{filename}"
        final_path = UPLOAD_DIR / final_name
        
        import shutil
        shutil.move(temp_path, str(final_path))
        
        boleto_id = boleto.get('id_boleto')
        registro = registrar_comprovante(
            boleto_id=boleto_id,
            file_path=str(final_path),
            original_name=original_filename
        )
        
        return {
            'cpf_identificado': cpf_extraido,
            'valor_boleto': valor_boleto,
            'arquivo_salvo': str(final_path),
            'registro_id': registro.get('id_comprovante') if registro else None
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar comprovante: {e}", exc_info=True)
        
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        
        return None


