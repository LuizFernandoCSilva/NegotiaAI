import re
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import pytesseract
from PIL import Image
import PyPDF2

logger = logging.getLogger(__name__)


class ComprovanteValidator:
    
    def __init__(self):
        try:
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
        except Exception:
            self.tesseract_available = False
    
    def validar_comprovante(
        self,
        file_path: str = None,
        caminho_arquivo: str = None,
        cpf_esperado: str = None,
        valor_esperado: float = None,
        linha_digitavel_esperada: str = None,
        data_vencimento_esperada: datetime = None,
        tolerancia_dias: int = 30
    ) -> Dict:
        """
        Valida um comprovante de pagamento via OCR.
        """
        path = file_path or caminho_arquivo
        if not path:
            return {
                'valido': False,
                'mensagem': 'Caminho do arquivo não fornecido.',
                'detalhes': {}
            }
        
        try:
            texto = self._extrair_texto(path)
            
            if not texto or len(texto.strip()) < 20:
                return {
                    'valido': False,
                    'mensagem': 'Comprovante ilegível ou vazio.',
                    'detalhes': {'texto_extraido': texto}
                }
            
            validacoes = {
                'cpf': self._validar_cpf_no_texto(texto, cpf_esperado),
                'valor': self._validar_valor_no_texto(texto, valor_esperado),
                'data': self._validar_data_pagamento(texto, tolerancia_dias),
                'palavras_chave': self._validar_palavras_chave(texto)
            }
            
            if linha_digitavel_esperada:
                validacoes['linha_digitavel'] = self._validar_linha_digitavel_no_texto(texto, linha_digitavel_esperada)
            
            if data_vencimento_esperada:
                validacoes['data_vencimento'] = self._validar_data_vencimento(texto, data_vencimento_esperada)
            
            validacoes_passadas = sum(1 for v in validacoes.values() if v['valido'])
            total_validacoes = len(validacoes)
            valido_geral = validacoes_passadas >= min(3, total_validacoes)
            
            if valido_geral:
                mensagem = 'Comprovante validado com sucesso.'
            else:
                falhas = [k for k, v in validacoes.items() if not v['valido']]
                mensagem = f'Comprovante inválido. Falhas: {", ".join(falhas)}'
            
            return {
                'valido': valido_geral,
                'mensagem': mensagem,
                'detalhes': {
                    'validacoes': validacoes,
                    'texto_extraido': texto[:500],
                    'score': f'{validacoes_passadas}/{total_validacoes}'
                }
            }
            
        except Exception as e:
            return {
                'valido': False,
                'mensagem': f'Erro ao processar comprovante: {str(e)}',
                'detalhes': {'erro': str(e)}
            }
    
    def extrair_texto(self, file_path: str) -> str:
        return self._extrair_texto(file_path)
    
    def _extrair_texto(self, file_path: str) -> str:
        file_path = Path(file_path)
        extensao = file_path.suffix.lower()
        
        try:
            if extensao == '.pdf':
                return self._extrair_texto_pdf(file_path)
            elif extensao in ['.jpg', '.jpeg', '.png']:
                return self._extrair_texto_imagem(file_path)
            else:
                return ''
        except Exception as e:
            logger.error(f"Erro ao extrair texto: {e}")
            return ''
    
    def _extrair_texto_pdf(self, file_path: Path) -> str:
        texto = ''
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    texto += page.extract_text() + '\n'
            
            if len(texto.strip()) < 20:
                try:
                    from pdf2image import convert_from_path
                    images = convert_from_path(str(file_path), first_page=1, last_page=1)
                    if images:
                        texto = pytesseract.image_to_string(images[0], lang='por')
                except ImportError:
                    pass
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {e}")
        return texto
    
    def _extrair_texto_imagem(self, file_path: Path) -> str:
        try:
            image = Image.open(file_path)
            texto = pytesseract.image_to_string(image, lang='por')
            return texto
        except Exception as e:
            logger.error(f"Erro ao extrair texto da imagem: {e}")
            return ''
    
    def _validar_cpf_no_texto(self, texto: str, cpf_esperado: str) -> Dict:
        cpf_limpo = re.sub(r'\D', '', cpf_esperado)
        cpf_formatado = f'{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}'
        encontrado = cpf_limpo in texto or cpf_formatado in texto
        return {
            'valido': encontrado,
            'mensagem': 'CPF encontrado' if encontrado else 'CPF não encontrado',
            'valor_procurado': cpf_formatado
        }
    
    def _validar_valor_no_texto(self, texto: str, valor_esperado: float) -> Dict:
        valor_str1 = f'{valor_esperado:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        valor_str2 = f'{valor_esperado:.2f}'.replace('.', ',')
        valor_str3 = f'R$ {valor_str1}'
        valor_str4 = f'R$ {valor_str2}'
        
        encontrado = any(v in texto for v in [valor_str1, valor_str2, valor_str3, valor_str4])
        
        if not encontrado:
            valores_no_texto = re.findall(r'R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})', texto)
            for v in valores_no_texto:
                v_num = float(v.replace('.', '').replace(',', '.'))
                if abs(v_num - valor_esperado) / valor_esperado <= 0.01:
                    encontrado = True
                    break
        
        return {
            'valido': encontrado,
            'mensagem': 'Valor encontrado' if encontrado else 'Valor não encontrado',
            'valor_procurado': valor_str3
        }
    
    def _validar_linha_digitavel_no_texto(self, texto: str, linha_digitavel: str) -> Dict:
        linha_limpa = re.sub(r'[\s\.]', '', linha_digitavel)
        texto_limpo = re.sub(r'[\s\.]', '', texto)
        encontrado = linha_limpa in texto_limpo
        
        if not encontrado and len(linha_limpa) >= 15:
            encontrado = linha_limpa[:15] in texto_limpo
        
        return {
            'valido': encontrado,
            'mensagem': 'Código de barras encontrado' if encontrado else 'Código de barras não encontrado',
            'valor_procurado': linha_digitavel[:20] + '...'
        }
    
    def _validar_data_pagamento(self, texto: str, tolerancia_dias: int) -> Dict:
        padroes = [
            r'(\d{2})[/-](\d{2})[/-](\d{4})',
            r'(\d{2})[/-](\d{2})[/-](\d{2})',
        ]
        
        datas_encontradas = []
        for padrao in padroes:
            matches = re.findall(padrao, texto)
            for match in matches:
                try:
                    ano = int(match[2]) + 2000 if len(match[2]) == 2 else int(match[2])
                    data = datetime(ano, int(match[1]), int(match[0]))
                    datas_encontradas.append(data)
                except ValueError:
                    continue
        
        agora = datetime.now()
        data_valida = any(abs((agora - data).days) <= tolerancia_dias for data in datas_encontradas)
        
        return {
            'valido': data_valida or len(datas_encontradas) == 0,
            'mensagem': 'Data válida' if data_valida else 'Data não encontrada ou fora do prazo',
            'datas_encontradas': [d.strftime('%d/%m/%Y') for d in datas_encontradas[:3]]
        }
    
    def _validar_data_vencimento(self, texto: str, data_vencimento_esperada: datetime) -> Dict:
        """
        Valida se a data do pagamento extraída do comprovante é anterior ou igual à data de vencimento do boleto.
        Retorna inválido se o pagamento foi feito após o vencimento.
        """
        padroes = [
            r'(?:data|pagamento|pago em|realizado em)[:\s]*(\d{2})[/-](\d{2})[/-](\d{4})',
            r'(\d{2})[/-](\d{2})[/-](\d{4})',
            r'(\d{2})[/-](\d{2})[/-](\d{2})',
        ]
        
        data_pagamento = None
        for padrao in padroes:
            matches = re.findall(padrao, texto, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match[2]) == 2:
                        ano = int(match[2]) + 2000
                    else:
                        ano = int(match[2])
                    data = datetime(ano, int(match[1]), int(match[0]))
                    
                    if 2020 <= data.year <= 2030:
                        data_pagamento = data
                        break
                except (ValueError, IndexError):
                    continue
            if data_pagamento:
                break
        
        if not data_pagamento:
            return {
                'valido': False,
                'mensagem': 'Data de pagamento não encontrada no comprovante',
                'data_vencimento': data_vencimento_esperada.strftime('%d/%m/%Y') if isinstance(data_vencimento_esperada, datetime) else str(data_vencimento_esperada),
                'data_pagamento': None
            }
        
        # Converter data_vencimento_esperada para datetime se for string
        if isinstance(data_vencimento_esperada, str):
            try:
                data_vencimento_esperada = datetime.strptime(data_vencimento_esperada, '%Y-%m-%d')
            except:
                try:
                    data_vencimento_esperada = datetime.strptime(data_vencimento_esperada, '%d/%m/%Y')
                except:
                    return {
                        'valido': False,
                        'mensagem': f'Erro ao processar data de vencimento: formato inválido ({data_vencimento_esperada})'
                    }
        
        pagamento_valido = data_pagamento.date() <= data_vencimento_esperada.date()
        
        if pagamento_valido:
            mensagem = f'Pagamento realizado antes do vencimento'
        else:
            dias_atraso = (data_pagamento.date() - data_vencimento_esperada.date()).days
            mensagem = f'ATENÇÃO: Pagamento realizado {dias_atraso} dia(s) APÓS o vencimento'
        
        return {
            'valido': pagamento_valido,
            'mensagem': mensagem,
            'data_vencimento': data_vencimento_esperada.strftime('%d/%m/%Y'),
            'data_pagamento': data_pagamento.strftime('%d/%m/%Y'),
            'dias_diferenca': (data_vencimento_esperada.date() - data_pagamento.date()).days
        }
    
    def _validar_palavras_chave(self, texto: str) -> Dict:
        texto_lower = texto.lower()
        palavras_chave = [
            'comprovante', 'pagamento', 'transferência', 'pix', 'boleto',
            'quitação', 'valor', 'data', 'autenticação', 'banco', 'agência', 'conta'
        ]
        encontradas = [p for p in palavras_chave if p in texto_lower]
        score = len(encontradas)
        return {
            'valido': score >= 3,
            'mensagem': f'{score} palavras-chave encontradas',
            'palavras_encontradas': encontradas[:5]
        }
    
    def extrair_cpf_do_comprovante(self, file_path: str) -> Optional[str]:
        try:
            texto = self._extrair_texto(file_path)
            if not texto or len(texto.strip()) < 10:
                return None
            return self._buscar_cpf_no_texto(texto)
        except Exception as e:
            logger.error(f"Erro ao extrair CPF: {e}")
            return None
        
    def extrair_data_do_pagamento(self, file_path: str) -> Optional[datetime]:
        try:
            texto = self._extrair_texto(file_path)
            if not texto or len(texto.strip()) < 10:
                return None
            
            padroes = [
                r'(\d{2})[/-](\d{2})[/-](\d{4})',
                r'(\d{2})[/-](\d{2})[/-](\d{2})',
            ]
            
            for padrao in padroes:
                matches = re.findall(padrao, texto)
                for match in matches:
                    try:
                        ano = int(match[2]) + 2000 if len(match[2]) == 2 else int(match[2])
                        data = datetime(ano, int(match[1]), int(match[0]))
                        return data
                    except ValueError:
                        continue
            return None
        except Exception as e:
            logger.error(f"Erro ao extrair data: {e}")
            return None
    
    def _buscar_cpf_no_texto(self, texto: str) -> Optional[str]:
        cpf_formatado = re.findall(r'\d{3}\.\d{3}\.\d{3}-\d{2}', texto)
        if cpf_formatado:
            return re.sub(r'[.\-]', '', cpf_formatado[0])
        cpf_apos_label = re.findall(r'CPF\s*:\s*(\d{11})', texto, re.IGNORECASE)
        if cpf_apos_label:
            return cpf_apos_label[0]
        cpf_sem_formato = re.findall(r'\b\d{11}\b', texto)
        if cpf_sem_formato:
            return cpf_sem_formato[0]
        cpf_espacos = re.findall(r'\b\d{3}\s\d{3}\s\d{3}\s\d{2}\b', texto)
        if cpf_espacos:
            return re.sub(r'\s', '', cpf_espacos[0])
        return None


# Instância singleton
_validator_instance = None

def get_validator() -> ComprovanteValidator:
    """Retorna instância singleton do validador (OCR apenas)."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ComprovanteValidator()
    return _validator_instance
