"""
Database Seed - NegotiaAI
Script para popular o banco de dados com dados iniciais
"""
from decimal import Decimal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.domain.models.database_models import Base, Customer, PaymentPlan
from app.core.config import DatabaseConfig
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLIENTES_DB = {
    "30131864025": {
        "nome": "João da Silva",
        "divida_total": 1500.75,
        "perfil": "Amigável"
    },
    "98765432100": {
        "nome": "Maria Oliveira",
        "divida_total": 450.00,
        "perfil": "Contencioso"
    },
    "15263533004": {
        "nome": "Carlos Pereira",
        "divida_total": 3200.50,
        "perfil": "Amigável"
    }
}

PLANOS_DB = {
    "30131864025": [
        {"id_plano": "a1b2c3d4-1111-4111-8111-a1b2c3d4e5f1", "parcelas": 1,
         "valor_parcela": 1350.68, "total_pago": 1350.68, "desconto_percent": 10.0},
        {"id_plano": "a1b2c3d4-2222-4222-8222-a1b2c3d4e5f2", "parcelas": 3,
         "valor_parcela": 510.25, "total_pago": 1530.75, "desconto_percent": 0.0},
        {"id_plano": "a1b2c3d4-3333-4333-8333-a1b2c3d4e5f3", "parcelas": 6,
         "valor_parcela": 260.12, "total_pago": 1560.72, "desconto_percent": 0.0},
    ],
    "98765432100": [
        {"id_plano": "a1b2c3d4-4444-4444-8444-a1b2c3d4e5f4", "parcelas": 1,
         "valor_parcela": 427.50, "total_pago": 427.50, "desconto_percent": 5.0},
        {"id_plano": "a1b2c3d4-5555-4555-8555-a1b2c3d4e5f5", "parcelas": 2,
         "valor_parcela": 230.00, "total_pago": 460.00, "desconto_percent": 0.0},
    ],
    "15263533004": [
        {"id_plano": "a1b2c3d4-6666-4666-8666-a1b2c3d4e5f6", "parcelas": 1,
         "valor_parcela": 3000.00, "total_pago": 3000.00, "desconto_percent": 6.25},
        {"id_plano": "a1b2c3d4-7777-4777-8777-a1b2c3d4e5f7", "parcelas": 6,
         "valor_parcela": 550.00, "total_pago": 3300.00, "desconto_percent": 0.0},
        {"id_plano": "a1b2c3d4-8888-4888-8888-a1b2c3d4e5f8", "parcelas": 12,
         "valor_parcela": 280.00, "total_pago": 3360.00, "desconto_percent": 0.0},
        {"id_plano": "a1b2c3d4-9999-4999-8999-a1b2c3d4e5f9", "parcelas": 18,
         "valor_parcela": 190.00, "total_pago": 3420.00, "desconto_percent": 0.0},
    ]
}


def create_tables():
    """Cria as tabelas no banco de dados."""
    try:
        DATABASE_URL = DatabaseConfig.get_url()
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tabelas criadas com sucesso!")
        return engine
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        raise


def seed_customers(session):
    """Popula a tabela de clientes."""
    logger.info("📊 Populando tabela de clientes...")
    
    for cpf, dados in CLIENTES_DB.items():
        # Verifica se o cliente já existe
        existing_customer = session.query(Customer).filter_by(cpf=cpf).first()
        if existing_customer:
            logger.info(f"⚠️  Cliente {dados['nome']} (CPF: {cpf}) já existe. Pulando...")
            continue
        
        # Cria novo cliente com UUID
        customer = Customer(
            id=str(uuid.uuid4()),
            cpf=cpf,
            name=dados['nome'],
            totalDebt=Decimal(str(dados['divida_total'])),
            profile=dados['perfil']
        )
        
        session.add(customer)
        logger.info(f"✅ Cliente adicionado: {dados['nome']} (CPF: {cpf})")
    
    session.commit()
    logger.info("✅ Clientes inseridos com sucesso!")


def seed_payment_plans(session):
    """Popula a tabela de planos de pagamento."""
    logger.info("💰 Populando tabela de planos de pagamento...")
    
    for cpf, planos in PLANOS_DB.items():
        # Verifica se o cliente existe
        customer = session.query(Customer).filter_by(cpf=cpf).first()
        if not customer:
            logger.warning(f"⚠️  Cliente com CPF {cpf} não encontrado. Pulando planos...")
            continue
        
        for plano in planos:
            # Verifica se o plano já existe
            existing_plan = session.query(PaymentPlan).filter_by(id=plano['id_plano']).first()
            if existing_plan:
                logger.info(f"⚠️  Plano {plano['id_plano']} já existe. Pulando...")
                continue
            
            # Cria novo plano
            payment_plan = PaymentPlan(
                id=plano['id_plano'],
                cpf=cpf,
                installments=plano['parcelas'],
                installmentAmount=Decimal(str(plano['valor_parcela'])),
                totalPaid=Decimal(str(plano['total_pago'])),
                discountPercent=Decimal(str(plano['desconto_percent']))
            )
            
            session.add(payment_plan)
            logger.info(f"✅ Plano adicionado: {plano['parcelas']}x de R$ {plano['valor_parcela']} para {customer.name}")
    
    session.commit()
    logger.info("✅ Planos de pagamento inseridos com sucesso!")


def run_seed():
    """Executa o processo completo de seed do banco."""
    logger.info("🚀 Iniciando processo de seed do banco de dados...")
    
    try:
        # Criar tabelas
        engine = create_tables()
        
        # Criar sessão
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            # Seed clientes
            seed_customers(session)
            
            # Seed planos de pagamento
            seed_payment_plans(session)
            
            logger.info("🎉 Processo de seed concluído com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro durante o seed: {e}")
            session.rollback()
            raise
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"❌ Erro fatal no processo de seed: {e}")
        raise


def check_data():
    """Verifica os dados inseridos no banco."""
    logger.info("🔍 Verificando dados inseridos...")
    
    try:
        DATABASE_URL = DatabaseConfig.get_url()
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        try:
            # Contar clientes
            customer_count = session.query(Customer).count()
            logger.info(f"📊 Total de clientes: {customer_count}")
            
            # Contar planos
            plan_count = session.query(PaymentPlan).count()
            logger.info(f"💰 Total de planos: {plan_count}")
            
            # Listar clientes
            customers = session.query(Customer).all()
            for customer in customers:
                plans = session.query(PaymentPlan).filter_by(cpf=customer.cpf).count()
                logger.info(f"👤 {customer.name} (CPF: {customer.cpf}) - {plans} planos")
                
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Erro ao verificar dados: {e}")


if __name__ == "__main__":
    run_seed()
    check_data()