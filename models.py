from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return Client.query.get(int(user_id))

# --- Clientes / Usuários (Barbeiros também ficam aqui) ---
class Client(db.Model, UserMixin):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default='customer', nullable=False) # 'customer' ou 'barber'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    # Agendamentos onde este usuário é o CLIENTE
    appointments = db.relationship('Appointment', backref='client', foreign_keys='Appointment.client_id', lazy=True)
    # Agendamentos onde este usuário é o BARBEIRO
    work_schedule = db.relationship('Appointment', backref='barber', foreign_keys='Appointment.barber_id', lazy=True)
    # Horários de trabalho (se for barbeiro)
    working_hours = db.relationship('WorkingHours', backref='barber', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

# --- Serviços ---
class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    appointments = db.relationship('Appointment', backref='service', lazy=True)

# --- Horários de Trabalho ---
class WorkingHours(db.Model):
    __tablename__ = 'working_hours'
    id = db.Column(db.Integer, primary_key=True)
    barber_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False) # Vincula o horário ao barbeiro
    day_of_week = db.Column(db.Integer, nullable=False) # 0=Segunda, 6=Domingo
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

# --- Agendamentos ---
class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    
    # Quem vai cortar
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    # Quem vai atender (O Barbeiro selecionado)
    barber_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), default='CONFIRMED', nullable=False) # CONFIRMED, COMPLETED, NO_SHOW, CANCELED
    
    # Campos para o fechamento de conta (Pop-up do Barbeiro)
    payment_method = db.Column(db.String(50), nullable=True) # PIX, Dinheiro, etc
    extra_services = db.Column(db.Text, nullable=True) # Lista de serviços adicionais em texto
    total_value = db.Column(db.Numeric(10, 2), nullable=True) # Valor final com os extras
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)