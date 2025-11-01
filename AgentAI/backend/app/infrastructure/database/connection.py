from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.domain.models.database_models import Base, Customer, PaymentPlan, Invoice, Receipt
from app.core.config import DatabaseConfig

logger = logging.getLogger(__name__)


DATABASE_URL = DatabaseConfig.get_url()

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _normalize_cpf(cpf: str) -> str:
    return "".join(filter(str.isdigit, cpf or ""))


def _decimal_to_float(value: Optional[Decimal]) -> Optional[float]:
    return float(value) if value is not None else None


def init_db() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        
        session = SessionLocal()
        try:
            customer_count = session.query(Customer).count()
            if customer_count == 0:
                from app.infrastructure.database.seed import run_seed
                run_seed()
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {e}")
        pass


def obter_cliente(cpf: str) -> Optional[Dict]:
    """Busca um cliente por CPF."""
    cpf_limpo = _normalize_cpf(cpf)
    session = SessionLocal()
    try:
        customer = session.query(Customer).filter_by(cpf=cpf_limpo).first()
        if not customer:
            return None
        
        return {
            "cpf": customer.cpf,
            "nome": customer.name,
            "divida_total": _decimal_to_float(customer.totalDebt),
            "perfil": customer.profile,
        }
    finally:
        session.close()


def obter_planos(cpf: str) -> List[Dict]:
    """Busca todos os planos de pagamento de um cliente."""
    cpf_limpo = _normalize_cpf(cpf)
    session = SessionLocal()
    try:
        plans = session.query(PaymentPlan).filter_by(cpf=cpf_limpo).order_by(PaymentPlan.installments).all()
        
        return [{
            "id_plano": plan.id,
            "cpf": plan.cpf,
            "parcelas": plan.installments,
            "valor_parcela": _decimal_to_float(plan.installmentAmount),
            "total_pago": _decimal_to_float(plan.totalPaid),
            "desconto_percent": _decimal_to_float(plan.discountPercent),
        } for plan in plans]
    finally:
        session.close()


def obter_plano_a_vista(cpf: str) -> Optional[Dict]:
    """Busca o melhor plano à vista (1 parcela) com maior desconto."""
    cpf_limpo = _normalize_cpf(cpf)
    session = SessionLocal()
    try:
        plan = session.query(PaymentPlan).filter_by(
            cpf=cpf_limpo, 
            installments=1
        ).order_by(PaymentPlan.discountPercent.desc()).first()
        
        if not plan:
            return None
        
        return {
            "id_plano": plan.id,
            "cpf": plan.cpf,
            "parcelas": plan.installments,
            "valor_parcela": _decimal_to_float(plan.installmentAmount),
            "total_pago": _decimal_to_float(plan.totalPaid),
            "desconto_percent": _decimal_to_float(plan.discountPercent),
        }
    finally:
        session.close()


def obter_plano_por_parcelas(cpf: str, parcelas_desejadas: int) -> Optional[Dict]:
    """Busca plano com número exato de parcelas."""
    cpf_limpo = _normalize_cpf(cpf)
    session = SessionLocal()
    try:
        plan = session.query(PaymentPlan).filter_by(
            cpf=cpf_limpo,
            installments=parcelas_desejadas
        ).first()
        
        if not plan:
            return None
        
        return {
            "id_plano": plan.id,
            "cpf": plan.cpf,
            "parcelas": plan.installments,
            "valor_parcela": _decimal_to_float(plan.installmentAmount),
            "total_pago": _decimal_to_float(plan.totalPaid),
            "desconto_percent": _decimal_to_float(plan.discountPercent),
        }
    finally:
        session.close()


def obter_plano_por_valor(cpf: str, valor_desejado: float) -> Optional[Dict]:
    """Busca plano mais próximo do valor desejado."""
    cpf_limpo = _normalize_cpf(cpf)
    session = SessionLocal()
    try:
        plans = session.query(PaymentPlan).filter_by(cpf=cpf_limpo).all()
        
        if not plans:
            return None
        
        plan = min(plans, key=lambda p: abs(float(p.installmentAmount) - valor_desejado))
        
        return {
            "id_plano": plan.id,
            "cpf": plan.cpf,
            "parcelas": plan.installments,
            "valor_parcela": _decimal_to_float(plan.installmentAmount),
            "total_pago": _decimal_to_float(plan.totalPaid),
            "desconto_percent": _decimal_to_float(plan.discountPercent),
        }
    finally:
        session.close()


def registrar_boleto(cpf: str, id_plano: str, linha_digitavel: str, data_vencimento: datetime, valor_total: float, id_boleto: Optional[str] = None) -> Optional[Dict]:
    """Registra um novo boleto."""
    import uuid
    cpf_limpo = _normalize_cpf(cpf)
    session = SessionLocal()
    try:
        plan = session.query(PaymentPlan).filter_by(id=id_plano, cpf=cpf_limpo).first()
        if not plan:
            return None
        
        if not id_boleto:
            id_boleto = str(uuid.uuid4())
        
        invoice = Invoice(
            id=id_boleto,
            cpf=cpf_limpo,
            paymentPlanId=id_plano,
            digitableLine=linha_digitavel,
            dueDate=data_vencimento,
            totalAmount=Decimal(str(valor_total)),
            status='PENDING',
            createdAt=datetime.utcnow()
        )
        
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        
        return {
            "id_boleto": invoice.id,
            "cpf": invoice.cpf,
            "id_plano": invoice.paymentPlanId,
            "linha_digitavel": invoice.digitableLine,
            "data_vencimento": invoice.dueDate.isoformat(),
            "valor_total": _decimal_to_float(invoice.totalAmount),
            "status": invoice.status,
            "criado_em": invoice.createdAt.isoformat(),
        }
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def listar_boletos(cpf: str) -> List[Dict]:
    """Lista todos os boletos de um CPF."""
    cpf_limpo = _normalize_cpf(cpf)
    session = SessionLocal()
    try:
        invoices = session.query(Invoice).filter_by(cpf=cpf_limpo).order_by(Invoice.createdAt.desc()).all()
        
        return [{
            "id_boleto": inv.id,
            "cpf": inv.cpf,
            "id_plano": inv.paymentPlanId,
            "linha_digitavel": inv.digitableLine,
            "data_vencimento": inv.dueDate.isoformat(),
            "valor_total": _decimal_to_float(inv.totalAmount),
            "status": inv.status,
            "criado_em": inv.createdAt.isoformat(),
        } for inv in invoices]
    finally:
        session.close()


def listar_todos_boletos(limit: int = 10) -> List[Dict]:
    """Lista todos os boletos recentes (sem filtro por CPF)."""
    session = SessionLocal()
    try:
        invoices = session.query(Invoice).order_by(Invoice.createdAt.desc()).limit(limit).all()
        
        return [{
            "id": inv.id,
            "cpf": inv.cpf,
            "totalAmount": _decimal_to_float(inv.totalAmount),
            "dueDate": inv.dueDate.isoformat(),
            "status": inv.status,
            "createdAt": inv.createdAt.isoformat(),
        } for inv in invoices]
    finally:
        session.close()


def obter_boleto(boleto_id: str) -> Optional[Dict]:
    """Obtém informações de um boleto específico pelo ID."""
    session = SessionLocal()
    try:
        invoice = session.query(Invoice).filter_by(id=boleto_id).first()
        if not invoice:
            return None
        
        return {
            "id_boleto": invoice.id,
            "cpf": invoice.cpf,
            "id_plano": invoice.paymentPlanId,
            "linha_digitavel": invoice.digitableLine,
            "data_vencimento": invoice.dueDate.isoformat(),
            "valor_total": _decimal_to_float(invoice.totalAmount),
            "status": invoice.status,
            "criado_em": invoice.createdAt.isoformat(),
        }
    finally:
        session.close()


def registrar_comprovante(boleto_id: str, file_path: str, original_name: str) -> Optional[Dict]:
    """Registra comprovante de pagamento."""
    import uuid
    session = SessionLocal()
    try:
        invoice = session.query(Invoice).filter_by(id=boleto_id).first()
        if not invoice:
            return None
        
        receipt = Receipt(
            id=str(uuid.uuid4()),
            invoiceId=boleto_id,
            filePath=file_path,
            originalName=original_name,
            receivedAt=datetime.utcnow()
        )
        
        session.add(receipt)
        session.commit()
        session.refresh(receipt)
        
        return {
            "id_comprovante": receipt.id,
            "id_boleto": receipt.invoiceId,
            "caminho_arquivo": receipt.filePath,
            "nome_original": receipt.originalName,
            "recebido_em": receipt.receivedAt.isoformat(),
        }
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
