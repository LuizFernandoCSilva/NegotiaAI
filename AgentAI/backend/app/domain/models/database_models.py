"""
SQLAlchemy Models - BancoAgil
Schema do banco de dados usando SQLAlchemy ORM
"""
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Customer(Base):
    """
    Model de Cliente
    
    Armazena informações dos clientes devedores.
    """
    __tablename__ = 'Customer'
    
    id = Column(String, primary_key=True, doc="UUID único do cliente")
    cpf = Column(String, unique=True, nullable=False, index=True, doc="CPF do cliente (apenas números)")
    name = Column(String, nullable=False, doc="Nome completo")
    totalDebt = Column(Numeric(12, 2), nullable=False, doc="Dívida total em R$")
    profile = Column(String, nullable=False, doc="Perfil: Amigável ou Contencioso")
    createdAt = Column(DateTime, default=datetime.utcnow, doc="Data de criação")
    updatedAt = Column(DateTime, nullable=True, doc="Data de atualização")
    deactivatedAt = Column(DateTime, nullable=True, doc="Data de desativação")
    deletedAt = Column(DateTime, nullable=True, doc="Data de exclusão lógica")
    
    payment_plans = relationship("PaymentPlan", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")


class PaymentPlan(Base):
    """
    Model de Plano de Pagamento
    
    Define as condições de pagamento negociadas com o cliente.
    """
    __tablename__ = 'PaymentPlan'
    
    id = Column(String, primary_key=True, doc="UUID do plano")
    cpf = Column(String, ForeignKey('Customer.cpf', ondelete='CASCADE'), nullable=False, doc="CPF do cliente")
    installments = Column(Integer, nullable=False, doc="Número de parcelas")
    installmentAmount = Column(Numeric(12, 2), nullable=False, doc="Valor por parcela")
    totalPaid = Column(Numeric(12, 2), nullable=False, doc="Valor total a pagar")
    discountPercent = Column(Numeric(5, 2), nullable=False, default=0, doc="Percentual de desconto")
    createdAt = Column(DateTime, default=datetime.utcnow, doc="Data de criação")
    updatedAt = Column(DateTime, nullable=True, doc="Data de atualização")
    deactivatedAt = Column(DateTime, nullable=True, doc="Data de desativação")
    deletedAt = Column(DateTime, nullable=True, doc="Data de exclusão lógica")
    
    customer = relationship("Customer", back_populates="payment_plans")
    invoices = relationship("Invoice", back_populates="payment_plan", cascade="all, delete-orphan")


class Invoice(Base):
    """
    Model de Boleto/Fatura
    
    Representa um boleto bancário gerado para pagamento.
    """
    __tablename__ = 'Invoice'
    
    id = Column(String, primary_key=True, doc="UUID do boleto")
    cpf = Column(String, ForeignKey('Customer.cpf', ondelete='CASCADE'), nullable=False, doc="CPF do cliente")
    paymentPlanId = Column(String, ForeignKey('PaymentPlan.id', ondelete='CASCADE'), nullable=False, doc="ID do plano")
    digitableLine = Column(String, nullable=False, doc="Linha digitável do boleto")
    dueDate = Column(DateTime, nullable=False, doc="Data de vencimento")
    totalAmount = Column(Numeric(12, 2), nullable=False, doc="Valor total")
    status = Column(String, default='PENDING', doc="Status: PENDING, PAID, EXPIRED")
    createdAt = Column(DateTime, default=datetime.utcnow, doc="Data de criação")
    updatedAt = Column(DateTime, nullable=True, doc="Data de atualização")
    deactivatedAt = Column(DateTime, nullable=True, doc="Data de desativação")
    deletedAt = Column(DateTime, nullable=True, doc="Data de exclusão lógica")
    
    customer = relationship("Customer", back_populates="invoices")
    payment_plan = relationship("PaymentPlan", back_populates="invoices")
    receipts = relationship("Receipt", back_populates="invoice", cascade="all, delete-orphan")


class Receipt(Base):
    """
    Model de Comprovante de Pagamento
    
    Armazena comprovantes enviados pelos clientes após pagamento.
    """
    __tablename__ = 'Receipt'
    
    id = Column(String, primary_key=True, doc="UUID do comprovante")
    invoiceId = Column(String, ForeignKey('Invoice.id', ondelete='CASCADE'), nullable=False, doc="ID do boleto pago")
    filePath = Column(String, nullable=False, doc="Caminho do arquivo no servidor")
    originalName = Column(String, nullable=False, doc="Nome original do arquivo")
    receivedAt = Column(DateTime, default=datetime.utcnow, doc="Data de recebimento")
    updatedAt = Column(DateTime, nullable=True, doc="Data de atualização")
    deactivatedAt = Column(DateTime, nullable=True, doc="Data de desativação")
    deletedAt = Column(DateTime, nullable=True, doc="Data de exclusão lógica")
    
    invoice = relationship("Invoice", back_populates="receipts")
