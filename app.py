from flask import Flask, render_template, request, redirect, url_for, flash
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
    """Página inicial"""
    return redirect(url_for('boas_vindas'))


@app.route('/dashboard')
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
    return render_template('categorias/categorias.html', categorias=categorias)

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
    
    return render_template('categorias/nova_categoria.html')

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
    
    return render_template('categorias/editar_categoria.html', categoria=categoria)

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

@app.route('/movimentacoes/rapido/<int:produto_id>', methods=['GET', 'POST'])
def movimentacao_rapida(produto_id):
    """Movimentação rápida por produto"""
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
            return redirect(url_for('listar_movimentacoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar movimentação: {str(e)}', 'error')
    
    return render_template('movimentacoes/movimentacao_rapida.html', produto=produto)

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
    
    return render_template('movimentacoes/movimentacoes.html',
        movimentacoes=movimentacoes,
        produtos=produtos,
        produto_selecionado=produto_id,
        tipo_selecionado=tipo
    )

@app.route('/movimentacoes/nova', methods=['GET', 'POST'])
def nova_movimentacao():
    """Registrar nova movimentação"""
    if request.method == 'POST':
        try:
            produto_id = int(request.form.get('produto_id'))
            tipo = request.form.get('tipo')
            quantidade = int(request.form.get('quantidade'))
            
            produto = Produto.query.get(produto_id)
            if not produto:
                flash('Produto não encontrado', 'error')
                return redirect(url_for('nova_movimentacao'))

            erro = aplicar_movimentacao_estoque(produto, tipo, quantidade)
            if erro:
                flash(erro, 'error')
                return redirect(url_for('nova_movimentacao'))
            
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
            return redirect(url_for('listar_movimentacoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar movimentação: {str(e)}', 'error')
    
    produtos = Produto.query.filter_by(ativo=True).all()
    return render_template('movimentacoes/nova_movimentacao.html', produtos=produtos)

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
def listar_caixas():
    caixas = Caixa.query.all()
    return render_template('caixas/caixas.html', caixas=caixas)

@app.route('/caixas/nova', methods=['GET', 'POST'])
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
def listar_mesas():
    mesas = Mesa.query.all()
    return render_template('mesas/mesas.html', mesas=mesas)

@app.route('/mesas/nova', methods=['GET', 'POST'])
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
def listar_pedidos():
    pedidos = Pedido.query.all()
    return render_template('pedidos/pedidos.html', pedidos=pedidos)

@app.route('/pedidos/novo', methods=['GET', 'POST'])
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
def listar_vendas():
    vendas = Pedido.query.filter_by(status='fechado').all()
    return render_template('vendas/vendas.html', vendas=vendas)


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
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ============ MAIN ============

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
