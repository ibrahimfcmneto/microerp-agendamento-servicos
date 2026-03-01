from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Service, Client, WorkingHours, Appointment
from datetime import datetime, timedelta, date

def init_routes(app):

# --- PÁGINA INICIAL ---
    # No routes.py

# --- PÁGINA INICIAL ---
    @app.route('/')
    def index():
        today_slots = []
        default_service = None

        # O erro acontecia aqui. Agora verificamos se existe um usuário antes de olhar as propriedades dele
        if current_user and current_user.is_authenticated:
            # Se for barbeiro ou admin, ele não precisa ver slots de agendamento na home
            if current_user.role != "barber" and current_user.email != "admin@barbearia.com":
                default_service = Service.query.first()
                
                if default_service:
                    today = date.today()
                    weekday = today.weekday()
                    now = datetime.now()
                    
                    barbers = Client.query.filter_by(role='barber').all()
                    available_times_set = set()

                    for barber in barbers:
                        working_hours = WorkingHours.query.filter_by(day_of_week=weekday, barber_id=barber.id).all()
                        existing_appointments = Appointment.query.filter(
                            db.func.date(Appointment.start_time) == today,
                            Appointment.barber_id == barber.id,
                            Appointment.status != 'CANCELED' 
                        ).all()
                        
                        busy_times = [app.start_time.time() for app in existing_appointments]

                        for period in working_hours:
                            current_time = datetime.combine(today, period.start_time)
                            end_time = datetime.combine(today, period.end_time)
                            
                            while current_time + timedelta(minutes=default_service.duration_minutes) <= end_time:
                                if current_time > now:
                                    if current_time.time() not in busy_times:
                                        available_times_set.add(current_time)
                                current_time += timedelta(minutes=30)

                    today_slots = sorted(list(available_times_set))[:6]

        return render_template('index.html', today_slots=today_slots, default_service=default_service)
    
# --- REGISTRO DE CLIENTES (Visual Novo) ---
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
    # --- LOGIN (Ajustado para levar todos à Home Inteligente) ---
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = Client.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                login_user(user)
                
                # MUDANÇA: Agora mandamos TODOS para o 'index'.
                # O index.html é que vai decidir se mostra o Painel Admin ou a Barbearia.
                return redirect(url_for('index'))
                
            else:
                flash('Email ou senha incorretos.', 'error')
                return redirect(url_for('login'))
        
        return render_template('login.html')
    
    # --- LOGOUT ---
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

# --- SETUP ADMIN ---
    @app.route('/setup-admin')
    def setup_admin():
        if Client.query.filter_by(email="admin@barbearia.com").first():
            return "Admin já existe!"
            
        admin = Client(name="Gestor Elite", email="admin@barbearia.com", phone="000000000", role='barber')
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        return "✅ Gestor criado! Email: admin@barbearia.com | Senha: admin123"

    # --- NOVO: CADASTRAR BARBEIRO (Exclusivo Admin) ---
    @app.route('/barbeiros/novo', methods=['GET', 'POST'])
    @login_required
    def register_barber():
        if current_user.email != "admin@barbearia.com":
            flash('Acesso negado.', 'error')
            return redirect(url_for('index'))

        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            phone = request.form.get('phone')

            if Client.query.filter_by(email=email).first():
                flash('Este email já está em uso.', 'error')
                return redirect(url_for('register_barber'))

            new_barber = Client(name=name, email=email, phone=phone, role='barber')
            new_barber.set_password(password)
            db.session.add(new_barber)
            db.session.commit()
            
            flash(f'Barbeiro {name} cadastrado com sucesso!', 'success')
            return redirect(url_for('dashboard'))

        return render_template('register_barber.html')
    

    # --- ROTA DE CONFIGURAÇÃO RÁPIDA (Executar uma vez) ---
    from models import WorkingHours
    from datetime import time

# --- ROTA DE CONFIGURAÇÃO RÁPIDA (Executar uma vez por barbeiro) ---
    @app.route('/setup-hours')
    @login_required
    def setup_hours():
        # Segurança: Apenas quem trabalha na barbearia pode configurar horários
        if current_user.role not in ['barber', 'admin']:
            flash('Acesso negado.', 'danger')
            return redirect(url_for('index'))
        
        # Limpa apenas os horários do barbeiro logado para não apagar os do colega
        WorkingHours.query.filter_by(barber_id=current_user.id).delete()
        
        dias_semana = [0, 1, 2, 3, 4] # Segunda a Sexta
        
        for dia in dias_semana:
            # Manhã: 09:00 às 12:00
            h1 = WorkingHours(barber_id=current_user.id, day_of_week=dia, start_time=time(9,0), end_time=time(12,0))
            # Tarde: 13:00 às 18:00
            h2 = WorkingHours(barber_id=current_user.id, day_of_week=dia, start_time=time(13,0), end_time=time(18,0))
            
            db.session.add(h1)
            db.session.add(h2)
            
        db.session.commit()
        return f"✅ Horários de {current_user.name} configurados com sucesso (Seg-Sex, 09-18h)!"


# --- CRUD DE HORÁRIOS (Individual por Barbeiro) ---
    @app.route('/working_hours', methods=['GET', 'POST'])
    @login_required
    def manage_working_hours(): 
        if current_user.role not in ['barber', 'admin']:
            return redirect(url_for('index'))

        if request.method == 'POST':
            # Remove apenas os horários do barbeiro que está salvando
            WorkingHours.query.filter_by(barber_id=current_user.id).delete()
            
            for i in range(7):
                if not request.form.get(f'closed_{i}'):
                    # Turno 1
                    s1 = request.form.get(f'start1_{i}')
                    e1 = request.form.get(f'end1_{i}')
                    if s1 and e1:
                        db.session.add(WorkingHours(
                            barber_id=current_user.id,
                            day_of_week=i, 
                            start_time=datetime.strptime(s1, '%H:%M').time(), 
                            end_time=datetime.strptime(e1, '%H:%M').time()
                        ))
                    # Turno 2
                    s2 = request.form.get(f'start2_{i}')
                    e2 = request.form.get(f'end2_{i}')
                    if s2 and e2:
                        db.session.add(WorkingHours(
                            barber_id=current_user.id,
                            day_of_week=i, 
                            start_time=datetime.strptime(s2, '%H:%M').time(), 
                            end_time=datetime.strptime(e2, '%H:%M').time()
                        ))
            
            db.session.commit()
            flash('Seus horários foram atualizados!', 'success')
            return redirect(url_for('dashboard'))

        # PREPARAÇÃO DOS DADOS: Busca apenas os horários do barbeiro logado
        existing_hours = WorkingHours.query.filter_by(barber_id=current_user.id)\
            .order_by(WorkingHours.day_of_week, WorkingHours.start_time).all()
        
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

# --- LISTAR SERVIÇOS ---
    @app.route('/services')
    @login_required
    def list_services():
        # SEGURANÇA: Admin gerencia, mas Barbeiros podem visualizar
        if current_user.role not in ['admin', 'barber']:
            flash('Acesso negado! Apenas funcionários podem ver a lista de serviços.', 'error')
            return redirect(url_for('index'))

        services = Service.query.all()
        return render_template('services_list.html', services=services)

    # --- CRIAR NOVO SERVIÇO ---
    @app.route('/services/new', methods=['GET', 'POST'])
    @login_required
    def create_service():
        # SEGURANÇA: Apenas o ADMIN (Dono) pode criar ou alterar preços
        if current_user.role != 'admin':
            flash('Acesso negado! Apenas o gestor pode criar serviços.', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            try:
                new_service = Service(
                    name=request.form.get('name'), 
                    duration_minutes=int(request.form.get('duration')), 
                    price=float(request.form.get('price'))
                )
                db.session.add(new_service)
                db.session.commit()
                flash('Serviço criado com sucesso!', 'success')
                return redirect(url_for('list_services'))
            except Exception as e:
                db.session.rollback()
                flash('Erro ao criar serviço. Verifique os dados.', 'danger')

        return render_template('service_new.html')

    # --- DELETAR SERVIÇO ---
    @app.route('/services/delete/<int:id>')
    @login_required
    def delete_service(id):
        # SEGURANÇA: Apenas o ADMIN pode deletar
        if current_user.role != 'admin':
            flash('Ação não permitida para o seu nível de acesso.', 'error')
            return redirect(url_for('dashboard'))

        service = Service.query.get_or_404(id)
        
        try:
            db.session.delete(service)
            db.session.commit()
            flash(f'Serviço "{service.name}" removido.', 'success')
        except:
            db.session.rollback()
            flash('Erro ao deletar. O serviço pode estar vinculado a agendamentos.', 'danger')
            
        return redirect(url_for('list_services'))
    

    # ==================================================
    # ÁREA DO CLIENTE (FLUXO DE AGENDAMENTO)
    # ==================================================

# --- PASSO 1: ESCOLHER SERVIÇO (Com Template) ---
    # --- ROTA DE AGENDAMENTO (CLIENTE ESCOLHE SERVIÇO, BARBEIRO E HORA) ---
    @app.route('/agendar', methods=['GET', 'POST'])
    @login_required
    def book_service():
        if request.method == 'POST':
            # Captura os dados do formulário
            service_id = request.form.get('service_id')
            barber_id = request.form.get('barber_id')
            date_str = request.form.get('date')
            time_str = request.form.get('time')

            # Validação básica
            if not all([service_id, barber_id, date_str, time_str]):
                flash('Por favor, preencha todos os campos.', 'danger')
                return redirect(url_for('book_service'))

            try:
                # Converte strings de data e hora para objeto datetime
                start_time = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
                
                # Cria o novo agendamento com o barbeiro escolhido
                new_app = Appointment(
                    client_id=current_user.id,
                    barber_id=int(barber_id), # Vincula ao barbeiro selecionado
                    service_id=int(service_id),
                    start_time=start_time,
                    status='CONFIRMED'
                )

                db.session.add(new_app)
                db.session.commit()
                flash('Agendamento realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))

            except Exception as e:
                db.session.rollback()
                print(f"Erro ao agendar: {e}")
                flash('Erro ao processar agendamento. Tente outro horário.', 'danger')

        # Se for GET: Carrega serviços e apenas usuários que são BARBEIROS
        services = Service.query.all()
        barbers = Client.query.filter_by(role='barber').all()
        
        return render_template('book.html', services=services, barbers=barbers)

    # --- ROTA PARA ESCOLHER O HORÁRIO (AGORA COM BARBEIRO) ---
    @app.route('/agendar/<int:service_id>/<int:barber_id>')
    @login_required
    def book_time(service_id, barber_id):
        service = Service.query.get_or_404(service_id)
        barber = Client.query.get_or_404(barber_id) # Busca o barbeiro escolhido
        
        date_str = request.args.get('date')
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selected_date = date.today()

        day_of_week = selected_date.weekday()
        
        # BUSCA O HORÁRIO DE TRABALHO DESTE BARBEIRO ESPECÍFICO
        working_hours = WorkingHours.query.filter_by(
            day_of_week=day_of_week, 
            barber_id=barber_id
        ).all()
        
        # BUSCA APENAS OS AGENDAMENTOS DESTE BARBEIRO
        existing_appointments = Appointment.query.filter(
            db.func.date(Appointment.start_time) == selected_date,
            Appointment.barber_id == barber_id, # Filtro essencial
            Appointment.status != 'CANCELED'
        ).all()
        
        busy_times = [app.start_time.time() for app in existing_appointments]
        now = datetime.now()
        available_slots = []

        from datetime import timedelta # Garanta que o timedelta está importado

        for period in working_hours:
            current_time = datetime.combine(selected_date, period.start_time)
            end_time = datetime.combine(selected_date, period.end_time)
            
            while current_time + timedelta(minutes=service.duration_minutes) <= end_time:
                # Só permite horários no futuro e que não estejam ocupados por este barbeiro
                if current_time > now:
                    if current_time.time() not in busy_times:
                        available_slots.append(current_time)
                current_time += timedelta(minutes=30)

        return render_template('book_time.html', 
                               service=service, 
                               barber=barber, # Passamos o barbeiro para o HTML
                               selected_date=selected_date, 
                               available_slots=available_slots,
                               today=date.today())



    # --- PASSO 3: CONFIRMAÇÃO (Agora com Barbeiro) ---
    @app.route('/agendar/confirmar/<int:service_id>/<int:barber_id>/<string:slot>')
    @login_required
    def confirm_booking(service_id, barber_id, slot):
        service = Service.query.get_or_404(service_id)
        barber = Client.query.get_or_404(barber_id)
        
        try:
            booking_time = datetime.strptime(slot, '%Y-%m-%d_%H-%M-%S')
        except ValueError:
            flash('Formato de data inválido.', 'error')
            return redirect(url_for('book_service'))
        
        # 1. Impede agendamentos no passado
        if booking_time < datetime.now():
             flash('Erro: Você tentou agendar em um horário que já passou.', 'error')
             return redirect(url_for('book_time', service_id=service.id, barber_id=barber.id))

        # 2. Verifica se ESSE barbeiro específico já foi ocupado enquanto o cliente decidia
        existing = Appointment.query.filter(
            Appointment.start_time == booking_time,
            Appointment.barber_id == barber_id, # Filtro de colisão por profissional
            Appointment.status != 'CANCELED'
        ).first()

        if existing:
            flash(f'Ops! Alguém acabou de reservar este horário com {barber.name}.', 'error')
            return redirect(url_for('book_time', service_id=service.id, barber_id=barber.id))
            
        # 3. Cria o agendamento com o vínculo correto
        new_appointment = Appointment(
            client_id=current_user.id,
            barber_id=barber.id, # Fundamental para separar as agendas
            service_id=service.id,
            start_time=booking_time,
            status='CONFIRMED'
        )
        
        try:
            db.session.add(new_appointment)
            db.session.commit()
            # Passamos o barbeiro para o template para mostrar: "Corte com o Barbeiro X confirmado!"
            return render_template('book_confirm.html', 
                                   service=service, 
                                   barber=barber, 
                                   booking_time=booking_time)
        except Exception as e:
            db.session.rollback()
            flash('Erro ao processar agendamento. Tente novamente.', 'error')
            return redirect(url_for('book_service'))
    

# --- CANCELAMENTO PELO CLIENTE (Com Regra de 24h) ---
    @app.route('/appointment/cancel/<int:id>')
    @login_required
    def cancel_appointment_client(id):
        appointment = Appointment.query.get_or_404(id)
        
        # 1. SEGURANÇA: Verifica se o agendamento é do cliente logado
        if appointment.client_id != current_user.id:
            flash('Acesso negado.', 'error')
            return redirect(url_for('dashboard'))
        
        if appointment.status in ['COMPLETED', 'CANCELED', 'NO_SHOW']:
             flash('Este agendamento já foi finalizado.', 'error')
             return redirect(url_for('dashboard'))

        # 2. VERIFICAÇÃO DE 24 HORAS
        time_difference = appointment.start_time - datetime.now()
        
        if time_difference < timedelta(hours=24):
            # MELHORIA: Mostra o telefone do barbeiro específico que está no banco de dados
            telefone_barbeiro = appointment.barber.phone or "(34) 99882-0007"
            flash(f'Menos de 24h para o agendamento. Entre em contato com o barbeiro {appointment.barber.name} pelo número {telefone_barbeiro} para cancelar.', 'error')
            return redirect(url_for('dashboard'))

        appointment.status = 'CANCELED'
        db.session.commit()
        
        flash('Agendamento cancelado com sucesso. O horário está livre novamente.', 'success')
        return redirect(url_for('dashboard'))

    # --- AGENDAMENTO MANUAL (Admin escolhe Cliente + Barbeiro) ---
    @app.route('/appointment/new', methods=['GET', 'POST'])
    @login_required
    def create_appointment_admin():
        # Apenas Admin ou Barbeiros podem marcar manualmente
        if current_user.role != "barber" and current_user.email != "admin@barbearia.com":
            flash('Acesso negado.', 'error')
            return redirect(url_for('index'))

        if request.method == 'POST':
            client_id = request.form.get('client_id')
            barber_id = request.form.get('barber_id') # NOVO: Admin seleciona o barbeiro
            service_id = request.form.get('service_id')
            date_str = request.form.get('date')
            time_str = request.form.get('time')
            
            try:
                start_time = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
                
                # VERIFICAÇÃO DE COLISÃO: Checa se O BARBEIRO escolhido está livre
                collision = Appointment.query.filter(
                    Appointment.start_time == start_time, 
                    Appointment.barber_id == barber_id,
                    Appointment.status != 'CANCELED'
                ).first()

                if collision:
                    flash('Este barbeiro já tem um agendamento neste horário!', 'error')
                else:
                    new_app = Appointment(
                        client_id=client_id,
                        barber_id=barber_id, # Vincula ao profissional
                        service_id=service_id,
                        start_time=start_time,
                        status='CONFIRMED'
                    )
                    db.session.add(new_app)
                    db.session.commit()
                    flash('Agendamento manual criado com sucesso!', 'success')
                    return redirect(url_for('dashboard'))
            except Exception as e:
                print(f"Erro no agendamento manual: {e}")
                flash('Erro ao processar os dados. Verifique a data e hora.', 'error')

        clients = Client.query.order_by(Client.name).all()
        services = Service.query.all()
        barbers = Client.query.filter_by(role='barber').all() # NOVO: Lista de barbeiros para o select
        
        return render_template('appointment_new.html', clients=clients, services=services, barbers=barbers)

    # --- ATUALIZAR STATUS (Ação Operacional) ---
    @app.route('/appointment/<int:id>/status/<string:new_status>')
    @login_required
    def update_status(id, new_status):
        appointment = Appointment.query.get_or_404(id)

        # SEGURANÇA: Só o dono do agendamento (barbeiro) ou o Admin podem mudar o status
        if current_user.id != appointment.barber_id and current_user.email != "admin@barbearia.com":
            flash('Você não tem permissão para alterar este agendamento.', 'error')
            return redirect(url_for('dashboard'))
        
        if new_status in ['COMPLETED', 'NO_SHOW', 'CANCELED']:
            appointment.status = new_status
            db.session.commit()
            flash(f'Status atualizado para {new_status}!', 'success')
        
        return redirect(url_for('dashboard'))
    
# --- DASHBOARD (Visão Individual por Barbeiro ou Total para Admin) ---
    @app.route('/dashboard')
    @login_required
    def dashboard():
        appointments = []
        receita = 0.0
        taxa_no_show = 0.0
        total_agendamentos_hoje = 0
        all_services = []
        
        hoje = date.today()
        hoje_inicio = datetime.combine(hoje, datetime.min.time())
        hoje_fim = datetime.combine(hoje, datetime.max.time())

        # LÓGICA PARA QUEM TRABALHA NA BARBEARIA (Barbeiros e Admin)
        if current_user.role == "barber" or current_user.email == "admin@barbearia.com":
            all_services = Service.query.all()
            
            # Se for Admin, vê TUDO. Se for Barbeiro, vê apenas o DELE.
            if current_user.email == "admin@barbearia.com":
                query = Appointment.query.filter(Appointment.start_time >= hoje_inicio)
            else:
                query = Appointment.query.filter(
                    Appointment.barber_id == current_user.id,
                    Appointment.start_time >= hoje_inicio
                )

            appointments = query.order_by(Appointment.start_time.asc()).all()
            
            # KPIs focados apenas no dia de hoje
            apps_hoje = [a for a in appointments if a.start_time <= hoje_fim]
            total_agendamentos_hoje = len(apps_hoje)
            receita = sum([float(a.service.price) for a in apps_hoje if a.status in ['COMPLETED', 'CONFIRMED']])
            
            # Taxa de No-Show (Calculada sobre o histórico do usuário logado)
            if current_user.email == "admin@barbearia.com":
                finalized = Appointment.query.filter(Appointment.status.in_(['COMPLETED', 'NO_SHOW'])).all()
            else:
                finalized = Appointment.query.filter_by(barber_id=current_user.id).filter(Appointment.status.in_(['COMPLETED', 'NO_SHOW'])).all()
            
            if finalized:
                count_no_show = len([a for a in finalized if a.status == 'NO_SHOW'])
                taxa_no_show = (count_no_show / len(finalized)) * 100

            return render_template('dashboard.html', 
                                    appointments=appointments,
                                    receita=receita,
                                    taxa_no_show=taxa_no_show,
                                    total_agendamentos_hoje=total_agendamentos_hoje,
                                    all_services=all_services)

        # LÓGICA DO CLIENTE (Vê seus próprios agendamentos com qualquer barbeiro)
        else:
            appointments = Appointment.query.filter_by(client_id=current_user.id)\
                .filter(Appointment.start_time >= hoje_inicio)\
                .order_by(Appointment.start_time.asc()).all()
            return render_template('dashboard.html', appointments=appointments)
        

    # --- FINALIZAR ATENDIMENTO (Protegido para o Barbeiro dono do corte) ---
    @app.route('/finish_appointment/<int:id>', methods=['POST'])
    @login_required
    def finish_appointment(id):
        appointment = Appointment.query.get_or_404(id)

        # Segurança: Só o barbeiro que fez o serviço ou o admin podem finalizar
        if current_user.role != 'barber' or (current_user.id != appointment.barber_id and current_user.email != "admin@barbearia.com"):
            flash('Você não tem permissão para finalizar este atendimento.', 'danger')
            return redirect(url_for('dashboard'))
        
        forma_pagamento = request.form.get('payment_method')
        extra_service_ids = request.form.getlist('extra_service_ids')
        extra_service_ids = [eid for eid in extra_service_ids if eid != "0"]

        # Calcula o valor total incluindo os adicionais para salvar no banco
        valor_total = float(appointment.service.price)
        servicos_nomes = [appointment.service.name]

        for sid in extra_service_ids:
            s = Service.query.get(sid)
            if s:
                valor_total += float(s.price)
                servicos_nomes.append(s.name)

        # Atualiza o objeto no banco com os dados reais do fechamento
        appointment.status = 'COMPLETED'
        appointment.payment_method = forma_pagamento
        appointment.extra_services = ", ".join(servicos_nomes[1:]) # Salva apenas os extras
        # Se você adicionou a coluna total_value no models:
        # appointment.total_value = valor_total 
        
        try:
            db.session.commit()
            flash(f'Atendimento de {appointment.client.name} finalizado! Total: R$ {valor_total:.2f}', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar no banco de dados.', 'danger')
            
        return redirect(url_for('dashboard'))