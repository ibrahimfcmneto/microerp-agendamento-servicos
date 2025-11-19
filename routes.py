from flask import render_template, request, redirect, url_for
from models import db, Service

def init_routes(app):

    # --- Rota da Página Inicial (Temporária) ---
    @app.route('/')
    def index():
        return """
        <h1>Bem-vindo ao MicroERP!</h1>
        <p>Sistema de Agendamento Simplificado</p>
        <hr>
        <a href='/services'>👉 Gerenciar Serviços (CRUD)</a>
        """

    # --- Rota: Listar Serviços (READ) ---
    @app.route('/services')
    def list_services():
        # Busca todos os serviços no banco de dados
        services = Service.query.all()
        
        # HTML simples misturado no código (apenas para este teste inicial)
        html = "<h2>📋 Serviços Cadastrados</h2>"
        html += "<p><a href='/services/new'>➕ Adicionar Novo Serviço</a></p>"
        html += "<hr>"
        html += "<ul>"
        for s in services:
            html += f"<li><b>{s.name}</b> - {s.duration_minutes} min - R$ {s.price} "
            html += f"[<a href='/services/delete/{s.id}' style='color:red'>Excluir</a>]</li>"
        html += "</ul>"
        html += "<br><a href='/'>🏠 Voltar ao Início</a>"
        return html

    # --- Rota: Adicionar Serviço (CREATE) ---
    @app.route('/services/new', methods=['GET', 'POST'])
    def create_service():
        if request.method == 'POST':
            # Pega os dados digitados no formulário
            name = request.form.get('name')
            duration = request.form.get('duration')
            price = request.form.get('price')
            
            # Cria o objeto e salva no Banco
            new_service = Service(name=name, duration_minutes=duration, price=price)
            db.session.add(new_service)
            db.session.commit()
            
            return redirect(url_for('list_services'))
        
        # Se for GET, mostra o formulário
        return """
        <h2>Novo Serviço</h2>
        <form method="POST">
            <label>Nome do Serviço:</label><br>
            <input type="text" name="name" placeholder="Ex: Corte de Cabelo" required><br><br>
            
            <label>Duração (minutos):</label><br>
            <input type="number" name="duration" placeholder="30" required><br><br>
            
            <label>Preço (R$):</label><br>
            <input type="number" step="0.01" name="price" placeholder="25.00" required><br><br>
            
            <button type="submit">Salvar Serviço</button>
        </form>
        <br><a href='/services'>Cancelar</a>
        """

    # --- Rota: Deletar Serviço (DELETE) ---
    @app.route('/services/delete/<int:id>')
    def delete_service(id):
        # Busca o serviço pelo ID ou dá erro 404 se não achar
        service = Service.query.get_or_404(id)
        
        db.session.delete(service)
        db.session.commit()
        return redirect(url_for('list_services'))