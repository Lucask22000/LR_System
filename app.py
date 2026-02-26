from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from sqlalchemy import inspect, text

from config import config
from models import Categoria, Funcionario, Movimentacao, Produto, db
from routes.estoque_routes import register_estoque_routes
from routes.vendas_routes import register_vendas_routes

# Informacoes do SystemLR
APP_NAME = 'SystemLR'
APP_VERSION = '1.0.0'
APP_DOMAIN = 'systemlr.com'

app = Flask(__name__)
app.config.from_object(config['development'])
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

# Inicializar banco de dados
db.init_app(app)

TIPOS_MOVIMENTACAO_VALIDOS = {Movimentacao.TIPO_ENTRADA, Movimentacao.TIPO_SAIDA}

# Criar tabelas e ajustes simples de schema
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    colunas_movimentacoes = {col['name'] for col in inspector.get_columns('movimentacoes')}
    if 'fornecedor_id' not in colunas_movimentacoes:
        db.session.execute(text('ALTER TABLE movimentacoes ADD COLUMN fornecedor_id INTEGER'))
        db.session.commit()


# ============ DECORADORES DE AUTENTICACAO ============

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'funcionario_id' not in session:
            flash('Voce precisa fazer login para acessar esta pagina.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'funcionario_id' not in session:
                flash('Voce precisa fazer login.', 'warning')
                return redirect(url_for('login'))

            funcionario = Funcionario.query.get(session['funcionario_id'])
            if not funcionario or not funcionario.ativo:
                session.clear()
                flash('Funcionario inativo ou removido.', 'danger')
                return redirect(url_for('login'))

            if funcionario.role not in roles:
                flash('Voce nao tem permissao para acessar esta pagina.', 'danger')
                return redirect(url_for('dashboard'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# ============ FUNCOES AUXILIARES ============

def get_funcionario_logado():
    if 'funcionario_id' in session:
        return Funcionario.query.get(session['funcionario_id'])
    return None


def aplicar_movimentacao_estoque(produto, tipo, quantidade):
    if tipo not in TIPOS_MOVIMENTACAO_VALIDOS:
        return 'Tipo de movimentacao invalido'

    if quantidade <= 0:
        return 'Quantidade deve ser maior que 0'

    if tipo == Movimentacao.TIPO_ENTRADA:
        produto.quantidade_estoque += quantidade
        return None

    if produto.quantidade_estoque < quantidade:
        return 'Quantidade em estoque insuficiente'

    produto.quantidade_estoque -= quantidade
    return None


# ============ ROTAS - AUTENTICACAO ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')

        if not email or not senha:
            flash('Email e senha sao obrigatorios.', 'danger')
            return redirect(url_for('login'))

        funcionario = Funcionario.query.filter_by(email=email).first()

        if funcionario and funcionario.check_password(senha):
            if not funcionario.ativo:
                flash('Usuario inativo. Contate um administrador.', 'danger')
                return redirect(url_for('login'))

            session['funcionario_id'] = funcionario.id
            session['funcionario_nome'] = funcionario.nome
            session['funcionario_role'] = funcionario.role
            db.session.commit()

            flash(f'Bem-vindo, {funcionario.nome}!', 'success')
            return redirect(url_for('dashboard'))

        flash('Email ou senha incorretos.', 'danger')
        return redirect(url_for('login'))

    return render_template('sistema/login.html')


@app.route('/logout')
def logout():
    nome = session.get('funcionario_nome', 'Usuario')
    session.clear()
    flash(f'Ate logo, {nome}!', 'info')
    return redirect(url_for('login'))


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    total_funcionarios = Funcionario.query.count()

    if request.method == 'POST':
        if total_funcionarios > 0 and 'funcionario_id' not in session:
            flash('Acesso negado. Faca login como administrador.', 'danger')
            return redirect(url_for('login'))

        if total_funcionarios > 0:
            funcionario_logado = get_funcionario_logado()
            if not funcionario_logado or funcionario_logado.role != 'admin':
                flash('Apenas administradores podem registrar novos funcionarios.', 'danger')
                return redirect(url_for('dashboard'))

        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmacao_senha = request.form.get('confirmacao_senha', '')
        role = request.form.get('role', 'operador')

        if not nome or not email or not senha:
            flash('Nome, email e senha sao obrigatorios.', 'danger')
            return redirect(url_for('registro'))

        if senha != confirmacao_senha:
            flash('As senhas nao conferem.', 'danger')
            return redirect(url_for('registro'))

        if len(senha) < 6:
            flash('A senha deve ter no minimo 6 caracteres.', 'danger')
            return redirect(url_for('registro'))

        if Funcionario.query.filter_by(email=email).first():
            flash('Email ja cadastrado.', 'danger')
            return redirect(url_for('registro'))

        novo_funcionario = Funcionario(nome=nome, email=email)
        novo_funcionario.set_password(senha)

        if total_funcionarios == 0:
            novo_funcionario.role = 'admin'
        elif role in ['admin', 'gerente', 'caixa', 'operador']:
            novo_funcionario.role = role

        db.session.add(novo_funcionario)
        db.session.commit()

        if total_funcionarios == 0:
            flash(f'Conta do administrador criada com sucesso! Bem-vindo, {nome}!', 'success')
            session['funcionario_id'] = novo_funcionario.id
            session['funcionario_nome'] = novo_funcionario.nome
            session['funcionario_role'] = novo_funcionario.role
            return redirect(url_for('dashboard'))

        flash(f'Funcionario {nome} registrado com sucesso!', 'success')
        return redirect(url_for('listar_funcionarios'))

    return render_template('sistema/registro.html', primeira_vez=(total_funcionarios == 0))


# ============ ROTAS - SISTEMA ============

@app.route('/')
def index():
    return redirect(url_for('boas_vindas'))


@app.route('/dashboard')
@login_required
def dashboard():
    total_produtos = Produto.query.count()
    produtos_em_falta = Produto.query.filter(
        Produto.quantidade_estoque < Produto.quantidade_minima,
        Produto.ativo == True
    ).count()
    valor_total_estoque = db.session.query(
        db.func.sum(Produto.quantidade_estoque * Produto.preco_custo)
    ).scalar() or 0

    movimentacoes_recentes = Movimentacao.query.order_by(Movimentacao.criado_em.desc()).limit(10).all()

    return render_template(
        'dashboard/index.html',
        total_produtos=total_produtos,
        produtos_em_falta=produtos_em_falta,
        valor_total_estoque=f'{valor_total_estoque:.2f}',
        movimentacoes_recentes=movimentacoes_recentes
    )


@app.route('/boas-vindas')
@login_required
def boas_vindas():
    return render_template(
        'sistema/boas_vindas.html',
        app_name=APP_NAME,
        app_version=APP_VERSION,
        app_domain=APP_DOMAIN,
        total_produtos=Produto.query.count(),
        total_categorias=Categoria.query.count()
    )


# ============ ROTAS - FUNCIONARIOS ============

@app.route('/funcionarios')
@require_role('admin', 'gerente')
def listar_funcionarios():
    funcionarios = Funcionario.query.all()
    return render_template('funcionarios/listar.html', funcionarios=funcionarios)


@app.route('/funcionarios/novo', methods=['GET', 'POST'])
@require_role('admin')
def criar_funcionario():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmacao_senha = request.form.get('confirmacao_senha', '')
        role = request.form.get('role', 'operador')

        if not nome or not email or not senha:
            flash('Nome, email e senha sao obrigatorios.', 'danger')
            return redirect(url_for('criar_funcionario'))

        if senha != confirmacao_senha:
            flash('As senhas nao conferem.', 'danger')
            return redirect(url_for('criar_funcionario'))

        if len(senha) < 6:
            flash('A senha deve ter no minimo 6 caracteres.', 'danger')
            return redirect(url_for('criar_funcionario'))

        if Funcionario.query.filter_by(email=email).first():
            flash('Email ja cadastrado.', 'danger')
            return redirect(url_for('criar_funcionario'))

        novo_funcionario = Funcionario(nome=nome, email=email, role=role)
        novo_funcionario.set_password(senha)
        db.session.add(novo_funcionario)
        db.session.commit()

        flash(f'Funcionario {nome} criado com sucesso!', 'success')
        return redirect(url_for('listar_funcionarios'))

    return render_template('funcionarios/criar.html')


@app.route('/funcionarios/<int:funcionario_id>/editar', methods=['GET', 'POST'])
@require_role('admin', 'gerente')
def editar_funcionario(funcionario_id):
    funcionario = Funcionario.query.get_or_404(funcionario_id)

    funcionario_logado = get_funcionario_logado()
    if funcionario_logado.role == 'gerente' and funcionario.role in ['admin', 'gerente'] and funcionario.id != funcionario_logado.id:
        flash('Voce nao tem permissao para editar este funcionario.', 'danger')
        return redirect(url_for('listar_funcionarios'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        role = request.form.get('role', funcionario.role)
        ativo = request.form.get('ativo') == 'on'
        nova_senha = request.form.get('nova_senha', '')

        if not nome or not email:
            flash('Nome e email sao obrigatorios.', 'danger')
            return redirect(url_for('editar_funcionario', funcionario_id=funcionario_id))

        outro_func = Funcionario.query.filter_by(email=email).first()
        if outro_func and outro_func.id != funcionario.id:
            flash('Email ja cadastrado por outro funcionario.', 'danger')
            return redirect(url_for('editar_funcionario', funcionario_id=funcionario_id))

        funcionario.nome = nome
        funcionario.email = email
        funcionario.ativo = ativo

        if funcionario_logado.role == 'admin':
            funcionario.role = role

        if nova_senha:
            if len(nova_senha) < 6:
                flash('A nova senha deve ter no minimo 6 caracteres.', 'danger')
                return redirect(url_for('editar_funcionario', funcionario_id=funcionario_id))
            funcionario.set_password(nova_senha)

        db.session.commit()
        flash('Funcionario atualizado com sucesso!', 'success')
        return redirect(url_for('listar_funcionarios'))

    return render_template('funcionarios/editar.html', funcionario=funcionario)


@app.route('/funcionarios/<int:funcionario_id>/deletar', methods=['POST'])
@require_role('admin')
def deletar_funcionario(funcionario_id):
    if funcionario_id == session.get('funcionario_id'):
        flash('Voce nao pode deletar sua propria conta.', 'danger')
        return redirect(url_for('listar_funcionarios'))

    funcionario = Funcionario.query.get_or_404(funcionario_id)
    try:
        db.session.delete(funcionario)
        db.session.commit()
        flash(f'Funcionario {funcionario.nome} deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar funcionario: {str(e)}', 'danger')

    return redirect(url_for('listar_funcionarios'))


# ============ REGISTRO DE MODULOS DE DOMINIO ============
register_estoque_routes(app, login_required, aplicar_movimentacao_estoque)
register_vendas_routes(app, login_required)


# ============ CONTEXT PROCESSORS ============

@app.context_processor
def inject_user():
    funcionario_logado = get_funcionario_logado()
    return {
        'ano_atual': datetime.utcnow().year,
        'total_alertas': Produto.query.filter(
            Produto.quantidade_estoque < Produto.quantidade_minima,
            Produto.ativo == True
        ).count(),
        'funcionario_logado': funcionario_logado
    }


# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
