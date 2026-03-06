from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Date, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from datetime import datetime, date
from typing import List, Optional, Tuple, Dict, Any
import os

# SQLAlchemy setup
Base = declarative_base()

class TaxTable(Base):
    """Represents a tax table (e.g., Monthly, Quarterly)"""
    __tablename__ = 'tables'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    
    # Relationship to dates
    dates = relationship("TaxDate", back_populates="table", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TaxTable(name='{self.name}', description='{self.description}')>"

class TaxDate(Base):
    """Represents a tax date in a specific table"""
    __tablename__ = 'tax_dates'
    
    id = Column(Integer, primary_key=True)
    table_name = Column(String(50), ForeignKey('tables.name'), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    day = Column(Integer, nullable=False)    # 1-31
    description = Column(String(200))
    
    # Relationship to table
    table = relationship("TaxTable", back_populates="dates")
    payments = relationship("TaxPayment", back_populates="tax_date", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TaxDate(table='{self.table_name}', month={self.month}, day={self.day}, description='{self.description}')>"

class TaxPayment(Base):
    """Represents a record of a tax payment"""
    __tablename__ = 'tax_payments'
    
    id = Column(Integer, primary_key=True)
    tax_date_id = Column(Integer, ForeignKey('tax_dates.id'), nullable=False)
    year = Column(Integer, nullable=False)
    payment_date = Column(Date, default=date.today)
    
    # Relationship to tax date
    tax_date = relationship("TaxDate", back_populates="payments")

    def __repr__(self):
        return f"<TaxPayment(tax_date_id={self.tax_date_id}, year={self.year}, payment_date='{self.payment_date}')>"

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, db_url: str = None):
        import sys
        import os
        
        # Si no se proporciona una URL de base de datos, usar la ruta correcta
        if db_url is None:
            # Obtener el directorio base (diferente si es un ejecutable o no)
            if getattr(sys, 'frozen', False):
                # Si es un ejecutable
                base_dir = os.path.dirname(sys.executable)
            else:
                # Si se ejecuta desde el código fuente
                base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Crear la ruta completa al archivo de la base de datos
            db_path = os.path.join(base_dir, 'tax_reminder.db')
            db_url = f'sqlite:///{db_path}'
            
            # Asegurarse de que el directorio existe
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        print(f"Conectando a la base de datos en: {db_url}")
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_db(self) -> Session:
        """Get a database session"""
        db = self.SessionLocal()
        try:
            return db
        finally:
            db.close()
    
    def add_table(self, name: str, description: str = None) -> bool:
        """Add a new tax table"""
        with self.get_db() as db:
            if db.query(TaxTable).filter(TaxTable.name == name).first():
                return False  # Table already exists
            
            table = TaxTable(name=name, description=description)
            db.add(table)
            db.commit()
            return True
    
    def add_date(self, table_name: str, month: int, day: int, description: str = None) -> bool:
        """Add a new tax date to a table"""
        with self.get_db() as db:
            # Check if table exists
            table = db.query(TaxTable).filter(TaxTable.name == table_name).first()
            if not table:
                return False
                
            # Check if date already exists
            existing = db.query(TaxDate).filter(
                TaxDate.table_name == table_name,
                TaxDate.month == month,
                TaxDate.day == day
            ).first()
            
            if existing:
                return False  # Date already exists
                
            tax_date = TaxDate(
                table_name=table_name,
                month=month,
                day=day,
                description=description
            )
            db.add(tax_date)
            db.commit()
            return True
    
    def check_today(self) -> List[Dict[str, Any]]:
        """Check for any tax dates due today"""
        today = date.today()
        return self.get_dates_by_month_day(today.month, today.day)
        
    def check_date(self, month: int, day: int) -> List[Dict[str, Any]]:
        """Check for tax dates on a specific month and day
        
        Args:
            month: Month (1-12)
            day: Day of month (1-31)
            
        Returns:
            List of dictionaries containing tax date information
        """
        return self.get_dates_by_month_day(month, day)

    def get_dates_by_month_day(self, month: int, day: int) -> List[Dict[str, Any]]:
        """Get all tax dates for a specific month and day"""
        with self.get_db() as db:
            # Usar el nombre correcto de la tabla 'tables' en lugar de 'tax_tables'
            results = db.query(TaxDate, TaxTable.description).join(
                TaxTable, TaxDate.table_name == TaxTable.name
            ).filter(
                TaxDate.month == month,
                TaxDate.day == day
            ).all()
            
            return [{
                'id': date_obj.id,
                'table': date_obj.table_name,
                'table_description': table_desc,
                'month': date_obj.month,
                'day': date_obj.day,
                'description': date_obj.description
            } for date_obj, table_desc in results]
    
    def get_dates_for_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Get all dates for a specific table"""
        with self.get_db() as db:
            dates = db.query(TaxDate).filter(
                TaxDate.table_name == table_name
            ).order_by(
                TaxDate.month, TaxDate.day
            ).all()
            
            return [{
                'id': d.id,
                'month': d.month,
                'day': d.day,
                'description': d.description
            } for d in dates]
            
    def clean_database(self) -> bool:
        """Remove all data from the database"""
        try:
            with self.get_db() as db:
                # Delete all dates first (due to foreign key constraint)
                db.query(TaxDate).delete()
                # Then delete all tables
                db.query(TaxTable).delete()
                db.commit()
                # Recreate default tables
                self.create_tables()
                return True
        except Exception as e:
            print(f"Error cleaning database: {e}")
            db.rollback()
            return False
    
    def delete_date(self, date_id: int) -> bool:
        """Delete a tax date by ID"""
        with self.get_db() as db:
            date_obj = db.query(TaxDate).filter(TaxDate.id == date_id).first()
            if not date_obj:
                return False
                
            db.delete(date_obj)
            db.commit()
            return True

    def mark_as_paid(self, tax_date_id: int, year: int) -> bool:
        """Mark a tax as paid for a specific year"""
        with self.get_db() as db:
            # Check if tax date exists
            tax_date = db.query(TaxDate).filter(TaxDate.id == tax_date_id).first()
            if not tax_date:
                return False
                
            # Check if already paid
            existing = db.query(TaxPayment).filter(
                TaxPayment.tax_date_id == tax_date_id,
                TaxPayment.year == year
            ).first()
            
            if existing: # Update date
                existing.payment_date = date.today()
            else:
                payment = TaxPayment(tax_date_id=tax_date_id, year=year)
                db.add(payment)
                
            db.commit()
            return True

    def unmark_as_paid(self, payment_id: int) -> bool:
        """Remove a payment record"""
        with self.get_db() as db:
            payment = db.query(TaxPayment).filter(TaxPayment.id == payment_id).first()
            if not payment:
                return False
                
            db.delete(payment)
            db.commit()
            return True

    def is_paid(self, tax_date_id: int, year: int) -> bool:
        """Check if a tax is marked as paid for a specific year"""
        with self.get_db() as db:
            payment = db.query(TaxPayment).filter(
                TaxPayment.tax_date_id == tax_date_id,
                TaxPayment.year == year
            ).first()
            return payment is not None

    def get_payment_history(self, year: int = None) -> List[Dict[str, Any]]:
        """Get payment history, optionally filtered by year"""
        with self.get_db() as db:
            query = db.query(TaxPayment, TaxDate, TaxTable.description).join(
                TaxDate, TaxPayment.tax_date_id == TaxDate.id
            ).join(
                TaxTable, TaxDate.table_name == TaxTable.name
            )
            
            if year is not None:
                query = query.filter(TaxPayment.year == year)
                
            results = query.order_by(TaxPayment.payment_date.desc()).all()
            
            return [{
                'payment_id': payment.id,
                'tax_date_id': tdate.id,
                'table': tdate.table_name,
                'table_description': tdesc,
                'month': tdate.month,
                'day': tdate.day,
                'description': tdate.description,
                'year': payment.year,
                'payment_date': payment.payment_date.isoformat()
            } for payment, tdate, tdesc in results]
