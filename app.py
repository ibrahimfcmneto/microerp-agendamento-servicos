from flask import Flask
from config import Config
from models import db, login_manager, bcrypt, Client 
from routes import init_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa as extensões
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'login' 
    login_manager.login_message = "Por favor, faça login para acessar esta página."

    init_routes(app)

    # --- CORREÇÃO: FORÇAR A CRIAÇÃO OU ATUALIZAÇÃO DO ADMIN ---
    with app.app_context():
        db.create_all()

        admin_email = "admin@barbearia.com"
        senha_padrao = "admin123"
        
        # Procura se o admin já existe
        admin = Client.query.filter_by(email=admin_email).first()

        if not admin:
            # Se não existe, cria do zero
            print("⚠️ Admin não encontrado. Criando novo...")
            admin = Client(name="Gestor", email=admin_email, phone="000000000")
            admin.set_password(senha_padrao)
            db.session.add(admin)
            print("✅ Conta criada!")
        else:
            # Se JÁ existe, ATUALIZA a senha para garantir que está certa
            print("⚠️ Admin já existe. Atualizando senha para o padrão...")
            admin.set_password(senha_padrao)
            print("✅ Senha atualizada!")

        db.session.commit()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)