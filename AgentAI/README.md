# 🤖 NegotiaAI - Sistema Inteligente de Negociação de Dívidas

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.120+-green?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue?style=for-the-badge&logo=postgresql)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-2.0-orange?style=for-the-badge&logo=google)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?style=for-the-badge&logo=docker)

**Sistema de agente conversacional inteligente para negociação automatizada de dívidas bancárias**

[🚀 Começar](#-instalação-passo-a-passo) • [📖 Documentação](#-arquitetura-do-sistema) • [🎯 Funcionalidades](#-principais-funcionalidades) • [🤝 Contribuir](#-contribuição)

</div>

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Principais Funcionalidades](#-principais-funcionalidades)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Fluxo do Agente](#-fluxo-do-agente-de-negociação)
- [Tecnologias Utilizadas](#️-tecnologias-utilizadas)
- [Desafios e Decisões Técnicas](#-desafios-enfrentados-e-decisões-técnicas)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação Passo a Passo](#-instalação-passo-a-passo)
- [Variáveis de Ambiente](#-configuração-de-variáveis-de-ambiente)
- [Como Executar](#-como-executar)
- [Endpoints da API](#-endpoints-da-api)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Testes](#-testes)
- [Comandos Úteis](#-comandos-úteis)

---

## 📖 Visão Geral

O **NegotiaAI** é uma plataforma completa que utiliza **Inteligência Artificial conversacional** para automatizar e humanizar o processo de negociação de dívidas bancárias. 

### ✅ NegotiaAI

Um agente de IA que:
- ✅ Atende clientes 24/7 de forma empática
- ✅ Personaliza propostas em tempo real
- ✅ Emite boletos automaticamente
- ✅ Valida comprovantes via OCR

---

## 🎯 Principais Funcionalidades

### 🤖 Agente Conversacional Inteligente
- Powered by **Google Gemini 2.0 Flash**
- Compreensão de linguagem natural em português
- Personalização baseada no perfil do cliente
- Respostas empáticas e humanizadas

### 💳 Gestão Completa de Dívidas
- Autenticação segura por CPF
- Consulta automática de débitos
- Cálculo dinâmico de propostas
- Múltiplas opções de parcelamento

### 📄 Sistema de Boletos
- Geração automática de boletos PDF
- Código de barras e linha digitável
- Download via API REST
- Integração com banco de dados

### 🔍 Validação de Comprovantes (OCR)
- Upload de imagens/PDFs
- Extração automática de CPF e valores
- Validação cruzada com boletos emitidos
- Detecção de inconsistências

---

## 🏗️ Arquitetura do Sistema

### 📐 Diagrama de Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────────────┐
│                    🎨 FRONTEND LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Streamlit   │  │  Chat UI     │  │ File Upload  │      │
│  │   Interface   │  │  Component   │  │  Component   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ⬇️ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                    🚀 API LAYER (FastAPI)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Chat       │  │  Boletos     │  │ Comprovantes │      │
│  │   Routes     │  │  Routes      │  │   Routes     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          CORS + Exception Handler Middleware        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ⬇️
┌─────────────────────────────────────────────────────────────┐
│                   💼 BUSINESS LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Agent      │  │   Session    │  │  Comprovante │      │
│  │   Service    │  │   Manager    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Validators: CPF, Date, Document, Payment Proof    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ⬇️
┌─────────────────────────────────────────────────────────────┐
│              🧠 AI LAYER (Google Gemini)                     │
│  ┌──────────────────────────────────────────────────┐       │
│  │              Google ADK Agent                     │       │
│  │  ┌─────────────────────────────────────────┐     │       │
│  │  │  Gemini 2.0 Flash LLM Engine            │     │       │
│  │  └─────────────────────────────────────────┘     │       │
│  │  ┌─────────────────────────────────────────┐     │       │
│  │  │  Function Tools (8 ferramentas)         │     │       │
│  │  │  • autenticar_cliente                   │     │       │
│  │  │  • consultar_divida                     │     │       │
│  │  │  • proposta_avista                      │     │       │
│  │  │  • proposta_por_parcelas                │     │       │
│  │  │  • proposta_por_valor                   │     │       │
│  │  │  • gerar_boleto_pdf_bytes               │     │       │
│  │  │  • listar_boletos                       │     │       │
│  │  │  • encerrar_atendimento                 │     │       │
│  │  └─────────────────────────────────────────┘     │       │
│  │  ┌─────────────────────────────────────────┐     │       │
│  │  │  Prompt Engineering System              │     │       │
│  │  │  • instructions (fluxo + regras)        │     │       │
│  │  │  • description (persona)                │     │       │
│  │  └─────────────────────────────────────────┘     │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            ⬇️
┌─────────────────────────────────────────────────────────────┐
│              🗄️ INFRASTRUCTURE LAYER                         │
│  ┌──────────────────────────────────────────────────┐       │
│  │          SQLAlchemy ORM + Connection Pool        │       │
│  └──────────────────────────────────────────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Seed      │  │    Models    │      │
│  │   Database   │  │   Sistema    │  │  (Customer,  │      │
│  │   (Docker)   │  │              │  │  Plan, etc)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 🔄 Comunicação Entre Camadas

1. **Frontend → API**: Requisições HTTP/REST
2. **API → Business**: Chamadas de funções Python
3. **Business → AI**: Google ADK SDK
4. **AI → Database**: ORM SQLAlchemy
5. **Database → AI**: Dados estruturados
6. **AI → Business**: Respostas JSON
7. **Business → API**: DTOs (Pydantic)
8. **API → Frontend**: JSON responses

---

## 🔄 Fluxo do Agente de Negociação

O agente segue um **fluxo estruturado** e **obrigatório**, garantindo uma experiência consistente:

### 📋 Fluxograma Completo

```mermaid
graph TD
    START([👋 Usuário Inicia Conversa]) --> GREETING[🎯 Saudação Personalizada]
    GREETING --> ASK_CPF[📝 Solicitar CPF]
    
    ASK_CPF --> RECEIVE_CPF{CPF Recebido?}
    RECEIVE_CPF -->|Sim| AUTH[🔐 autenticar_cliente CPF]
    RECEIVE_CPF -->|Não| ASK_CPF
    
    AUTH --> AUTH_OK{Autenticado?}
    AUTH_OK -->|❌ Não| NOT_FOUND[❌ CPF não encontrado]
    NOT_FOUND --> ASK_CPF
    
    AUTH_OK -->|✅ Sim| QUERY_DEBT[💰 consultar_divida CPF]
    QUERY_DEBT --> PRESENT_DEBT[📊 Apresentar Valor da Dívida]
    
    PRESENT_DEBT --> ASK_OPTION[💡 Perguntar: À vista ou Parcelado?]
    
    ASK_OPTION --> USER_CHOICE{Escolha do Cliente}
    
    USER_CHOICE -->|À vista| PROPOSAL_CASH[💵 proposta_avista CPF]
    USER_CHOICE -->|Parcelado| ASK_INSTALLMENT[🔢 Perguntar: Qtd parcelas ou valor?]
    
    ASK_INSTALLMENT --> INSTALL_CHOICE{Tipo de Info}
    INSTALL_CHOICE -->|Quantidade| PROPOSAL_INSTALL[🔢 proposta_por_parcelas CPF qtd]
    INSTALL_CHOICE -->|Valor| PROPOSAL_VALUE[💵 proposta_por_valor CPF valor]
    
    PROPOSAL_CASH --> SHOW_PROPOSAL[📋 Mostrar Proposta]
    PROPOSAL_INSTALL --> SHOW_PROPOSAL
    PROPOSAL_VALUE --> SHOW_PROPOSAL
    
    SHOW_PROPOSAL --> CONFIRM{Cliente Aceita?}
    CONFIRM -->|❌ Não| ASK_OPTION
    CONFIRM -->|✅ Sim| GENERATE_BOLETO[📄 gerar_boleto_pdf_bytes ...]
    
    GENERATE_BOLETO --> BOLETO_OK{Boleto Gerado?}
    BOLETO_OK -->|❌ Erro| ERROR[⚠️ Erro ao Gerar]
    BOLETO_OK -->|✅ Sucesso| SHOW_BOLETO[📥 Mostrar Boleto + Link Download]
    
    SHOW_BOLETO --> ASK_RECEIPT[📤 Perguntar: Enviará comprovante?]
    
    ASK_RECEIPT --> RECEIPT_CHOICE{Cliente Responde}
    RECEIPT_CHOICE -->|Sim| WAIT_UPLOAD[⏳ Aguardar Upload]
    RECEIPT_CHOICE -->|Não| INFORM_LATER[📝 Informar que pode enviar depois]
    
    WAIT_UPLOAD --> UPLOAD_RECEIVED[✅ Comprovante Recebido]
    UPLOAD_RECEIVED --> VALIDATE[🔍 Validar via OCR]
    
    VALIDATE --> VALID{Validação}
    VALID -->|✅ OK| CONFIRM_RECEIPT[✅ Confirmar Recebimento]
    VALID -->|❌ Erro| ERROR_MSG[❌ Mensagem de Erro Específica]
    
    ERROR_MSG --> ASK_RECEIPT
    CONFIRM_RECEIPT --> THANK[🙏 Agradecer]
    INFORM_LATER --> THANK
    
    THANK --> FAREWELL_CHECK{Cliente se Despede?}
    FAREWELL_CHECK -->|❌ Não| CONTINUE[💬 Continuar Atendimento]
    FAREWELL_CHECK -->|✅ Sim| END_SESSION[🔚 encerrar_atendimento motivo]
    
    CONTINUE --> ASK_OPTION
    END_SESSION --> GOODBYE[👋 Mensagem de Despedida]
    GOODBYE --> STOP([🛑 FIM - Não Responder Mais])
    
    ERROR --> ASK_OPTION
```

### 📝 Descrição Detalhada de Cada Etapa

#### **1️⃣ Saudação e Autenticação** (Obrigatório)

**Ação do Agente:**
```
"Olá! Tenho uma proposta para quitarmos sua dívida do cartão ResolveBank. 
Podemos conversar?"
```

**Próximo Passo:**
```
"Para começarmos, qual é o seu CPF?"
```

**Ferramentas Chamadas:**
1. `autenticar_cliente(cpf)` - Verifica se CPF existe na base
2. `consultar_divida(cpf)` - Busca valor real da dívida

**Validações:**
- ✅ CPF deve ter 11 dígitos
- ✅ CPF deve passar na validação de dígito verificador
- ✅ CPF deve existir no banco de dados

---

#### **2️⃣ Apresentação da Dívida** (Obrigatório)

**Ação do Agente:**
```
"[Nome], o valor da sua dívida no cartão ResolveBank é R$ [divida_total]. 
Temos opções à vista com desconto e parceladas. Qual prefere?"
```

**Regras:**
- 🚫 NUNCA inventar valores
- ✅ SEMPRE usar valor retornado por `consultar_divida()`
- ✅ Chamar cliente pelo nome retornado

---

#### **3️⃣ Negociação - Escolha da Modalidade** (Interativo)

**Opção A: À Vista**
- **Ferramenta:** `proposta_avista(cpf)`
- **Retorno:** Plano com 1 parcela e maior desconto
- **Apresentação:**
  ```
  "Ótimo! À vista você paga R$ [total_pago] (desconto de [desconto]%). 
  Aceita essa proposta?"
  ```

**Opção B: Parcelado**
- **Pergunta:** "Prefere dizer o número de parcelas ou o valor que cabe no bolso?"
  
  - **Por Quantidade:**
    - **Ferramenta:** `proposta_por_parcelas(cpf, qtd_parcelas)`
    - **Apresentação:**
      ```
      "Certo! Em [qtd] parcelas de R$ [valor_parcela].
      Total: R$ [total_pago]. Aceita?"
      ```
  
  - **Por Valor:**
    - **Ferramenta:** `proposta_por_valor(cpf, valor_parcela_desejado)`
    - **Apresentação:**
      ```
      "Encontrei um plano de [qtd] parcelas de R$ [valor_parcela].
      Total: R$ [total_pago]. Serve para você?"
      ```

**Tratamento de "Não Exato":**
- Se não houver plano exato, o sistema retorna o **mais próximo**
- Agente apresenta a alternativa sem forçar aceitação

---

#### **4️⃣ Geração do Boleto** (Automático) Oliveira   (R$ 450,00   - Perfil: Contencioso)
CPF: 11122233344 - Carlos Pereira   (R$ 3.200,50 - Perfil: Amigável)
```

**💰 Planos de Pagamento:**
- **João da Silva**: 3 opções (1x, 3x, 6x) com desconto à vista
- ****Após Aceitação:**
- **Ferramenta:** `gerar_boleto_pdf_bytes(cpf, id_plano, linha_digitavel, valor, dias_vencimento, id_boleto)`
- **Ações Automáticas:**
  1. Gera PDF do boleto com código de barras
  2. Salva em `data/boletos/`
  3. Registra no banco de dados
  4. Retorna URL de download

**Apresentação:**
```
Boleto gerado com sucesso!

Detalhes:
- Valor: R$ [valor]
- Vencimento: [DD/MM/AAAA]
- Linha digitável: [linha_digitavel]

O boleto já está disponível para download. Basta clicar no botão abaixo da mensagem!

Você conseguirá enviar um comprovante do pagamento?
```

**Metadados (invisíveis ao usuário):**
```html
<!-- METADATA_BOLETO: id=[UUID], url=[download_url] -->
```

---

#### **5️⃣ Validação de Comprovante** (Opcional mas Encorajado)

**Pergunta do Agente:**
```
"Você conseguirá enviar um comprovante do pagamento?"
```

**Se SIM:**
```
"Ótimo! Você pode enviar o comprovante pela lateral da tela. 
Estarei aguardando!"
```

**Quando Arquivo Chegar:**

**✅ SUCESSO:**
```
"Perfeito! Recebi seu comprovante. Ele já está sendo processado. Obrigado!"
```

**❌ ERROS DO SISTEMA:**

| Erro | Mensagem do Agente |
|------|-------------------|
| CPF não encontrado | "Não consegui identificar seu CPF no sistema. Você tem certeza de que possui uma dívida conosco?" |
| CPF inválido | "Não consegui identificar um CPF válido. Pode tentar enviar novamente?" |
| Sem boleto | "Identifiquei seu CPF, mas você ainda não possui um boleto gerado." |
| CPF diferente | "ATENÇÃO! Este comprovante pertence a outro CPF. Envie o comprovante CORRETO da sua negociação." |

**Se NÃO:**
```
"Sem problemas! Quando fizer o pagamento, pode enviar por aqui. 
Estarei à disposição!"
```

---

#### **6️⃣ Encerramento** (Apenas com Despedida Clara)

**✅ Sinais de Encerramento (Aceitos):**
- "Até logo", "Tchau", "Obrigado, é só isso"
- "Pode encerrar", "Não preciso de mais nada"
- "Já resolvi tudo", "Até mais", "Valeu até", "Falou"

**❌ NÃO Encerrar Com:**
- "Ok", "Obrigado" (simples agradecimento)
- "Tá bom", "Entendi", "Certo"
- Qualquer mensagem sem despedida explícita

**Ferramenta:** `encerrar_atendimento(motivo)`
- **Motivos:** `"encerramento"` ou `"transferencia"`

**Mensagem Final:**
```
"Foi um prazer ajudar você! Se precisar, estarei por aqui. Até breve!"
```

**🛑 REGRA CRÍTICA:** Após encerrar, o agente **NÃO RESPONDE MAIS MENSAGENS**.

---

## 🛠️ Tecnologias Utilizadas

### 🔧 Backend

| Tecnologia | Versão | Propósito |
|-----------|--------|-----------|
| **Python** | 3.11+ | Linguagem principal |
| **FastAPI** | 0.120+ | Framework web assíncrono |
| **Uvicorn** | 0.34+ | Servidor ASGI |
| **Pydantic** | 2.12+ | Validação de dados |
| **SQLAlchemy** | 2.0+ | ORM para PostgreSQL |
| **psycopg2-binary** | 2.9+ | Driver PostgreSQL |

### 🧠 Inteligência Artificial

| Tecnologia | Versão | Propósito |
|-----------|--------|-----------|
| **Google Gemini** | 2.0 Flash | LLM conversacional |
| **google-genai** | 1.46+ | SDK oficial Google AI |
| **google-adk** | 1.17+ | Agent Development Kit |

### 🔍 Processamento de Documentos

| Tecnologia | Versão | Propósito |
|-----------|--------|-----------|
| **Tesseract OCR** | 0.3+ | Extração de texto |
| **pytesseract** | 0.3+ | Wrapper Python |
| **Pillow** | 11.3+ | Processamento de imagens |
| **PyPDF2** | 3.0+ | Manipulação de PDFs |
| **ReportLab** | 4.2+ | Geração de PDFs |

### 🗄️ Infraestrutura

| Tecnologia | Versão | Propósito |
|-----------|--------|-----------|
| **PostgreSQL** | 16+ | Banco de dados relacional |
| **Docker** | Latest | Containerização |
| **Docker Compose** | 3.8+ | Orquestração |

### 🎨 Frontend

| Tecnologia | Versão | Propósito |
|-----------|--------|-----------|
| **Streamlit** | 1.28+ | Interface web interativa |
| **python-multipart** | 0.0.20+ | Upload de arquivos |

---

## ⚡ Desafios Enfrentados e Decisões Técnicas

### 🎯 Desafio 1: Controle de Fluxo Conversacional

**❌ Problema:**
- LLMs tendem a "fugir do roteiro"
- Risco de pular etapas obrigatórias (ex: autenticação)
- Dificuldade em forçar chamadas de ferramentas

**✅ Solução Implementada:**

1. **Prompt Engineering Rigoroso**
   - Instruções claras com palavras em CAIXA ALTA para ênfase
   - Exemplos de fluxo correto e incorreto
   - Seção "PROIBIÇÕES" explícita

2. **Validação em Múltiplas Camadas**
   ```python
   # Agent Layer
   - Valida CPF antes de qualquer operação
   - Retorna erro estruturado se dados inválidos
  
   # Business Layer  
   - Normaliza CPF (remove formatação)
   - Valida existência no banco
   
   # Infrastructure Layer
   - Constraints de banco (UNIQUE, NOT NULL)
   - Foreign keys para integridade referencial
   ```

3. **Function Tools como "Guardrails"**
   - Cada função valida seus próprios inputs
   - Retorno padronizado: `{success, data, error}`
   - Logs detalhados para auditoria

---

### 🎯 Desafio 2: Performance e Latência da IA

**❌ Problema:**
- Latência de ~2-5s por chamada ao Gemini
- Custo por token (entrada + saída)
- Risco de timeout em conversas longas

**✅ Solução Implementada:**

2. **Otimizações de Prompt**
   - Temperatura baixa (0.1) para respostas determinísticas
   - Max tokens limitado (2048) para respostas concisas
   - Instruções diretas sem fluff

3. **Gerenciamento de Sessões**
   ```python
   class SessionManager:
       # Sessões em memória (InMemorySessionService)
       # Cleanup automático após inatividade
       # Reuso de contexto sem re-processar histórico
   ```
---

### 🎯 Desafio 3: Validação de Comprovantes (OCR)

**❌ Problema:**
- PDFs de baixa qualidade (escaneados)
- Formato de CPF inconsistente (com/sem máscara)
- Valores em formatos variados (R$ 1.000,00 vs 1000.00)

**✅ Solução Implementada:**

1. **Pipeline OCR Multi-Stage**
   ```python
   # Stage 1: Extração de Texto
   - Tesseract OCR (português)
   - Fallback: pdf2image + OCR em imagens
   
   # Stage 2: Normalização
   - Remove caracteres especiais
   - Padroniza formato de CPF (somente números)
   - Converte valores para Decimal
   
   # Stage 3: Validação Cruzada
   - Compara CPF extraído com boleto cadastrado
   - Verifica valor ±5% de tolerância
   - Valida data de pagamento vs vencimento
   ```

2. **Tratamento de Erros Específicos**
   ```python
   if not cpf_extraido:
       return "CPF não encontrado no comprovante"
   
   if not validaFr_cpf(cpf_extraido):
       return "CPF extraído é inválido"
   
   if cpf_extraido != cpf_esperado:
       return "CPF diferente do boleto!"
   ```

3. **Feedback Claro ao Usuário**
   - Mensagens em português claro
   - Sugestões de ação ("Envie novamente", "Verifique o arquivo")
   - Sem jargão técnico

---

### 🎯 Desafio 3: Arquitetura Escalável e Manutenível

**❌ Problema:**
  - Estruturar o projeto de uma forma pensando em possíveis necessidade de escalamento

**✅ Solução Implementada:**

**Um pouco de Clean Architecture + DDD:**

```
backend/
├── app/
│   ├── api/              # 🌐 Controllers (FastAPI routes)
│   │   └── v1/
│   │       └── endpoints/
│   ├── services/         # 💼 Business Logic
│   │   ├── agent_service.py
│   │   └── comprovante_service.py
│   ├── domain/           # 📊 Entities & Value Objects
│   │   ├── models/
│   │   └── schemas/
│   ├── infrastructure/   # 🔧 External Dependencies
│   │   ├── database/
│   │   └── llm/
│   └── utils/            # 🛠️ Helpers
```

**Benefícios:**
- ✅ **Testabilidade**: Cada camada testável isoladamente
- ✅ **Manutenibilidade**: Mudanças localizadas (ex: trocar banco)
- ✅ **Escalabilidade**: Fácil adicionar novos endpoints/features
- ✅ **Onboarding**: Devs novos entendem estrutura rapidamente

---

### 🎯 Desafio 5: Escolha do LLM

**❌ Opções Consideradas:**

| Modelo | Prós | Contras | Decisão |
|--------|------|---------|---------|
| **Ollama (Llama 3.1)** | Gratuito, offline, privacidade | Lento, alto consumo RAM, qualidade inferior | ❌ Rejeitado |
| **OpenAI GPT-4** | Alta qualidade, APIs robustas | Caro ($0.03/1K tokens) - chaves limitadas por conta | ❌ Rejeitado |
| **Google Gemini 2.0** | Rápido, barato, boa qualidade PT-BR | Modelo do Google, traz segurança sobre sua capacidade técnica e documentação | Facilidade para obter keys em uma mesma conta | ✅ **Escolhido** |

**✅ Por que Gemini 2.0 Flash?**

1. **Suporte PT-BR**
   - Treinado com dados em português
   - Compreende gírias e contexto cultural

2. **Function Calling**
   - Suporte nativo a ferramentas (Google ADK)
   - Parsing automático de argumentos

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

### ✅ Obrigatórios

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Docker Desktop** ([Download](https://www.docker.com/products/docker-desktop/))

### ✅ Recomendados

- **Visual Studio Code** ([Download](https://code.visualstudio.com/))
- **DBeaver/pgAdmin** (para visualizar banco)

### 📦 Verificação de Instalação

```powershell
# Verificar Python
python --version  # Deve mostrar 3.11+

# Verificar Docker
docker --version
docker-compose --version

# Verificar Git
git --version
```

---

## 🚀 Instalação Passo a Passo

### 📥 1. Clone o Repositório

```powershell
# Clone via HTTPS
git clone https://github.com/LuizFernandoCSilva/NegotiaAI.git

# OU via SSH (se configurado)
git clone git@github.com:LuizFernandoCSilva/NegotiaAI.git

# Entre no diretório
cd NegotiaAI
cd AgentAI
```

### 🔑 3. Obtenha a API Key do Google

1. **Acesse:** [Google AI Studio](https://aistudio.google.com/)
2. **Login:** Com sua conta Google
3. **Crie API Key:**
   - Clique em "Get API Key" (canto superior direito)
   - Selecione ou crie um projeto
   - Clique em "Create API Key"
4. **Copie a chave:** Vai parecer com `AIzaSyB...`

### ⚙️ 4. Configure Variáveis de Ambiente

Crie um arquivo `.env` na **raiz do projeto** (todas as variáveis em um único arquivo):

```powershell
# Criar .env a partir do exemplo
Copy-Item .env.example .env

# Editar no VS Code
code .env
```

**Arquivo `.env` completo (raiz do projeto):**

```env
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🗄️ CONFIGURAÇÃO DO BANCO DE DADOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POSTGRES_USER=negotiaai_user
POSTGRES_PASSWORD=Negotiaai2025Secure
POSTGRES_DB=negotiaai_db
POSTGRES_PORT=5432

DATABASE_URL=postgresql://negotiaai_user:Negotiaai2025Secure@localhost:5432/negotiaai_db

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🤖 CONFIGURAÇÃO DO GOOGLE GEMINI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cole sua API key aqui (obtida em aistudio.google.com)
GOOGLE_API_KEY=AIzaSy...SEU_KEY_AQUI...

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧠 CONFIGURAÇÃO DO LLM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LLM_MODEL=gemini-2.0-flash-exp
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2048

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 CONFIGURAÇÃO DO BACKEND
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SERVER_PORT=5000
APP_HOST=0.0.0.0
APP_PORT=5000

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎨 CONFIGURAÇÃO DO FRONTEND
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API_URL=http://localhost:5000
```

⚠️ **IMPORTANTE:** 
- Todas as variáveis estão em **um único arquivo** `.env` na raiz
- Não precisa criar `.env` separado no frontend
- O Docker Compose lê automaticamente o `.env` da raiz

### 🐍 5. Configure Ambiente Python

```powershell
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1
```

### 🐳 6. Inicie o Sistema

```powershell
#Build o sistema
docker-compose build --no-cache
# Suba o sistema
docker-compose up -d

```

### 🌱 7. Execute o Seed do Banco

```powershell
# Garantir que .venv está ativo
.\.venv\Scripts\Activate.ps1

# Executar seed
cd backend
docker-compose exec negotiaai-backend python backend/seed_runner.py
# Saída esperada:
# ✅ Tabelas criadas com sucesso!
# ✅ 3 clientes inseridos
# ✅ 9 planos de pagamento inseridos
```
# Verificar status
docker-compose ps

# Ver logs em tempo real
docker-compose logs -f

# Acessar aplicações:
# Backend: http://localhost:5000
# Docs: http://localhost:5000/api/docs
# Frontend: http://localhost:8501

# Cpf de usuários para teste: 30131864025 - João da Silva, 98765432100 - Maria Oliveira, 15263533004 - Carlos Pereira
```
## 📡 Endpoints da API

### 📖 Documentação Interativa

Após iniciar o backend, acesse:

- **Swagger UI (Recomendado):** http://localhost:5000/api/docs
  - Interface gráfica para testar endpoints
  - Exemplos de requisições
  - Modelos de dados

- **ReDoc:** http://localhost:5000/api/redoc
  - Documentação estilo livro
  - Melhor para leitura Oliveira**: 2 opções (1x, 2x) com desconto à vista

#### 🔄 Executar Seed Manualmente

```powershell
# Método 1: Via script dedicado
cd backend
python seed_runner.py

# Método 2: Via módulo Python
cd backend
python -c "from app.infrastructure.database.seed import run_seed; run_seed()"
```

---

## 🔧 Comandos Úteis

### 🐳 Docker Management

```powershell
# Verificar status dos containers
docker-compose ps

# Ver logs em tempo real
docker logs negotiaai-backend -f
docker logs negotiaai-db -f

# Reiniciar serviços específicos
docker-compose restart negotiaai-backend

# Parar todos os serviços
docker-compose down

# Parar e remover volumes ( apaga dados!)
docker-compose down -v

# Rebuild completo
docker-compose build --no-cache
docker-compose up -d
```

### 🗄️ Database Management

```powershell
# Conectar ao PostgreSQL
docker exec -it negotiaai-db psql -U negotiaai_user -d negotiaai_db

# Backup do banco
docker exec negotiaai-db pg_dump -U negotiaai_user negotiaai_db > backup.sql

# Restaurar backup
cat backup.sql | docker exec -i negotiaai-db psql -U negotiaai_user -d negotiaai_db

# Executar seed manualmente
cd backend
python seed_runner.py

# Limpar dados ( cuidado!)
docker exec -it negotiaai-db psql -U negotiaai_user -d negotiaai_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

<div align="center">

**🚀 Desenvolvido por Luiz Fernando**

</div>
