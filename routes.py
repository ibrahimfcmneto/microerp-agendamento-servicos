from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Service, Client, WorkingHours, Appointment
from datetime import datetime, timedelta, date

def init_routes(app):

# --- PÁGINA INICIAL ---
    @app.route('/')
    def index():
        # Simples assim! O Python vai buscar o arquivo templates/index.html
        return render_template('index.html')

# --- REGISTRO DE CLIENTES (Visual Novo) ---
# --- REGISTRO DE CLIENTES (Com Flash Message) ---
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            phone = request.form.get('phone')

            if Client.query.filter_by(email=email).first():
                # AQUI A MUDANÇA: Usa flash em vez de retornar HTML
                flash('Este email já está cadastrado. Tente fazer login.', 'error')
                return redirect(url_for('register'))

            new_client = Client(name=name, email=email, phone=phone)
            new_client.set_password(password)
            
            db.session.add(new_client)
            db.session.commit()

            flash('Conta criada com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    # --- LOGIN (Visual Novo) ---
# --- LOGIN (Com Flash Message) ---
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = Client.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                login_user(user)
                # Redireciona gestor para dashboard, cliente para home
                if user.email == "admin@barbearia.com":
                    return redirect(url_for('dashboard'))
                return redirect(url_for('index'))
            else:
                # AQUI A MUDANÇA: Mensagem de erro elegante
                flash('Email ou senha incorretos.', 'error')
                return redirect(url_for('login'))
        
        return render_template('login.html')
    
    # --- LOGOUT ---
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    # --- SETUP ADMIN (Cria o Gestor) ---
    @app.route('/setup-admin')
    def setup_admin():
        if Client.query.filter_by(email="admin@barbearia.com").first():
            return "Admin já existe!"
            
        admin = Client(name="Gestor", email="admin@barbearia.com", phone="000000000")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        return "✅ Gestor criado com sucesso! Email: admin@barbearia.com | Senha: admin123"
    

    # --- ROTA DE CONFIGURAÇÃO RÁPIDA (Executar uma vez) ---
    from models import WorkingHours
    from datetime import time

    @app.route('/setup-hours')
    @login_required
    def setup_hours():
        # Segurança: Só o admin pode fazer isso
        if current_user.email != "admin@barbearia.com":
            return "Acesso Negado"
        
        # Limpa horários antigos para não duplicar
        WorkingHours.query.delete()
        
        # Cria horários de Segunda (0) a Sexta (4)
        # 09:00 às 18:00
        horarios = []
        dias_semana = [0, 1, 2, 3, 4] # 0=Seg, 4=Sex
        
        for dia in dias_semana:
            # Manhã: 09:00 às 12:00
            h1 = WorkingHours(day_of_week=dia, start_time=time(9,0), end_time=time(12,0))
            # Tarde: 13:00 às 18:00
            h2 = WorkingHours(day_of_week=dia, start_time=time(13,0), end_time=time(18,0))
            
            db.session.add(h1)
            db.session.add(h2)
            
        db.session.commit()
        return "✅ Horários de Funcionamento (Seg-Sex, 09-18h) configurados com sucesso!"


# --- CRUD DE HORÁRIOS (Com Almoço/Dois Turnos) ---
    @app.route('/working_hours', methods=['GET', 'POST'])
    @login_required
    def manage_working_hours():
        if current_user.email != "admin@barbearia.com":
            return redirect(url_for('index'))

        if request.method == 'POST':
            WorkingHours.query.delete()
            
            for i in range(7):
                if not request.form.get(f'closed_{i}'):
                    # Turno 1
                    s1 = request.form.get(f'start1_{i}')
                    e1 = request.form.get(f'end1_{i}')
                    if s1 and e1:
                        db.session.add(WorkingHours(day_of_week=i, 
                                     start_time=datetime.strptime(s1, '%H:%M').time(), 
                                     end_time=datetime.strptime(e1, '%H:%M').time()))
                    # Turno 2
                    s2 = request.form.get(f'start2_{i}')
                    e2 = request.form.get(f'end2_{i}')
                    if s2 and e2:
                        db.session.add(WorkingHours(day_of_week=i, 
                                     start_time=datetime.strptime(s2, '%H:%M').time(), 
                                     end_time=datetime.strptime(e2, '%H:%M').time()))
            
            db.session.commit()
            flash('Horários atualizados com sucesso!', 'success')
            return redirect(url_for('dashboard'))

        # PREPARAÇÃO DOS DADOS PARA O TEMPLATE
        # Precisamos organizar os dados numa lista limpa para o HTML ler fácil
        existing_hours = WorkingHours.query.order_by(WorkingHours.day_of_week, WorkingHours.start_time).all()
        hours_map = {}
        for h in existing_hours:
            if h.day_of_week not in hours_map: hours_map[h.day_of_week] = []
            hours_map[h.day_of_week].append(h)

        dias_nomes = {0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira', 3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'}
        
        days_data = []
        for i in range(7):
            periods = hours_map.get(i, [])
            day_info = {
                'id': i,
                'name': dias_nomes[i],
                'is_closed': len(periods) == 0,
                # Valores padrão ou do banco
                's1': periods[0].start_time.strftime('%H:%M') if len(periods) > 0 else "09:00",
                'e1': periods[0].end_time.strftime('%H:%M') if len(periods) > 0 else "12:00",
                's2': periods[1].start_time.strftime('%H:%M') if len(periods) > 1 else "13:00",
                'e2': periods[1].end_time.strftime('%H:%M') if len(periods) > 1 else "18:00",
            }
            days_data.append(day_info)

        return render_template('working_hours.html', days_data=days_data)

    # ==================================================
    # ÁREA ADMINISTRATIVA (PROTEGIDA EXTRA)
    # ==================================================

    @app.route('/services')
    @login_required
    def list_services():
        # SEGURANÇA: Só o admin pode ver isso
        if current_user.email != "admin@barbearia.com":
            return "<h1>Acesso Negado!</h1> <p>Apenas o gestor pode acessar esta área.</p> <a href='/'>Voltar</a>"

        services = Service.query.all()
        html = "<h2>📋 Serviços Cadastrados (Modo Gestor)</h2>"
        html += "<p><a href='/services/new'>➕ Adicionar Novo Serviço</a></p>"
        html += "<ul>"
        for s in services:
            html += f"<li><b>{s.name}</b> - R$ {s.price} [<a href='/services/delete/{s.id}'>Excluir</a>]</li>"
        html += "</ul>"
        html += "<br><a href='/'>🏠 Voltar</a>"
        return html

    @app.route('/services/new', methods=['GET', 'POST'])
    @login_required
    def create_service():
        # SEGURANÇA
        if current_user.email != "admin@barbearia.com":
            return "Acesso Negado"

        if request.method == 'POST':
            new_service = Service(
                name=request.form.get('name'), 
                duration_minutes=request.form.get('duration'), 
                price=request.form.get('price')
            )
            db.session.add(new_service)
            db.session.commit()
            return redirect(url_for('list_services'))
        
        return """
        <h2>Novo Serviço</h2>
        <form method="POST">
            Nome: <input type="text" name="name" required><br>
            Duração (min): <input type="number" name="duration" required><br>
            Preço: <input type="number" step="0.01" name="price" required><br>
            <button type="submit">Salvar</button>
        </form>
        """

    @app.route('/services/delete/<int:id>')
    @login_required
    def delete_service(id):
        # SEGURANÇA
        if current_user.email != "admin@barbearia.com":
            return "Acesso Negado"

        service = Service.query.get_or_404(id)
        db.session.delete(service)
        db.session.commit()
        return redirect(url_for('list_services'))
    

    # ==================================================
    # ÁREA DO CLIENTE (FLUXO DE AGENDAMENTO)
    # ==================================================

# --- PASSO 1: ESCOLHER SERVIÇO (Com Template) ---
    @app.route('/book')
    @login_required
    def book_service():
        services = Service.query.all()
        return render_template('book_service.html', services=services)

    # --- PASSO 2: ESCOLHER HORÁRIO (Com Template) ---
    @app.route('/book/<int:service_id>')
    @login_required
    def book_time(service_id):
        service = Service.query.get_or_404(service_id)
        
        date_str = request.args.get('date')
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selected_date = date.today()

        day_of_week = selected_date.weekday()
        working_hours = WorkingHours.query.filter_by(day_of_week=day_of_week).all()
        
        existing_appointments = Appointment.query.filter(
            db.func.date(Appointment.start_time) == selected_date
        ).all()
        
        busy_times = [app.start_time.time() for app in existing_appointments]
        now = datetime.now()
        available_slots = []

        for period in working_hours:
            current_time = datetime.combine(selected_date, period.start_time)
            end_time = datetime.combine(selected_date, period.end_time)
            
            while current_time + timedelta(minutes=service.duration_minutes) <= end_time:
                if current_time > now:
                    if current_time.time() not in busy_times:
                        available_slots.append(current_time)
                current_time += timedelta(minutes=30)

        # Renderiza o template passando as variáveis necessárias
        return render_template('book_time.html', 
                               service=service, 
                               selected_date=selected_date, 
                               available_slots=available_slots,
                               today=date.today())

    # --- PASSO 3: CONFIRMAÇÃO (Com Template) ---
# --- PASSO 3: CONFIRMAÇÃO (Com Flash Message) ---
    @app.route('/book/confirm/<int:service_id>/<string:slot>')
    @login_required
    def confirm_booking(service_id, slot):
        service = Service.query.get_or_404(service_id)
        booking_time = datetime.strptime(slot, '%Y-%m-%d_%H-%M-%S')
        
        # Validações com Flash
        if booking_time < datetime.now():
             flash('Erro: Você tentou agendar no passado.', 'error')
             return redirect(url_for('book_time', service_id=service.id))

        existing = Appointment.query.filter_by(start_time=booking_time).first()
        if existing:
            flash('Ops! Alguém acabou de reservar este horário.', 'error')
            return redirect(url_for('book_time', service_id=service.id))
            
        # ... (resto do código de salvar igual) ...
        new_appointment = Appointment(
            client_id=current_user.id,
            service_id=service.id,
            start_time=booking_time,
            status='CONFIRMED'
        )
        db.session.add(new_appointment)
        db.session.commit()
        
        return render_template('book_confirm.html', service=service, booking_time=booking_time)
    
    # --- CANCELAMENTO PELO CLIENTE ---
    @app.route('/appointment/cancel/<int:id>')
    @login_required
    def cancel_appointment_client(id):
        # Busca o agendamento
        appointment = Appointment.query.get_or_404(id)
        
        # SEGURANÇA: Verifica se o agendamento pertence mesmo ao cliente logado
        if appointment.client_id != current_user.id:
            return "<h1>Acesso Negado!</h1> <p>Você não pode cancelar agendamentos de outras pessoas.</p> <a href='/dashboard'>Voltar</a>"
        
        # Verifica se já não está cancelado ou concluído
        if appointment.status in ['COMPLETED', 'CANCELED', 'NO_SHOW']:
             return "<h1>Erro!</h1> <p>Este agendamento já foi finalizado ou cancelado.</p> <a href='/dashboard'>Voltar</a>"

        # Atualiza o status para CANCELED
        appointment.status = 'CANCELED'
        db.session.commit()
        
        return redirect(url_for('dashboard'))

# --- AGENDAMENTO MANUAL (Gestor marca pelo cliente) ---
    @app.route('/appointment/new', methods=['GET', 'POST'])
    @login_required
    def create_appointment_admin():
        if current_user.email != "admin@barbearia.com":
            flash('Acesso negado.', 'error')
            return redirect(url_for('index'))

        if request.method == 'POST':
            client_id = request.form.get('client_id')
            service_id = request.form.get('service_id')
            date_str = request.form.get('date')
            time_str = request.form.get('time')
            
            try:
                start_time = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
                
                # Verifica colisão
                if Appointment.query.filter_by(start_time=start_time).first():
                    flash('Já existe um agendamento neste horário!', 'error')
                else:
                    new_app = Appointment(
                        client_id=client_id,
                        service_id=service_id,
                        start_time=start_time,
                        status='CONFIRMED'
                    )
                    db.session.add(new_app)
                    db.session.commit()
                    flash('Agendamento manual criado com sucesso!', 'success')
                    return redirect(url_for('dashboard'))
            except:
                flash('Erro ao processar data/hora.', 'error')

        # GET: Busca dados para preencher os selects
        clients = Client.query.order_by(Client.name).all()
        services = Service.query.all()
        
        return render_template('appointment_new.html', clients=clients, services=services)

# --- DASHBOARD (KPIs + Ações Operacionais + Agendamento Manual) ---
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Inicializa variáveis padrão para evitar erros
        appointments = []
        receita = 0.0
        taxa_no_show = 0.0
        total_finalized = 0
        
        # LÓGICA DO GESTOR
        if current_user.email == "admin@barbearia.com":
            appointments = Appointment.query.order_by(Appointment.start_time.desc()).all()
            
            # Cálculos de KPI (Matemática)
            finalized = [a for a in appointments if a.status in ['COMPLETED', 'NO_SHOW']]
            total_finalized = len(finalized)
            count_no_show = len([a for a in finalized if a.status == 'NO_SHOW'])
            
            if total_finalized > 0:
                taxa_no_show = (count_no_show / total_finalized) * 100
            
            receita = sum([a.service.price for a in appointments if a.status != 'CANCELED'])

        # LÓGICA DO CLIENTE
        else:
            appointments = Appointment.query.filter_by(client_id=current_user.id).order_by(Appointment.start_time.desc()).all()

        # AQUI ESTÁ A MÁGICA:
        # Em vez de retornar texto HTML, chamamos o arquivo bonito que criamos
        return render_template('dashboard.html', 
                               appointments=appointments,
                               receita=receita,
                               taxa_no_show=taxa_no_show,
                               total_finalized=total_finalized)

    # --- ROTA DE MUDANÇA DE STATUS (Ação Operacional) ---
    @app.route('/appointment/<int:id>/status/<string:new_status>')
    @login_required
    def update_status(id, new_status):
        # Segurança: Só admin
        if current_user.email != "admin@barbearia.com":
            return "Acesso Negado"
            
        appointment = Appointment.query.get_or_404(id)
        
        # Validar status permitidos
        if new_status in ['COMPLETED', 'NO_SHOW', 'CANCELED']:
            appointment.status = new_status
            db.session.commit()
        
        return redirect(url_for('dashboard'))