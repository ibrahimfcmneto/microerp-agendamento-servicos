# 💈 MicroERP - Agendamento de Serviços (Barbearia)

> **🚀 PROJETO NO AR:** Acesse agora em [https://microerp-agendamento-servicos.vercel.app/](https://microerp-agendamento-servicos.vercel.app/)

## 📖 Sobre o Projeto
Este é um sistema completo de **MicroERP para Barbearias e Salões de Beleza**, desenvolvido para gerenciar agendamentos, controlar horários de funcionamento e fornecer métricas financeiras em tempo real.

O projeto resolve o problema de agendamentos manuais (papel/WhatsApp), permitindo que o cliente escolha o serviço e horário disponível, enquanto o gestor tem controle total sobre a agenda e o faturamento.

## ✨ Funcionalidades Principais

### 👤 Área do Cliente
* **Cadastro e Login:** Sistema seguro de autenticação.
* **Agendamento Online:** Seleção visual de data e horários disponíveis (evita conflitos).
* **Histórico:** O cliente pode ver seus agendamentos futuros e passados.
* **Cancelamento:** Regra de negócio que permite cancelamento apenas com 24h de antecedência.

### 🛡️ Área do Gestor (Admin)
* **Dashboard Executivo:** Visualização de KPIs como *Receita Estimada* e *Taxa de No-Show*.
* **Gestão de Agenda:** Visualização de todos os cortes do dia.
* **Controle de Status:** Marcar agendamentos como *Concluído*, *Faltou (No-Show)* ou *Cancelado*.
* **Configuração de Horários:** Definição de turnos de trabalho (Manhã/Tarde) e dias de folga.
* **Gestão de Serviços:** Adicionar, editar ou remover serviços e preços.
* **Agendamento Manual:** Para encaixar clientes que ligaram ou vieram presencialmente.

## 🛠️ Tecnologias Utilizadas

* **Back-end:** Python, Flask, Flask-SQLAlchemy, Flask-Login.
* **Banco de Dados:** MySQL 8 (Hospedado na Aiven Cloud).
* **Front-end:** HTML5, CSS3 (Responsivo/Mobile-First), Jinja2 Templates.
* **Deploy:** Vercel (Serverless Functions).
* **Segurança:** Bcrypt para hash de senhas e conexão SSL com o banco.

## 🚀 Como Rodar Localmente

### Pré-requisitos
* Python 3.8+
* Git

### Passo a Passo

1.  **Clone o repositório**
    ```bash
    git clone [https://github.com/seu-usuario/microerp-agendamento-servicos.git](https://github.com/seu-usuario/microerp-agendamento-servicos.git)
    cd microerp-agendamento-servicos
    ```

2.  **Crie e ative o ambiente virtual**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Instale as dependências**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Variáveis de Ambiente**
    Crie um arquivo `.env` na raiz do projeto com as credenciais do seu banco MySQL:
    ```ini
    DB_HOST=seu-host-mysql.aivencloud.com
    DB_PORT=27525
    DB_USER=seu-usuario
    DB_PASSWORD=sua-senha
    DB_NAME=defaultdb
    SECRET_KEY=sua-chave-secreta
    ```
    *(Nota: Se usar Aiven, lembre-se de baixar o certificado `ca.pem` e colocar na raiz).*

5.  **Execute o projeto**
    ```bash
    python app.py
    ```
    O sistema criará as tabelas automaticamente e criará um usuário Admin padrão se não existir.

## 🔐 Acesso Administrativo (Demo)

Para testar as funcionalidades de gestor no link de demonstração ou localmente:

* **Email:** `admin@barbearia.com`
* **Senha:** `admin123`

---

Desenvolvido por **Ibrahim Fleury**.
