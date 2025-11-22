from flask import render_template, request, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Service, Client, WorkingHours, Appointment
from datetime import datetime, timedelta, date

def init_routes(app):

    # --- PÁGINA INICIAL ---
    # --- PÁGINA INICIAL ---
    @app.route('/')
    def index():
        menu = ""
        if current_user.is_authenticated:
            menu += f"<p>Olá, <b>{current_user.name}</b>!</p>"
            
            # LÓGICA DE SEGURANÇA: Mostra menu de admin APENAS se for o admin
            if current_user.email == "admin@barbearia.com":
                menu += "<p style='color:red'>Painel do Gestor Ativo</p>"
                # ADICIONEI ESTE LINK NOVO AQUI EM BAIXO 👇
                menu += "<a href='/dashboard'>📊 Ver Dashboard (Agenda)</a> | "
                menu += "<a href='/services'>🛠️ Gerenciar Serviços</a> | "
            else:
                menu += "<p>Bem-vindo à nossa Barbearia!</p>"
                menu += "<a href='/book'>📅 Agendar Horário</a> | "
                menu += "<a href='/dashboard'>👤 Meus Agendamentos</a> | "
                
            menu += "<a href='/logout'>Sair</a>"
        else:
            menu = "<a href='/login'>🔐 Login</a> | <a href='/register'>📝 Criar Conta</a>"
            
        return f"""
        <h1>Bem-vindo ao MicroERP!</h1>
        <p>Agendamento Online Simplificado</p>
        <hr>
        {menu}
        """

    # --- REGISTRO DE CLIENTES (NOVO) ---
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            phone = request.form.get('phone')

            # Verifica se o email já existe
            if Client.query.filter_by(email=email).first():
                return "<h1>Erro: Este email já está cadastrado!</h1> <a href='/register'>Tentar outro</a>"

            # Cria o novo cliente
            new_client = Client(name=name, email=email, phone=phone)
            new_client.set_password(password)
            
            db.session.add(new_client)
            db.session.commit()

            return "<h1>Conta criada com sucesso!</h1> <a href='/login'>Faça Login agora</a>"

        return """
        <h2>📝 Cadastro de Cliente</h2>
        <form method="POST">
            Nome: <input type="text" name="name" required><br><br>
            Email: <input type="email" name="email" required><br><br>
            Telefone: <input type="text" name="phone" placeholder="(xx) 9xxxx-xxxx"><br><br>
            Senha: <input type="password" name="password" required><br><br>
            <button type="submit">Criar Conta</button>
        </form>
        <p>Já tem conta? <a href='/login'>Fazer Login</a></p>
        """

    # --- LOGIN ---
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = Client.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('index'))
            else:
                return "<h1>Erro: Email ou senha inválidos!</h1> <a href='/login'>Tentar de novo</a>"
        
        return """
        <h2>🔐 Login</h2>
        <form method="POST">
            Email: <input type="email" name="email" required><br><br>
            Senha: <input type="password" name="password" required><br><br>
            <button type="submit">Entrar</button>
        </form>
        <p>Ainda não tem conta? <a href='/register'>Crie uma conta aqui</a></p>
        """

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
        # Segurança: Só admin
        if current_user.email != "admin@barbearia.com":
            return "Acesso Negado"

        dias_semana = {
            0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
            3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
        }

        if request.method == 'POST':
            # 1. Limpa tudo para recriar
            WorkingHours.query.delete()
            
            # 2. Para cada dia (0 a 6), verifica os dois turnos
            for i in range(7):
                if not request.form.get(f'closed_{i}'):
                    # Turno 1 (Manhã)
                    s1 = request.form.get(f'start1_{i}')
                    e1 = request.form.get(f'end1_{i}')
                    if s1 and e1:
                        db.session.add(WorkingHours(day_of_week=i, 
                                     start_time=datetime.strptime(s1, '%H:%M').time(), 
                                     end_time=datetime.strptime(e1, '%H:%M').time()))
                    
                    # Turno 2 (Tarde)
                    s2 = request.form.get(f'start2_{i}')
                    e2 = request.form.get(f'end2_{i}')
                    if s2 and e2:
                        db.session.add(WorkingHours(day_of_week=i, 
                                     start_time=datetime.strptime(s2, '%H:%M').time(), 
                                     end_time=datetime.strptime(e2, '%H:%M').time()))
            
            db.session.commit()
            return redirect(url_for('dashboard'))

        # GET: Preparar dados
        # Busca horários e ordena por hora para separar manhã/tarde corretamente
        existing_hours = WorkingHours.query.order_by(WorkingHours.day_of_week, WorkingHours.start_time).all()
        
        # Agrupa por dia: { 0: [periodo1, periodo2], 1: [...], ... }
        hours_map = {}
        for h in existing_hours:
            if h.day_of_week not in hours_map: hours_map[h.day_of_week] = []
            hours_map[h.day_of_week].append(h)

        # Monta o HTML
        rows_html = ""
        for i in range(7):
            day_name = dias_semana[i]
            periods = hours_map.get(i, [])
            
            # Se a lista estiver vazia, consideramos fechado
            is_closed = "checked" if not periods else ""
            
            # Define valores padrão (se existirem no banco, usa-os; senão usa padrão 09-12 / 13-18)
            # Turno 1
            v_s1 = periods[0].start_time.strftime('%H:%M') if len(periods) > 0 else "09:00"
            v_e1 = periods[0].end_time.strftime('%H:%M') if len(periods) > 0 else "12:00"
            
            # Turno 2 (Pega o segundo item da lista, se houver)
            v_s2 = periods[1].start_time.strftime('%H:%M') if len(periods) > 1 else "13:00"
            v_e2 = periods[1].end_time.strftime('%H:%M') if len(periods) > 1 else "18:00"

            # JavaScript para desabilitar tudo se estiver "Fechado"
            js_toggle = f"""
                let c = this.checked;
                ['start1_{i}','end1_{i}','start2_{i}','end2_{i}'].forEach(id => document.getElementById(id).disabled = c);
            """

            rows_html += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px;"><b>{day_name}</b></td>
                <td style="padding: 10px;">
                    <label><input type="checkbox" name="closed_{i}" {is_closed} onchange="{js_toggle}"> Fechado</label>
                </td>
                <td style="padding: 5px; background:#f9f9f9;">
                    <small>Turno 1 (Manhã)</small><br>
                    <input type="time" id="start1_{i}" name="start1_{i}" value="{v_s1}" {'disabled' if is_closed else ''}> até
                    <input type="time" id="end1_{i}" name="end1_{i}" value="{v_e1}" {'disabled' if is_closed else ''}>
                </td>
                <td style="padding: 5px;">
                    <small>Turno 2 (Tarde)</small><br>
                    <input type="time" id="start2_{i}" name="start2_{i}" value="{v_s2}" {'disabled' if is_closed else ''}> até
                    <input type="time" id="end2_{i}" name="end2_{i}" value="{v_e2}" {'disabled' if is_closed else ''}>
                </td>
            </tr>
            """

        return f"""
        <h2>⏰ Configurar Horários (Com Almoço)</h2>
        <p>Defina dois turnos de trabalho. O intervalo entre eles será o horário de almoço.</p>
        <p><i>Dica: Para não ter pausa, basta fazer o Fim do Turno 1 ser igual ao Início do Turno 2 (Ex: 12:00 até 12:00).</i></p>
        
        <form method="POST">
            <table style="border-collapse: collapse; width: 100%; max-width: 800px;">
                {rows_html}
            </table>
            <br>
            <button type="submit" style="padding: 15px; background-color: #28a745; color: white; border: none; cursor: pointer; font-size: 16px;">
                💾 Salvar Configuração
            </button>
        </form>
        <br>
        <a href='/dashboard'>Cancelar e Voltar</a>
        """

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

    # Passo 1: Escolher o Serviço
    @app.route('/book')
    @login_required
    def book_service():
        services = Service.query.all()
        
        html = "<h2>📅 Novo Agendamento</h2>"
        html += "<p>Passo 1: Qual serviço você gostaria de realizar?</p>"
        html += "<hr>"
        html += "<ul>"
        for s in services:
            html += f"<li style='margin-bottom: 15px;'>"
            html += f"<b>{s.name}</b> <br>"
            html += f"⏱️ {s.duration_minutes} min | 💰 R$ {s.price} <br>"
            # O botão leva para o Passo 2 (passando o ID do serviço)
            html += f"<a href='/book/{s.id}'><button>➡️ Selecionar este</button></a>"
            html += "</li>"
        html += "</ul>"
        html += "<br><a href='/'>🏠 Cancelar e Voltar</a>"
        return html

    # Passo 2: Escolher o Horário (COM ALGORITMO DE DISPONIBILIDADE)
    @app.route('/book/<int:service_id>')
    @login_required
    def book_time(service_id):
        service = Service.query.get_or_404(service_id)
        
        # 1. Pega a data da URL ou usa HOJE como padrão
        date_str = request.args.get('date')
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selected_date = date.today()

        # 2. Descobre o dia da semana
        day_of_week = selected_date.weekday()
        
        # 3. Busca os horários de funcionamento
        working_hours = WorkingHours.query.filter_by(day_of_week=day_of_week).all()
        
        # 4. Busca agendamentos JÁ FEITOS
        existing_appointments = Appointment.query.filter(
            db.func.date(Appointment.start_time) == selected_date
        ).all()
        
        busy_times = [app.start_time.time() for app in existing_appointments]
        
        # --- NOVO: PEGA A HORA ATUAL PARA COMPARAR ---
        now = datetime.now()

        available_slots = []

        # 5. O ALGORITMO
        for period in working_hours:
            current_time = datetime.combine(selected_date, period.start_time)
            end_time = datetime.combine(selected_date, period.end_time)
            
            while current_time + timedelta(minutes=service.duration_minutes) <= end_time:
                
                # --- A MÁGICA ACONTECE AQUI ---
                # Verifica se está livre E SE É NO FUTURO
                # Só adiciona se o horário for MAIOR que "agora"
                if current_time > now:
                    if current_time.time() not in busy_times:
                        available_slots.append(current_time)
                
                current_time += timedelta(minutes=30)

        return f"""
        <h2>📅 Agendando: {service.name}</h2>
        <p>Data Escolhida: <b>{selected_date.strftime('%d/%m/%Y')}</b></p>
        
        <form method="GET">
            <label>Mudar Data:</label>
            <input type="date" name="date" value="{selected_date}" min="{date.today()}" onchange="this.form.submit()">
        </form>
        <hr>
        
        <h3>🕒 Horários Disponíveis:</h3>
        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
            {''.join([
                f'''<a href="/book/confirm/{service.id}/{slot.strftime('%Y-%m-%d_%H-%M-%S')}" 
                       style="text-decoration:none;">
                       <button style="padding: 10px; background-color: #4CAF50; color: white; border: none; cursor: pointer;">
                         {slot.strftime('%H:%M')}
                       </button>
                    </a>''' 
                for slot in available_slots
            ]) or "<p>❌ Nenhum horário disponível (ou o dia já acabou).</p>"}
        </div>
        
        <br><br>
        <a href='/book'>⬅️ Voltar</a>
        """
    
    # Passo 3: Confirmação e Salvamento (O Clique Final)
    # Passo 3: Confirmação e Salvamento
    @app.route('/book/confirm/<int:service_id>/<string:slot>')
    @login_required
    def confirm_booking(service_id, slot):
        service = Service.query.get_or_404(service_id)
        booking_time = datetime.strptime(slot, '%Y-%m-%d_%H-%M-%S')
        
        # --- SEGURANÇA 1: BLOQUEIA PASSADO ---
        if booking_time < datetime.now():
             return "<h1>Erro!</h1> <p>Você não pode agendar no passado. 🕰️</p> <a href='/book'>Tente novamente</a>"

        # --- SEGURANÇA 2: BLOQUEIA COLISÃO ---
        existing = Appointment.query.filter_by(start_time=booking_time).first()
        if existing:
            return "<h1>Ops! Alguém acabou de pegar esse horário. 🐢</h1> <a href='/book'>Tente outro</a>"
            
        # ... (o resto da função continua igual: cria o agendamento e salva) ...
        new_appointment = Appointment(
            client_id=current_user.id,
            service_id=service.id,
            start_time=booking_time,
            status='CONFIRMED'
        )
        db.session.add(new_appointment)
        db.session.commit()
        
        return f"""
        <h1>🎉 Sucesso! Agendamento Confirmado.</h1>
        <div style="border: 1px solid #ddd; padding: 20px; max-width: 400px;">
            <p>✂️ <b>Serviço:</b> {service.name}</p>
            <p>📅 <b>Data:</b> {booking_time.strftime('%d/%m/%Y')}</p>
            <p>⏰ <b>Horário:</b> {booking_time.strftime('%H:%M')}</p>
            <p>💰 <b>Valor:</b> R$ {service.price}</p>
            <p>👤 <b>Cliente:</b> {current_user.name}</p>
        </div>
        <br>
        <a href='/dashboard'><button>Ver Meus Agendamentos</button></a>
        """
    
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
        # Segurança: Só admin
        if current_user.email != "admin@barbearia.com":
            return "Acesso Negado"

        if request.method == 'POST':
            client_id = request.form.get('client_id')
            service_id = request.form.get('service_id')
            date_str = request.form.get('date') # Ex: 2023-10-30
            time_str = request.form.get('time') # Ex: 15:30
            
            # Monta a data final
            start_time = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
            
            # Verifica colisão (Opcional, mas bom ter)
            if Appointment.query.filter_by(start_time=start_time).first():
                return "<h1>Erro: Já existe agendamento neste horário!</h1> <a href='/appointment/new'>Voltar</a>"
            
            new_app = Appointment(
                client_id=client_id,
                service_id=service_id,
                start_time=start_time,
                status='CONFIRMED'
            )
            db.session.add(new_app)
            db.session.commit()
            
            return redirect(url_for('dashboard'))

        # GET: Mostrar o formulário
        clients = Client.query.order_by(Client.name).all()
        services = Service.query.all()
        
        return f"""
        <h2>📝 Agendamento Manual (Gestor)</h2>
        <form method="POST">
            <label>1. Escolha o Cliente:</label><br>
            <select name="client_id" required>
                {''.join([f'<option value="{c.id}">{c.name} ({c.email})</option>' for c in clients])}
            </select>
            <br><br>
            
            <label>2. Escolha o Serviço:</label><br>
            <select name="service_id" required>
                {''.join([f'<option value="{s.id}">{s.name} - R$ {s.price}</option>' for s in services])}
            </select>
            <br><br>
            
            <label>3. Data e Hora:</label><br>
            <input type="date" name="date" required>
            <input type="time" name="time" required>
            <br><br>
            
            <button type="submit">📅 Agendar Manualmente</button>
        </form>
        <br>
        <a href='/dashboard'>Cancelar</a>
        """


# --- DASHBOARD (KPIs + Ações Operacionais + Agendamento Manual) ---
    @app.route('/dashboard')
    @login_required
    def dashboard():
        html = ""
        
        # VISÃO DO GESTOR (Painel de Controle)
        if current_user.email == "admin@barbearia.com":
            # Busca todos os agendamentos ordenados (mais novos primeiro)
            appointments = Appointment.query.order_by(Appointment.start_time.desc()).all()
            
            # --- CÁLCULO DE KPI (Taxa de No-Show) ---
            # Consideramos apenas agendamentos finalizados (Concluídos ou Faltas) para a estatística
            finalized = [a for a in appointments if a.status in ['COMPLETED', 'NO_SHOW']]
            total_finalized = len(finalized)
            count_no_show = len([a for a in finalized if a.status == 'NO_SHOW'])
            
            # Evita divisão por zero
            if total_finalized > 0:
                taxa_no_show = (count_no_show / total_finalized) * 100
            else:
                taxa_no_show = 0.0
            
            # Receita (Soma de tudo que foi 'COMPLETED' ou 'CONFIRMED')
            receita = sum([a.service.price for a in appointments if a.status != 'CANCELED'])

# --- TELA DO DASHBOARD ---
            html += f"""
            <h1>👓 Painel do Gestor</h1>
            
            <div style="margin-bottom: 20px;">
                <a href='/appointment/new'>
                    <button style='padding:10px; font-size:16px; margin-right:10px;'>➕ Novo Agendamento Manual</button>
                </a>
                <a href='/working_hours'>
                    <button style='padding:10px; font-size:16px; background-color: #6c757d; color: white;'>⚙️ Configurar Horários</button>
                </a>
            </div>
            
            <div style="display: flex; gap: 20px; background: #f4f4f4; padding: 15px; border-radius: 8px;">
                <div>
                    <h3>💰 Receita Estimada</h3>
                    <p style="font-size: 20px; color: green;">R$ {receita:.2f}</p>
                </div>
                <div>
                    <h3>📉 Taxa de No-Show</h3>
                    <p style="font-size: 20px; color: red;">{taxa_no_show:.1f}%</p>
                    <small>Baseado em {total_finalized} atendimentos finalizados</small>
                </div>
            </div>
            <hr>
            <h3>📅 Agenda de Hoje e Futuro</h3>
            <ul>
            """
            
            for app in appointments:
                # Define cor do status
                color = "black"
                if app.status == 'CONFIRMED': color = "blue"
                elif app.status == 'COMPLETED': color = "green"
                elif app.status == 'NO_SHOW': color = "red"
                
                html += f"<li style='margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px;'>"
                html += f"<b>{app.start_time.strftime('%d/%m às %H:%M')}</b> | "
                html += f"{app.client.name} - {app.service.name} | "
                html += f"Status: <b style='color:{color}'>{app.status}</b> "
                
                # Botões de Ação (Só aparecem se estiver Confirmado/Pendente)
                if app.status == 'CONFIRMED':
                    html += f"""
                    <br>
                    👉 Ações: 
                    <a href='/appointment/{app.id}/status/COMPLETED'><button style='color:green'>✅ Concluir (Veio)</button></a>
                    <a href='/appointment/{app.id}/status/NO_SHOW'><button style='color:red'>❌ No-Show (Faltou)</button></a>
                    """
                html += "</li>"
            html += "</ul>"

# VISÃO DO CLIENTE (Vê só os dele)
        else:
            appointments = Appointment.query.filter_by(client_id=current_user.id).order_by(Appointment.start_time.desc()).all()
            html += f"<h2>📅 Meus Agendamentos ({current_user.name})</h2><hr>"
            
            if not appointments:
                html += "<p>Você ainda não tem agendamentos.</p>"
            
            html += "<ul>"
            for app in appointments:
                # Define cor do status
                color_style = "color:black"
                if app.status == 'CONFIRMED': color_style = "color:blue"
                elif app.status == 'CANCELED': color_style = "color:red; text-decoration:line-through"
                elif app.status == 'COMPLETED': color_style = "color:green"

                html += f"<li style='margin-bottom:10px;'>"
                html += f"<b>{app.start_time.strftime('%d/%m/%Y às %H:%M')}</b> - {app.service.name} "
                html += f"(R$ {app.service.price}) - <span style='{color_style}'>{app.status}</span> "
                
                # Botão Cancelar (Só aparece se estiver CONFIRMADO ou PENDENTE)
                if app.status in ['CONFIRMED', 'PENDING']:
                    html += f" <a href='/appointment/cancel/{app.id}' onclick=\"return confirm('Tem certeza que deseja cancelar?');\">"
                    html += f"<button style='color:red; cursor:pointer; font-size:12px;'>❌ Cancelar</button></a>"
                
                html += "</li>"
            html += "</ul>"

        # --- ESTAS LINHAS ESTAVAM A FALTAR: ---
        html += "<br><a href='/'>🏠 Voltar ao Início</a>"
        return html

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