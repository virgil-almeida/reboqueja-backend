# 🚛 ReboqueJá — Backend API

> Plataforma digital de conexão entre motoristas e prestadores de serviço de reboque.

**Desenvolvido por:** Alunos do curso de Desenvolvimento Backend Python — IFMG Betim + CEPEDI  
**Stack:** Django 5 · Django REST Framework · PostgreSQL · JWT

---

## 📋 Sobre o projeto

O ReboqueJá resolve um problema real: quando um veículo quebra, o motorista não sabe a quem recorrer.
Esta API conecta motoristas com caminhões de reboque disponíveis na região, em tempo real.

## 🏗️ Arquitetura de apps

```
reboqueja/
├── users/      # Motoristas e Prestadores
├── services/   # Solicitações e fluxo de status
└── ratings/    # Avaliações e histórico
```

## 🚀 Instalação local

```bash
# Clone o repositório
git clone https://github.com/SEU_USUARIO/reboqueja-backend.git
cd reboqueja-backend

# Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# Execute as migrações
python manage.py migrate

# Inicie o servidor
python manage.py runserver
```

## 🔑 Variáveis de ambiente

Crie um arquivo `.env` baseado no `.env.example`:

```env
SECRET_KEY=sua-chave-secreta
DEBUG=True
DATABASE_URL=postgres://usuario:senha@localhost:5432/reboqueja
```

## 📚 Documentação da API

Com o servidor rodando, acesse:
- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/

## 🧪 Executando os testes

```bash
pytest --cov=. --cov-report=term-missing
```

## 👥 Time

Projeto acadêmico desenvolvido no IFMG Betim em parceria com o CEPEDI.

---

*Prazo: 2 meses · Metodologia: Scrum + Kanban*
