from flask import Flask
from config import Config
from models import db, login_manager, bcrypt, Client 
from routes import init_routes
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa as extensões
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'login' 
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    init_routes(app)

    # --- CONFIGURAÇÃO AUTOMÁTICA DO BANCO E ADMIN ---
    with app.app_context():
        # db.drop_all() 
        
        # Garante que as tabelas existam sem apagar os dados atuais
        db.create_all() 

        admin_email = app.config.get('ADMIN_EMAIL')
        senha_padrao = app.config.get('ADMIN_PASSWORD')
        
        if not admin_email or not senha_padrao:
            print("❌ ERRO: ADMIN_EMAIL ou ADMIN_PASSWORD não encontrados no .env")
            return app

        try:
            admin = Client.query.filter_by(email=admin_email).first()

            if not admin:
                print(f"⚠️ Criando novo Admin: {admin_email}")
                admin = Client(
                    name="Gestor", 
                    email=admin_email, 
                    phone="000000000",
                    role="barber" 
                )
                admin.set_password(senha_padrao)
                db.session.add(admin)
                db.session.commit()
                print("✅ Conta do administrador criada com sucesso!")
            # else:
            #    print("ℹ️ Admin já existe no banco.")

        except Exception as e:
            print(f"❌ Erro crítico: {e}")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)