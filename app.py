from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from config import config
from models import db, Categoria, Produto, Movimentacao, Caixa, Mesa, Pedido, ItemPedido
from datetime import datetime, timedelta
import os

# InformaÃ§Ãµes do SystemLR
APP_NAME = 'SystemLR'
APP_VERSION = '1.0.0'
APP_DOMAIN = 'systemlr.com'

app = Flask(__name__)
app.config.from_object(config['development'])

# Inicializar banco de dados
db.init_app(app)

TIPOS_MOVIMENTACAO_VALIDOS = {Movimentacao.TIPO_ENTRADA, Movimentacao.TIPO_SAIDA}

# Criar tabelas
with app.app_context():
    db.create_all()


def obter_categorias_menu():
    """Retorna categorias ordenadas para menu global."""
    return Categoria.query.order_by(Categoria.nome.asc()).all()


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

# ============ ROTAS - DASHBOARD ============

@app.route('/')
def index():
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
    
    return render_template('index.html',
        total_produtos=total_produtos,
        produtos_em_falta=produtos_em_falta,
        valor_total_estoque=f'{valor_total_estoque:.2f}',
        movimentacoes_recentes=movimentacoes_recentes
    )

# ============ ROTAS - PRODUTOS ============

@app.route('/produtos')
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
    
    return render_template('produtos.html',
        produtos=produtos,
        categorias=categorias,
        categoria_selecionada=categoria_id,
        busca=busca
    )

@app.route('/produtos/novo', methods=['GET', 'POST'])
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
    return render_template('novo_produto.html', categorias=categorias)

@app.route('/produtos/<int:produto_id>/editar', methods=['GET', 'POST'])
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
    return render_template('editar_produto.html', produto=produto, categorias=categorias)

@app.route('/produtos/<int:produto_id>')
def visualizar_produto(produto_id):
    """Visualizar detalhes do produto"""
    produto = Produto.query.get_or_404(produto_id)
    movimentacoes = Movimentacao.query.filter_by(produto_id=produto_id).order_by(
        Movimentacao.criado_em.desc()
    ).all()
    
    return render_template('visualizar_produto.html',
        produto=produto,
        movimentacoes=movimentacoes
    )

@app.route('/produtos/<int:produto_id>/deletar', methods=['POST'])
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
def listar_categorias():
    """Lista todas as categorias"""
    categorias = Categoria.query.all()
    return render_template('categorias.html', categorias=categorias)

@app.route('/categorias/nova', methods=['GET', 'POST'])
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
    
    return render_template('nova_categoria.html')

@app.route('/categorias/<int:categoria_id>/editar', methods=['GET', 'POST'])
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
    
    return render_template('editar_categoria.html', categoria=categoria)

@app.route('/categorias/<int:categoria_id>/deletar', methods=['POST'])
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

# ============ ROTAS - SCANNER DE CÃ“DIGO DE BARRAS ============

@app.route('/scanner')
def scanner():
    """PÃ¡gina do scanner de cÃ³digo de barras"""
    return render_template('scanner.html')

@app.route('/movimentacoes/rapido/<int:produto_id>', methods=['GET', 'POST'])
def movimentacao_rapida(produto_id):
    """Movimentação rápida via scanner"""
    produto = Produto.query.get_or_404(produto_id)
    
    if request.method == 'POST':
        try:
            tipo = request.form.get('tipo')
            quantidade = int(request.form.get('quantidade'))

            erro = aplicar_movimentacao_estoque(produto, tipo, quantidade)
            if erro:
                flash(erro, 'error')
                return redirect(url_for('movimentacao_rapida', produto_id=produto_id))
            
            # Registrar movimentação
            movimentacao = Movimentacao(
                produto_id=produto_id,
                tipo=tipo,
                quantidade=quantidade,
                motivo=request.form.get('motivo'),
                observacoes=request.form.get('observacoes')
            )
            
            db.session.add(movimentacao)
            db.session.commit()
            
            flash('Movimentação registrada com sucesso!', 'success')
            return redirect(url_for('scanner'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar movimentação: {str(e)}', 'error')
    
    return render_template('movimentacao_rapida.html', produto=produto)

# ============ ROTAS - MOVIMENTAÃ‡Ã•ES (ESTOQUE) ============

@app.route('/movimentacoes')
def listar_movimentacoes():
    """Lista todas as movimentaÃ§Ãµes"""
    produto_id = request.args.get('produto_id', type=int)
    tipo = request.args.get('tipo', '')
    
    query = Movimentacao.query
    
    if produto_id:
        query = query.filter_by(produto_id=produto_id)
    
    if tipo and tipo in ['entrada', 'saida']:
        query = query.filter_by(tipo=tipo)
    
    movimentacoes = query.order_by(Movimentacao.criado_em.desc()).all()
    produtos = Produto.query.all()
    
    return render_template('movimentacoes.html',
        movimentacoes=movimentacoes,
        produtos=produtos,
        produto_selecionado=produto_id,
        tipo_selecionado=tipo
    )

@app.route('/movimentacoes/nova', methods=['GET', 'POST'])
def nova_movimentacao():
    """Registrar nova movimentaÃ§Ã£o"""
    if request.method == 'POST':
        try:
            produto_id = int(request.form.get('produto_id'))
            tipo = request.form.get('tipo')
            quantidade = int(request.form.get('quantidade'))
            
            if tipo not in ['entrada', 'saida']:
                flash('Tipo de movimentaÃ§Ã£o invÃ¡lido', 'error')
                return redirect(url_for('nova_movimentacao'))
            
            if quantidade <= 0:
                flash('Quantidade deve ser maior que 0', 'error')
                return redirect(url_for('nova_movimentacao'))
            
            produto = Produto.query.get(produto_id)
            if not produto:
                flash('Produto nÃ£o encontrado', 'error')
                return redirect(url_for('nova_movimentacao'))
            
            # Atualizar estoque
            if tipo == 'entrada':
                produto.quantidade_estoque += quantidade
            else:  # saida
                if produto.quantidade_estoque < quantidade:
                    flash('Quantidade em estoque insuficiente', 'error')
                    return redirect(url_for('nova_movimentacao'))
                produto.quantidade_estoque -= quantidade
            
            # Registrar movimentaÃ§Ã£o
            movimentacao = Movimentacao(
                produto_id=produto_id,
                tipo=tipo,
                quantidade=quantidade,
                motivo=request.form.get('motivo'),
                observacoes=request.form.get('observacoes')
            )
            
            db.session.add(movimentacao)
            db.session.commit()
            
            flash('MovimentaÃ§Ã£o registrada com sucesso!', 'success')
            return redirect(url_for('listar_movimentacoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar movimentaÃ§Ã£o: {str(e)}', 'error')
    
    produtos = Produto.query.filter_by(ativo=True).all()
    return render_template('nova_movimentacao.html', produtos=produtos)

# ============ ROTAS - RELATÃ“RIOS ============

@app.route('/relatorios')
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
    
    return render_template('relatorios.html',
        total_produtos=total_produtos,
        produtos_ativos=produtos_ativos,
        produtos_inativos=produtos_inativos,
        produtos_em_falta=produtos_em_falta,
        valor_total_estoque=f'{valor_total:.2f}',
        produtos_maior_valor=produtos_maior_valor,
        movimentacoes_mes=movimentacoes_mes
    )

# ============ API - ENDPOINTS PARA JAVASCRIPT ============

@app.route('/api-documentation')
def api_documentation():
    """PÃ¡gina simples descrevendo as APIs disponÃ­veis"""
    endpoints = [
        {'path': '/api/produtos/json', 'methods': ['GET'], 'description': 'Lista produtos'},
        {'path': '/api/caixas', 'methods': ['GET','POST'], 'description': 'Cadastra/lista caixas'},
        {'path': '/api/caixas/<id>', 'methods': ['GET','PUT','DELETE'], 'description': 'OperaÃ§Ãµes com caixa especÃ­fica'},
        {'path': '/api/mesas', 'methods': ['GET','POST'], 'description': 'Cadastra/lista mesas'},
        {'path': '/api/mesas/<id>', 'methods': ['GET','PUT','DELETE'], 'description': 'OperaÃ§Ãµes com mesa'},
        {'path': '/api/pedidos', 'methods': ['GET','POST'], 'description': 'Cadastra/lista pedidos'},
        {'path': '/api/pedidos/<id>', 'methods': ['GET','PUT','DELETE'], 'description': 'OperaÃ§Ãµes com pedido'},
        {'path': '/api/vendas', 'methods': ['GET'], 'description': 'Lista vendas (pedidos fechados)'},
        {'path': '/api/sistema-info', 'methods': ['GET'], 'description': 'InformaÃ§Ãµes do sistema'}
    ]
    return render_template('api_documentation.html', endpoints=endpoints)


@app.route('/api/produtos/json')
def api_produtos():
    """API para obter produtos em JSON"""
    produtos = Produto.query.all()
    return jsonify([{
        'id': p.id,
        'codigo': p.codigo,
        'nome': p.nome,
        'categoria': p.categoria.nome,
        'preco_venda': p.preco_venda,
        'quantidade': p.quantidade_estoque,
        'em_falta': p.em_falta
    } for p in produtos])


# ======== NOVAS APIs DE VENDAS / CAIXA / MESAS / PEDIDOS ========

@app.route('/api/caixas', methods=['GET', 'POST'])
def api_caixas():
    if request.method == 'GET':
        caixas = Caixa.query.all()
        return jsonify([{
            'id': c.id,
            'nome': c.nome,
            'saldo_inicial': c.saldo_inicial,
            'saldo_atual': c.saldo_atual,
            'aberto': c.aberto
        } for c in caixas])

    data = request.get_json() or {}
    Caixa_obj = Caixa(
        nome=data.get('nome'),
        saldo_inicial=data.get('saldo_inicial', 0),
        saldo_atual=data.get('saldo_inicial', 0),
        aberto=bool(data.get('aberto', True))
    )
    db.session.add(Caixa_obj)
    db.session.commit()
    return jsonify({'id': Caixa_obj.id}), 201

@app.route('/api/caixas/<int:caixa_id>', methods=['GET', 'PUT', 'DELETE'])
def api_caixa(caixa_id):
    caixa = Caixa.query.get_or_404(caixa_id)
    if request.method == 'GET':
        return jsonify({
            'id': caixa.id,
            'nome': caixa.nome,
            'saldo_inicial': caixa.saldo_inicial,
            'saldo_atual': caixa.saldo_atual,
            'aberto': caixa.aberto
        })
    if request.method == 'PUT':
        data = request.get_json() or {}
        caixa.nome = data.get('nome', caixa.nome)
        caixa.saldo_atual = data.get('saldo_atual', caixa.saldo_atual)
        caixa.aberto = data.get('aberto', caixa.aberto)
        if not caixa.aberto:
            caixa.fechado_em = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'ok'})
    if request.method == 'DELETE':
        db.session.delete(caixa)
        db.session.commit()
        return ('', 204)

@app.route('/api/mesas', methods=['GET', 'POST'])
def api_mesas():
    if request.method == 'GET':
        mesas = Mesa.query.all()
        return jsonify([{
            'id': m.id,
            'numero': m.numero,
            'capacidade': m.capacidade,
            'status': m.status
        } for m in mesas])
    data = request.get_json() or {}
    mesa = Mesa(
        numero=data.get('numero'),
        capacidade=data.get('capacidade', 4),
        status=data.get('status', 'livre')
    )
    db.session.add(mesa)
    db.session.commit()
    return jsonify({'id': mesa.id}), 201

@app.route('/api/mesas/<int:mesa_id>', methods=['GET', 'PUT', 'DELETE'])
def api_mesa(mesa_id):
    mesa = Mesa.query.get_or_404(mesa_id)
    if request.method == 'GET':
        return jsonify({
            'id': mesa.id,
            'numero': mesa.numero,
            'capacidade': mesa.capacidade,
            'status': mesa.status
        })
    if request.method == 'PUT':
        data = request.get_json() or {}
        mesa.numero = data.get('numero', mesa.numero)
        mesa.capacidade = data.get('capacidade', mesa.capacidade)
        mesa.status = data.get('status', mesa.status)
        db.session.commit()
        return jsonify({'status': 'ok'})
    if request.method == 'DELETE':
        db.session.delete(mesa)
        db.session.commit()
        return ('', 204)

@app.route('/api/pedidos', methods=['GET', 'POST'])
def api_pedidos():
    if request.method == 'GET':
        pedidos = Pedido.query.all()
        return jsonify([{
            'id': p.id,
            'mesa_id': p.mesa_id,
            'caixa_id': p.caixa_id,
            'total': p.total,
            'status': p.status
        } for p in pedidos])
    data = request.get_json() or {}
    pedido = Pedido(
        mesa_id=data.get('mesa_id'),
        caixa_id=data.get('caixa_id'),
        status=data.get('status', 'aberto'),
        observacoes=data.get('observacoes')
    )
    db.session.add(pedido)
    db.session.commit()
    # adicionar itens se existir lista
    for item in data.get('itens', []):
        prod = Produto.query.get(item['produto_id'])
        if not prod: continue
        ip = ItemPedido(
            pedido_id=pedido.id,
            produto_id=prod.id,
            quantidade=item.get('quantidade',1),
            preco_unitario=item.get('preco_unitario', prod.preco_venda)
        )
        db.session.add(ip)
    pedido.calcular_total()
    db.session.commit()
    return jsonify({'id': pedido.id}), 201

@app.route('/api/pedidos/<int:pedido_id>', methods=['GET', 'PUT', 'DELETE'])
def api_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    if request.method == 'GET':
        return jsonify({
            'id': pedido.id,
            'mesa_id': pedido.mesa_id,
            'caixa_id': pedido.caixa_id,
            'total': pedido.total,
            'status': pedido.status,
            'itens': [{
                'produto_id': i.produto_id,
                'quantidade': i.quantidade,
                'preco_unitario': i.preco_unitario
            } for i in pedido.itens]
        })
    if request.method == 'PUT':
        data = request.get_json() or {}
        pedido.status = data.get('status', pedido.status)
        pedido.observacoes = data.get('observacoes', pedido.observacoes)
        # atualizar itens se enviado
        if 'itens' in data:
            pedido.itens.clear()
            for item in data['itens']:
                prod = Produto.query.get(item['produto_id'])
                if not prod: continue
                ip = ItemPedido(
                    pedido_id=pedido.id,
                    produto_id=prod.id,
                    quantidade=item.get('quantidade',1),
                    preco_unitario=item.get('preco_unitario', prod.preco_venda)
                )
                db.session.add(ip)
        pedido.calcular_total()
        if pedido.status == 'fechado':
            pedido.fechado_em = datetime.utcnow()
            # reduzir estoque e registrar movimentaÃ§Ã£o
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
        return jsonify({'status':'ok'})
    if request.method == 'DELETE':
        db.session.delete(pedido)
        db.session.commit()
        return ('',204)

@app.route('/api/vendas', methods=['GET'])
def api_vendas():
    """Retorna pedidos fechados como vendas"""
    vendas = Pedido.query.filter_by(status='fechado').all()
    return jsonify([{
        'id': v.id,
        'total': v.total,
        'caixa_id': v.caixa_id,
        'mesa_id': v.mesa_id,
        'data': v.fechado_em
    } for v in vendas])

@app.route('/api/categorias/json')
def api_categorias():
    """API para obter categorias em JSON"""
    categorias = Categoria.query.all()
    return jsonify([{
        'id': c.id,
        'nome': c.nome,
        'total_produtos': len(c.produtos)
    } for c in categorias])

@app.route('/api/estoque/resumo')
def api_estoque_resumo():
    """API para obter resumo do estoque"""
    total_itens = db.session.query(db.func.sum(Produto.quantidade_estoque)).scalar() or 0
    valor_total = db.session.query(
        db.func.sum(Produto.quantidade_estoque * Produto.preco_custo)
    ).scalar() or 0
    
    return jsonify({
        'total_itens': total_itens,
        'valor_total': round(valor_total, 2),
        'produtos_em_falta': Produto.query.filter(
            Produto.quantidade_estoque < Produto.quantidade_minima
        ).count()
    })

@app.route('/api/produto/codigo/<codigo>')
def api_produto_por_codigo(codigo):
    """API para obter produto por cÃ³digo de barras"""
    produto = Produto.query.filter_by(codigo=codigo.upper()).first()
    
    if not produto:
        return jsonify({'erro': 'Produto nÃ£o encontrado'}), 404
    
    return jsonify({
        'id': produto.id,
        'codigo': produto.codigo,
        'nome': produto.nome,
        'descricao': produto.descricao,
        'categoria': produto.categoria.nome,
        'preco_custo': produto.preco_custo,
        'preco_venda': produto.preco_venda,
        'quantidade_estoque': produto.quantidade_estoque,
        'quantidade_minima': produto.quantidade_minima,
        'ativo': produto.ativo,
        'em_falta': produto.em_falta,
        'lucro_unitario': produto.lucro_unitario,
        'margem_lucro': produto.margem_lucro
    })

@app.route('/api/sistema/info')
def api_sistema_info():
    """API para obter informaÃ§Ãµes do SystemLR"""
    return jsonify({
        'nome': APP_NAME,
        'versao': APP_VERSION,
        'dominio': APP_DOMAIN,
        'desenvolvido_por': 'SystemLR',
        'ano': datetime.now().year,
        'banco_de_dados': 'SQLite',
        'framework': 'Flask'
    })

# ============ CONTEXT PROCESSORS ============

@app.context_processor
def inject_user():
    """Injeta dados globais nos templates"""
    return {
        'ano_atual': datetime.utcnow().year,
        'total_alertas': Produto.query.filter(
            Produto.quantidade_estoque < Produto.quantidade_minima,
            Produto.ativo == True
        ).count()
    }

# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ============ MAIN ============

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
