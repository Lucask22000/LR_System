from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import config
from models import db, Categoria, Produto, Movimentacao, Caixa, Mesa, Pedido, ItemPedido, Funcionario, Fornecedor
from datetime import datetime, timedelta
import os
from functools import wraps
from sqlalchemy import inspect, text

# InformaÃ§Ãµes do SystemLR
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

# Criar tabelas
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    colunas_movimentacoes = {col['name'] for col in inspector.get_columns('movimentacoes')}
    if 'fornecedor_id' not in colunas_movimentacoes:
        db.session.execute(text('ALTER TABLE movimentacoes ADD COLUMN fornecedor_id INTEGER'))
        db.session.commit()


# ============ DECORADORES DE AUTENTICAÇÃO ============

def login_required(f):
    """Decorator para verificar se o usuário está autenticado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'funcionario_id' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def require_role(*roles):
    """Decorator para verificar se o usuário tem a role necessária"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'funcionario_id' not in session:
                flash('Você precisa fazer login.', 'warning')
                return redirect(url_for('login'))
            
            funcionario = Funcionario.query.get(session['funcionario_id'])
            if not funcionario or not funcionario.ativo:
                session.clear()
                flash('Funcionário inativo ou removido.', 'danger')
                return redirect(url_for('login'))
            
            if funcionario.role not in roles:
                flash('Você não tem permissão para acessar esta página.', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============ FUNÇÕES AUXILIARES ============

def get_funcionario_logado():
    """Retorna o funcionário logado ou None"""
    if 'funcionario_id' in session:
        return Funcionario.query.get(session['funcionario_id'])
    return None


def aplicar_movimentacao_estoque(produto, tipo, quantidade):
    """
    Aplica entrada/saida no estoque.
    Retorna None em sucesso ou mensagem de erro.
    """
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

# ============ ROTAS - AUTENTICAÇÃO ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        
        if not email or not senha:
            flash('Email e senha são obrigatórios.', 'danger')
            return redirect(url_for('login'))
        
        funcionario = Funcionario.query.filter_by(email=email).first()
        
        if funcionario and funcionario.check_password(senha):
            if not funcionario.ativo:
                flash('Usuário inativo. Contate um administrador.', 'danger')
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
    """Fazer logout"""
    nome = session.get('funcionario_nome', 'Usuário')
    session.clear()
    flash(f'Até logo, {nome}!', 'info')
    return redirect(url_for('login'))


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Página de registro (primeira vez)"""
    # Se houver funcionários já cadastrados, apenas admin pode registrar novos
    total_funcionarios = Funcionario.query.count()
    
    if request.method == 'POST':
        # Se já há funcionários, precisa estar autenticado como admin
        if total_funcionarios > 0 and 'funcionario_id' not in session:
            flash('Acesso negado. Faça login como administrador.', 'danger')
            return redirect(url_for('login'))
        
        if total_funcionarios > 0:
            funcionario_logado = get_funcionario_logado()
            if not funcionario_logado or funcionario_logado.role != 'admin':
                flash('Apenas administradores podem registrar novos funcionários.', 'danger')
                return redirect(url_for('dashboard'))
        
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmacao_senha = request.form.get('confirmacao_senha', '')
        role = request.form.get('role', 'operador')
        
        if not nome or not email or not senha:
            flash('Nome, email e senha são obrigatórios.', 'danger')
            return redirect(url_for('registro'))
        
        if senha != confirmacao_senha:
            flash('As senhas não conferem.', 'danger')
            return redirect(url_for('registro'))
        
        if len(senha) < 6:
            flash('A senha deve ter no mínimo 6 caracteres.', 'danger')
            return redirect(url_for('registro'))
        
        if Funcionario.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'danger')
            return redirect(url_for('registro'))
        
        novo_funcionario = Funcionario(nome=nome, email=email)
        novo_funcionario.set_password(senha)
        
        # O primeiro funcionário é sempre admin
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
        else:
            flash(f'Funcionário {nome} registrado com sucesso!', 'success')
            return redirect(url_for('listar_funcionarios'))
    
    return render_template('sistema/registro.html', primeira_vez=(total_funcionarios == 0))

# ============ ROTAS - DASHBOARD ============

@app.route('/')
def index():
    """Página inicial"""
    return redirect(url_for('boas_vindas'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal"""
    total_produtos = Produto.query.count()
    produtos_em_falta = Produto.query.filter(
        Produto.quantidade_estoque < Produto.quantidade_minima,
        Produto.ativo == True
    ).count()
    valor_total_estoque = db.session.query(
        db.func.sum(Produto.quantidade_estoque * Produto.preco_custo)
    ).scalar() or 0
    
    # Ãšltimas movimentaÃ§Ãµes
    movimentacoes_recentes = Movimentacao.query.order_by(
        Movimentacao.criado_em.desc()
    ).limit(10).all()
    
    return render_template('dashboard/index.html',
        total_produtos=total_produtos,
        produtos_em_falta=produtos_em_falta,
        valor_total_estoque=f'{valor_total_estoque:.2f}',
        movimentacoes_recentes=movimentacoes_recentes
    )


@app.route('/boas-vindas')
def boas_vindas():
    """Tela de boas-vindas e informações gerais"""
    return render_template(
        'sistema/boas_vindas.html',
        app_name=APP_NAME,
        app_version=APP_VERSION,
        app_domain=APP_DOMAIN,
        total_produtos=Produto.query.count(),
        total_categorias=Categoria.query.count()
    )
# ============ ROTAS - PRODUTOS ============

@app.route('/produtos')
@login_required
def listar_produtos():
    """Lista todos os produtos"""
    categoria_id = request.args.get('categoria_id', type=int)
    busca = request.args.get('busca', '')
    
    query = Produto.query
    
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    
    if busca:
        query = query.filter(
            db.or_(
                Produto.nome.ilike(f'%{busca}%'),
                Produto.codigo.ilike(f'%{busca}%')
            )
        )
    
    produtos = query.all()
    categorias = Categoria.query.all()
    
    return render_template('produtos/produtos.html',
        produtos=produtos,
        categorias=categorias,
        categoria_selecionada=categoria_id,
        busca=busca
    )

@app.route('/produtos/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    """Criar novo produto"""
    if request.method == 'POST':
        try:
            categoria_id = request.form.get('categoria_id', type=int)
            categoria = Categoria.query.get(categoria_id)
            
            if not categoria:
                flash('Categoria invÃ¡lida', 'error')
                return redirect(url_for('novo_produto'))
            
            produto = Produto(
                codigo=request.form.get('codigo').upper(),
                nome=request.form.get('nome'),
                descricao=request.form.get('descricao'),
                categoria_id=categoria_id,
                preco_custo=float(request.form.get('preco_custo', 0)),
                preco_venda=float(request.form.get('preco_venda', 0)),
                quantidade_estoque=int(request.form.get('quantidade_estoque', 0)),
                quantidade_minima=int(request.form.get('quantidade_minima', 5))
            )
            
            db.session.add(produto)
            db.session.commit()
            
            flash(f'Produto "{produto.nome}" criado com sucesso!', 'success')
            return redirect(url_for('listar_produtos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar produto: {str(e)}', 'error')
    
    categorias = Categoria.query.all()
    return render_template('produtos/novo_produto.html', categorias=categorias)

@app.route('/produtos/<int:produto_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_produto(produto_id):
    """Editar produto"""
    produto = Produto.query.get_or_404(produto_id)
    
    if request.method == 'POST':
        try:
            produto.nome = request.form.get('nome')
            produto.descricao = request.form.get('descricao')
            produto.categoria_id = int(request.form.get('categoria_id'))
            produto.preco_custo = float(request.form.get('preco_custo', 0))
            produto.preco_venda = float(request.form.get('preco_venda', 0))
            produto.quantidade_minima = int(request.form.get('quantidade_minima', 5))
            
            db.session.commit()
            flash(f'Produto "{produto.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('listar_produtos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar produto: {str(e)}', 'error')
    
    categorias = Categoria.query.all()
    return render_template('produtos/editar_produto.html', produto=produto, categorias=categorias)

@app.route('/produtos/<int:produto_id>')
@login_required
def visualizar_produto(produto_id):
    """Visualizar detalhes do produto"""
    produto = Produto.query.get_or_404(produto_id)
    movimentacoes = Movimentacao.query.filter_by(produto_id=produto_id).order_by(
        Movimentacao.criado_em.desc()
    ).all()
    
    return render_template('produtos/visualizar_produto.html',
        produto=produto,
        movimentacoes=movimentacoes
    )

@app.route('/produtos/<int:produto_id>/deletar', methods=['POST'])
@login_required
def deletar_produto(produto_id):
    """Deletar produto"""
    produto = Produto.query.get_or_404(produto_id)
    
    try:
        db.session.delete(produto)
        db.session.commit()
        flash(f'Produto "{produto.nome}" deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar produto: {str(e)}', 'error')
    
    return redirect(url_for('listar_produtos'))

# ============ ROTAS - CATEGORIAS ============

@app.route('/categorias')
@login_required
def listar_categorias():
    """Lista todas as categorias"""
    categorias = Categoria.query.all()
    return render_template('categorias/categorias.html', categorias=categorias)

@app.route('/categorias/nova', methods=['GET', 'POST'])
@login_required
def nova_categoria():
    """Criar nova categoria"""
    if request.method == 'POST':
        try:
            categoria = Categoria(
                nome=request.form.get('nome'),
                descricao=request.form.get('descricao')
            )
            db.session.add(categoria)
            db.session.commit()
            flash(f'Categoria "{categoria.nome}" criada com sucesso!', 'success')
            return redirect(url_for('listar_categorias'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar categoria: {str(e)}', 'error')
    
    return render_template('categorias/nova_categoria.html')

@app.route('/categorias/<int:categoria_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_categoria(categoria_id):
    """Editar categoria"""
    categoria = Categoria.query.get_or_404(categoria_id)
    
    if request.method == 'POST':
        try:
            categoria.nome = request.form.get('nome')
            categoria.descricao = request.form.get('descricao')
            db.session.commit()
            flash(f'Categoria "{categoria.nome}" atualizada com sucesso!', 'success')
            return redirect(url_for('listar_categorias'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar categoria: {str(e)}', 'error')
    
    return render_template('categorias/editar_categoria.html', categoria=categoria)

@app.route('/categorias/<int:categoria_id>/deletar', methods=['POST'])
@login_required
def deletar_categoria(categoria_id):
    """Deletar categoria"""
    categoria = Categoria.query.get_or_404(categoria_id)
    
    try:
        db.session.delete(categoria)
        db.session.commit()
        flash(f'Categoria "{categoria.nome}" deletada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar categoria: {str(e)}', 'error')
    
    return redirect(url_for('listar_categorias'))


# ============ ROTAS - FORNECEDORES ============

@app.route('/fornecedores')
@login_required
def listar_fornecedores():
    fornecedores = Fornecedor.query.order_by(Fornecedor.nome.asc()).all()
    return render_template('fornecedores/fornecedores.html', fornecedores=fornecedores)


@app.route('/fornecedores/novo', methods=['GET', 'POST'])
@login_required
def novo_fornecedor():
    if request.method == 'POST':
        try:
            fornecedor = Fornecedor(
                nome=request.form.get('nome', '').strip(),
                contato=request.form.get('contato', '').strip() or None,
                telefone=request.form.get('telefone', '').strip() or None,
                email=request.form.get('email', '').strip() or None,
                ativo=(request.form.get('ativo') == 'on')
            )
            if not fornecedor.nome:
                flash('Nome do fornecedor e obrigatorio.', 'error')
                return redirect(url_for('novo_fornecedor'))

            db.session.add(fornecedor)
            db.session.commit()
            flash(f'Fornecedor "{fornecedor.nome}" cadastrado com sucesso!', 'success')
            return redirect(url_for('listar_fornecedores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar fornecedor: {str(e)}', 'error')

    return render_template('fornecedores/novo_fornecedor.html')


@app.route('/fornecedores/<int:fornecedor_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_fornecedor(fornecedor_id):
    fornecedor = Fornecedor.query.get_or_404(fornecedor_id)

    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            if not nome:
                flash('Nome do fornecedor e obrigatorio.', 'error')
                return redirect(url_for('editar_fornecedor', fornecedor_id=fornecedor_id))

            fornecedor.nome = nome
            fornecedor.contato = request.form.get('contato', '').strip() or None
            fornecedor.telefone = request.form.get('telefone', '').strip() or None
            fornecedor.email = request.form.get('email', '').strip() or None
            fornecedor.ativo = (request.form.get('ativo') == 'on')

            db.session.commit()
            flash(f'Fornecedor "{fornecedor.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('listar_fornecedores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar fornecedor: {str(e)}', 'error')

    return render_template('fornecedores/editar_fornecedor.html', fornecedor=fornecedor)


@app.route('/fornecedores/<int:fornecedor_id>/deletar', methods=['POST'])
@login_required
def deletar_fornecedor(fornecedor_id):
    fornecedor = Fornecedor.query.get_or_404(fornecedor_id)
    try:
        db.session.delete(fornecedor)
        db.session.commit()
        flash(f'Fornecedor "{fornecedor.nome}" removido com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover fornecedor: {str(e)}', 'error')

    return redirect(url_for('listar_fornecedores'))

@app.route('/movimentacoes/rapido/<int:produto_id>', methods=['GET', 'POST'])
@login_required
def movimentacao_rapida(produto_id):
    """Movimentação rápida por produto"""
    produto = Produto.query.get_or_404(produto_id)
    
    if request.method == 'POST':
        try:
            tipo = request.form.get('tipo')
            quantidade = int(request.form.get('quantidade'))
            fornecedor_id = request.form.get('fornecedor_id', type=int)

            erro = aplicar_movimentacao_estoque(produto, tipo, quantidade)
            if erro:
                flash(erro, 'error')
                return redirect(url_for('movimentacao_rapida', produto_id=produto_id))

            fornecedor = None
            if tipo == Movimentacao.TIPO_ENTRADA and fornecedor_id:
                fornecedor = Fornecedor.query.get(fornecedor_id)
                if not fornecedor:
                    flash('Fornecedor invalido.', 'error')
                    return redirect(url_for('movimentacao_rapida', produto_id=produto_id))
            
            # Registrar movimentação
            movimentacao = Movimentacao(
                produto_id=produto_id,
                fornecedor_id=(fornecedor.id if fornecedor else None),
                tipo=tipo,
                quantidade=quantidade,
                motivo=request.form.get('motivo'),
                observacoes=request.form.get('observacoes')
            )
            
            db.session.add(movimentacao)
            db.session.commit()
            
            flash('Movimentação registrada com sucesso!', 'success')
            return redirect(url_for('listar_movimentacoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar movimentação: {str(e)}', 'error')
    
    fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome.asc()).all()
    return render_template('movimentacoes/movimentacao_rapida.html', produto=produto, fornecedores=fornecedores)

# ============ ROTAS - MOVIMENTAÃ‡Ã•ES (ESTOQUE) ============

@app.route('/movimentacoes')
@login_required
def listar_movimentacoes():
    """Lista todas as movimentaÃ§Ãµes"""
    produto_id = request.args.get('produto_id', type=int)
    tipo = request.args.get('tipo', '')
    fornecedor_id = request.args.get('fornecedor_id', type=int)
    
    query = Movimentacao.query
    
    if produto_id:
        query = query.filter_by(produto_id=produto_id)
    
    if tipo and tipo in ['entrada', 'saida']:
        query = query.filter_by(tipo=tipo)

    if fornecedor_id:
        query = query.filter_by(fornecedor_id=fornecedor_id)
    
    movimentacoes = query.order_by(Movimentacao.criado_em.desc()).all()
    produtos = Produto.query.all()
    fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome.asc()).all()
    
    return render_template('movimentacoes/movimentacoes.html',
        movimentacoes=movimentacoes,
        produtos=produtos,
        fornecedores=fornecedores,
        produto_selecionado=produto_id,
        tipo_selecionado=tipo,
        fornecedor_selecionado=fornecedor_id
    )

@app.route('/movimentacoes/nova', methods=['GET', 'POST'])
@login_required
def nova_movimentacao():
    """Registrar nova movimentação"""
    if request.method == 'POST':
        try:
            produto_id = int(request.form.get('produto_id'))
            tipo = request.form.get('tipo')
            quantidade = int(request.form.get('quantidade'))
            fornecedor_id = request.form.get('fornecedor_id', type=int)
            
            produto = Produto.query.get(produto_id)
            if not produto:
                flash('Produto não encontrado', 'error')
                return redirect(url_for('nova_movimentacao'))

            erro = aplicar_movimentacao_estoque(produto, tipo, quantidade)
            if erro:
                flash(erro, 'error')
                return redirect(url_for('nova_movimentacao'))

            fornecedor = None
            if tipo == Movimentacao.TIPO_ENTRADA and fornecedor_id:
                fornecedor = Fornecedor.query.get(fornecedor_id)
                if not fornecedor:
                    flash('Fornecedor invalido.', 'error')
                    return redirect(url_for('nova_movimentacao'))
            
            # Registrar movimentação
            movimentacao = Movimentacao(
                produto_id=produto_id,
                fornecedor_id=(fornecedor.id if fornecedor else None),
                tipo=tipo,
                quantidade=quantidade,
                motivo=request.form.get('motivo'),
                observacoes=request.form.get('observacoes')
            )
            
            db.session.add(movimentacao)
            db.session.commit()
            
            flash('Movimentação registrada com sucesso!', 'success')
            return redirect(url_for('listar_movimentacoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar movimentação: {str(e)}', 'error')
    
    produtos = Produto.query.filter_by(ativo=True).all()
    fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome.asc()).all()
    return render_template('movimentacoes/nova_movimentacao.html', produtos=produtos, fornecedores=fornecedores)

# ============ ROTAS - RELATÃ“RIOS ============

@app.route('/relatorios')
@login_required
def relatorios():
    """PÃ¡gina de relatÃ³rios"""
    total_produtos = Produto.query.count()
    produtos_ativos = Produto.query.filter_by(ativo=True).count()
    produtos_inativos = Produto.query.filter_by(ativo=False).count()
    
    # Produtos em falta
    produtos_em_falta = Produto.query.filter(
        Produto.quantidade_estoque < Produto.quantidade_minima,
        Produto.ativo == True
    ).all()
    
    # Valor total de estoque
    valor_total = db.session.query(
        db.func.sum(Produto.quantidade_estoque * Produto.preco_custo)
    ).scalar() or 0
    
    # Produtos com maior valor em estoque
    produtos_maior_valor = db.session.query(
        Produto,
        (Produto.quantidade_estoque * Produto.preco_custo).label('valor_total')
    ).order_by(db.desc('valor_total')).limit(10).all()
    
    # MovimentaÃ§Ãµes do Ãºltimo mÃªs
    data_limite = datetime.utcnow() - timedelta(days=30)
    movimentacoes_mes = Movimentacao.query.filter(
        Movimentacao.criado_em >= data_limite
    ).count()
    
    return render_template('relatorios/relatorios.html',
        total_produtos=total_produtos,
        produtos_ativos=produtos_ativos,
        produtos_inativos=produtos_inativos,
        produtos_em_falta=produtos_em_falta,
        valor_total_estoque=f'{valor_total:.2f}',
        produtos_maior_valor=produtos_maior_valor,
        movimentacoes_mes=movimentacoes_mes
    )


# ============ ROTAS - CAIXAS ============

@app.route('/caixas')
@login_required
def listar_caixas():
    caixas = Caixa.query.all()
    return render_template('caixas/caixas.html', caixas=caixas)

@app.route('/caixas/nova', methods=['GET', 'POST'])
@login_required
def nova_caixa():
    if request.method == 'POST':
        try:
            nome = request.form.get('nome')
            saldo = float(request.form.get('saldo_inicial') or 0)
            caixa = Caixa(nome=nome, saldo_inicial=saldo, saldo_atual=saldo)
            db.session.add(caixa)
            db.session.commit()
            flash(f'Caixa "{caixa.nome}" criado com sucesso!', 'success')
            return redirect(url_for('listar_caixas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar caixa: {str(e)}', 'error')
    return render_template('caixas/nova_caixa.html')

@app.route('/caixas/<int:caixa_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_caixa(caixa_id):
    caixa = Caixa.query.get_or_404(caixa_id)
    if request.method == 'POST':
        try:
            caixa.nome = request.form.get('nome', caixa.nome)
            caixa.saldo_atual = float(request.form.get('saldo_atual', caixa.saldo_atual))
            aberto = request.form.get('aberto')
            caixa.aberto = bool(aberto == 'on')
            if not caixa.aberto and not caixa.fechado_em:
                caixa.fechado_em = datetime.utcnow()
            db.session.commit()
            flash(f'Caixa "{caixa.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('listar_caixas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar caixa: {str(e)}', 'error')
    return render_template('caixas/editar_caixa.html', caixa=caixa)

@app.route('/caixas/<int:caixa_id>/deletar', methods=['POST'])
@login_required
def deletar_caixa(caixa_id):
    caixa = Caixa.query.get_or_404(caixa_id)
    try:
        db.session.delete(caixa)
        db.session.commit()
        flash(f'Caixa "{caixa.nome}" deletado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar caixa: {str(e)}', 'error')
    return redirect(url_for('listar_caixas'))

# ============ ROTAS - MESAS ============

@app.route('/mesas')
@login_required
def listar_mesas():
    mesas = Mesa.query.all()
    return render_template('mesas/mesas.html', mesas=mesas)

@app.route('/mesas/nova', methods=['GET', 'POST'])
@login_required
def nova_mesa():
    if request.method == 'POST':
        try:
            numero = request.form.get('numero')
            capacidade = int(request.form.get('capacidade') or 1)
            mesa = Mesa(numero=numero, capacidade=capacidade, status='livre')
            db.session.add(mesa)
            db.session.commit()
            flash(f'Mesa "{mesa.numero}" criada com sucesso!', 'success')
            return redirect(url_for('listar_mesas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar mesa: {str(e)}', 'error')
    return render_template('mesas/nova_mesa.html')

@app.route('/mesas/<int:mesa_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_mesa(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    if request.method == 'POST':
        try:
            mesa.numero = request.form.get('numero', mesa.numero)
            mesa.capacidade = int(request.form.get('capacidade', mesa.capacidade))
            mesa.status = request.form.get('status', mesa.status)
            db.session.commit()
            flash(f'Mesa "{mesa.numero}" atualizada!', 'success')
            return redirect(url_for('listar_mesas'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar mesa: {str(e)}', 'error')
    return render_template('mesas/editar_mesa.html', mesa=mesa)

@app.route('/mesas/<int:mesa_id>/deletar', methods=['POST'])
@login_required
def deletar_mesa(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    try:
        db.session.delete(mesa)
        db.session.commit()
        flash(f'Mesa "{mesa.numero}" deletada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar mesa: {str(e)}', 'error')
    return redirect(url_for('listar_mesas'))

# ============ ROTAS - PEDIDOS ============

@app.route('/pedidos')
@login_required
def listar_pedidos():
    pedidos = Pedido.query.all()
    return render_template('pedidos/pedidos.html', pedidos=pedidos)

@app.route('/pedidos/novo', methods=['GET', 'POST'])
@login_required
def novo_pedido():
    produtos = Produto.query.filter_by(ativo=True).all()
    mesas = Mesa.query.all()
    caixas = Caixa.query.filter_by(aberto=True).all()
    if request.method == 'POST':
        try:
            mesa_id = request.form.get('mesa_id') or None
            caixa_id = request.form.get('caixa_id') or None
            observacoes = request.form.get('observacoes')
            pedido = Pedido(mesa_id=mesa_id, caixa_id=caixa_id, observacoes=observacoes)
            db.session.add(pedido)
            db.session.flush()
            total = 0
            # items
            for i in range(int(request.form.get('item_count',0))):
                pid = request.form.get(f'produto_{i}')
                qty = int(request.form.get(f'quantidade_{i}',1))
                if not pid: continue
                prod = Produto.query.get(pid)
                if not prod: continue
                ip = ItemPedido(pedido_id=pedido.id, produto_id=prod.id, quantidade=qty, preco_unitario=prod.preco_venda)
                db.session.add(ip)
                total += qty * prod.preco_venda
            pedido.total = total
            db.session.commit()
            flash('Pedido criado com sucesso!', 'success')
            return redirect(url_for('listar_pedidos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar pedido: {str(e)}', 'error')
    return render_template('pedidos/novo_pedido.html', produtos=produtos, mesas=mesas, caixas=caixas)

@app.route('/pedidos/<int:pedido_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    produtos = Produto.query.filter_by(ativo=True).all()
    mesas = Mesa.query.all()
    caixas = Caixa.query.all()
    if request.method == 'POST':
        try:
            pedido.mesa_id = request.form.get('mesa_id') or None
            pedido.caixa_id = request.form.get('caixa_id') or None
            pedido.status = request.form.get('status', pedido.status)
            pedido.observacoes = request.form.get('observacoes', pedido.observacoes)
            # rebuild items
            pedido.itens.clear()
            total = 0
            for i in range(int(request.form.get('item_count',0))):
                pid = request.form.get(f'produto_{i}')
                qty = int(request.form.get(f'quantidade_{i}',1))
                if not pid: continue
                prod = Produto.query.get(pid)
                if not prod: continue
                ip = ItemPedido(pedido_id=pedido.id, produto_id=prod.id, quantidade=qty, preco_unitario=prod.preco_venda)
                db.session.add(ip)
                total += qty * prod.preco_venda
            pedido.total = total
            if pedido.status == 'fechado' and not pedido.fechado_em:
                pedido.fechado_em = datetime.utcnow()
                # reduce stock
                for ip in pedido.itens:
                    prod = Produto.query.get(ip.produto_id)
                    if prod:
                        prod.quantidade_estoque -= ip.quantidade
                        mov = Movimentacao(
                            produto_id=prod.id,
                            tipo=Movimentacao.TIPO_SAIDA,
                            quantidade=ip.quantidade,
                            motivo='venda',
                            observacoes=f'Pedido {pedido.id}'
                        )
                        db.session.add(mov)
            db.session.commit()
            flash('Pedido atualizado com sucesso!', 'success')
            return redirect(url_for('listar_pedidos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar pedido: {str(e)}', 'error')
    return render_template('pedidos/editar_pedido.html', pedido=pedido, produtos=produtos, mesas=mesas, caixas=caixas)

@app.route('/pedidos/<int:pedido_id>/deletar', methods=['POST'])
@login_required
def deletar_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    try:
        db.session.delete(pedido)
        db.session.commit()
        flash('Pedido excluído.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir pedido: {str(e)}', 'error')
    return redirect(url_for('listar_pedidos'))

# ============ ROTAS - VENDAS ============

@app.route('/vendas')
@login_required
def listar_vendas():
    vendas = Pedido.query.filter_by(status='fechado').all()
    return render_template('vendas/vendas.html', vendas=vendas)


# ============ ROTAS - FUNCIONÁRIOS ============

@app.route('/funcionarios')
@require_role('admin', 'gerente')
def listar_funcionarios():
    """Lista todos os funcionários"""
    funcionarios = Funcionario.query.all()
    return render_template('funcionarios/listar.html', funcionarios=funcionarios)


@app.route('/funcionarios/novo', methods=['GET', 'POST'])
@require_role('admin')
def criar_funcionario():
    """Cria novo funcionário"""
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')
        confirmacao_senha = request.form.get('confirmacao_senha', '')
        role = request.form.get('role', 'operador')
        
        if not nome or not email or not senha:
            flash('Nome, email e senha são obrigatórios.', 'danger')
            return redirect(url_for('criar_funcionario'))
        
        if senha != confirmacao_senha:
            flash('As senhas não conferem.', 'danger')
            return redirect(url_for('criar_funcionario'))
        
        if len(senha) < 6:
            flash('A senha deve ter no mínimo 6 caracteres.', 'danger')
            return redirect(url_for('criar_funcionario'))
        
        if Funcionario.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'danger')
            return redirect(url_for('criar_funcionario'))
        
        novo_funcionario = Funcionario(nome=nome, email=email, role=role)
        novo_funcionario.set_password(senha)
        
        db.session.add(novo_funcionario)
        db.session.commit()
        
        flash(f'Funcionário {nome} criado com sucesso!', 'success')
        return redirect(url_for('listar_funcionarios'))
    
    return render_template('funcionarios/criar.html')


@app.route('/funcionarios/<int:funcionario_id>/editar', methods=['GET', 'POST'])
@require_role('admin', 'gerente')
def editar_funcionario(funcionario_id):
    """Edita um funcionário"""
    funcionario = Funcionario.query.get_or_404(funcionario_id)
    
    # Gerentes só podem editar a si mesmos ou operadores/caixas
    funcionario_logado = get_funcionario_logado()
    if funcionario_logado.role == 'gerente' and funcionario.role in ['admin', 'gerente'] and funcionario.id != funcionario_logado.id:
        flash('Você não tem permissão para editar este funcionário.', 'danger')
        return redirect(url_for('listar_funcionarios'))
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        role = request.form.get('role', funcionario.role)
        ativo = request.form.get('ativo') == 'on'
        nova_senha = request.form.get('nova_senha', '')
        
        if not nome or not email:
            flash('Nome e email são obrigatórios.', 'danger')
            return redirect(url_for('editar_funcionario', funcionario_id=funcionario_id))
        
        # Verificar se outro funcionário já usa este email
        outro_func = Funcionario.query.filter_by(email=email).first()
        if outro_func and outro_func.id != funcionario.id:
            flash('Email já cadastrado por outro funcionário.', 'danger')
            return redirect(url_for('editar_funcionario', funcionario_id=funcionario_id))
        
        funcionario.nome = nome
        funcionario.email = email
        funcionario.ativo = ativo
        
        # Apenas admin pode mudar role
        if funcionario_logado.role == 'admin':
            funcionario.role = role
        
        # Se forneceu nova senha, atualiza
        if nova_senha:
            if len(nova_senha) < 6:
                flash('A nova senha deve ter no mínimo 6 caracteres.', 'danger')
                return redirect(url_for('editar_funcionario', funcionario_id=funcionario_id))
            funcionario.set_password(nova_senha)
        
        db.session.commit()
        flash('Funcionário atualizado com sucesso!', 'success')
        return redirect(url_for('listar_funcionarios'))
    
    return render_template('funcionarios/editar.html', funcionario=funcionario)


@app.route('/funcionarios/<int:funcionario_id>/deletar', methods=['POST'])
@require_role('admin')
def deletar_funcionario(funcionario_id):
    """Deleta um funcionário"""
    if funcionario_id == session.get('funcionario_id'):
        flash('Você não pode deletar sua própria conta.', 'danger')
        return redirect(url_for('listar_funcionarios'))
    
    funcionario = Funcionario.query.get_or_404(funcionario_id)
    
    try:
        db.session.delete(funcionario)
        db.session.commit()
        flash(f'Funcionário {funcionario.nome} deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar funcionário: {str(e)}', 'danger')
    
    return redirect(url_for('listar_funcionarios'))


# ============ CONTEXT PROCESSORS ============

@app.context_processor
def inject_user():
    """Injeta dados globais nos templates"""
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

# ============ MAIN ============

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
