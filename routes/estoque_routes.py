from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash

from models import db, Categoria, Produto, Movimentacao, Fornecedor


def register_estoque_routes(app, login_required, aplicar_movimentacao_estoque):
    @app.route('/produtos')
    @login_required
    def listar_produtos():
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
        return render_template(
            'produtos/produtos.html',
            produtos=produtos,
            categorias=categorias,
            categoria_selecionada=categoria_id,
            busca=busca
        )

    @app.route('/produtos/novo', methods=['GET', 'POST'])
    @login_required
    def novo_produto():
        if request.method == 'POST':
            try:
                categoria_id = request.form.get('categoria_id', type=int)
                categoria = Categoria.query.get(categoria_id)
                if not categoria:
                    flash('Categoria invalida', 'error')
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
        produto = Produto.query.get_or_404(produto_id)
        movimentacoes = Movimentacao.query.filter_by(produto_id=produto_id).order_by(
            Movimentacao.criado_em.desc()
        ).all()
        return render_template('produtos/visualizar_produto.html', produto=produto, movimentacoes=movimentacoes)

    @app.route('/produtos/<int:produto_id>/deletar', methods=['POST'])
    @login_required
    def deletar_produto(produto_id):
        produto = Produto.query.get_or_404(produto_id)
        try:
            db.session.delete(produto)
            db.session.commit()
            flash(f'Produto "{produto.nome}" deletado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao deletar produto: {str(e)}', 'error')
        return redirect(url_for('listar_produtos'))

    @app.route('/categorias')
    @login_required
    def listar_categorias():
        categorias = Categoria.query.all()
        return render_template('categorias/categorias.html', categorias=categorias)

    @app.route('/categorias/nova', methods=['GET', 'POST'])
    @login_required
    def nova_categoria():
        if request.method == 'POST':
            try:
                categoria = Categoria(nome=request.form.get('nome'), descricao=request.form.get('descricao'))
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
        categoria = Categoria.query.get_or_404(categoria_id)
        try:
            db.session.delete(categoria)
            db.session.commit()
            flash(f'Categoria "{categoria.nome}" deletada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao deletar categoria: {str(e)}', 'error')
        return redirect(url_for('listar_categorias'))

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
                flash('Movimentacao registrada com sucesso!', 'success')
                return redirect(url_for('listar_movimentacoes'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao registrar movimentacao: {str(e)}', 'error')

        fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome.asc()).all()
        return render_template('movimentacoes/movimentacao_rapida.html', produto=produto, fornecedores=fornecedores)

    @app.route('/movimentacoes')
    @login_required
    def listar_movimentacoes():
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
        return render_template(
            'movimentacoes/movimentacoes.html',
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
        if request.method == 'POST':
            try:
                produto_id = int(request.form.get('produto_id'))
                tipo = request.form.get('tipo')
                quantidade = int(request.form.get('quantidade'))
                fornecedor_id = request.form.get('fornecedor_id', type=int)

                produto = Produto.query.get(produto_id)
                if not produto:
                    flash('Produto nao encontrado', 'error')
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
                flash('Movimentacao registrada com sucesso!', 'success')
                return redirect(url_for('listar_movimentacoes'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao registrar movimentacao: {str(e)}', 'error')

        produtos = Produto.query.filter_by(ativo=True).all()
        fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome.asc()).all()
        return render_template('movimentacoes/nova_movimentacao.html', produtos=produtos, fornecedores=fornecedores)

    @app.route('/relatorios')
    @login_required
    def relatorios():
        total_produtos = Produto.query.count()
        produtos_ativos = Produto.query.filter_by(ativo=True).count()
        produtos_inativos = Produto.query.filter_by(ativo=False).count()

        produtos_em_falta = Produto.query.filter(
            Produto.quantidade_estoque < Produto.quantidade_minima,
            Produto.ativo == True
        ).all()

        valor_total = db.session.query(
            db.func.sum(Produto.quantidade_estoque * Produto.preco_custo)
        ).scalar() or 0

        produtos_maior_valor = db.session.query(
            Produto,
            (Produto.quantidade_estoque * Produto.preco_custo).label('valor_total')
        ).order_by(db.desc('valor_total')).limit(10).all()

        data_limite = datetime.utcnow() - timedelta(days=30)
        movimentacoes_mes = Movimentacao.query.filter(Movimentacao.criado_em >= data_limite).count()

        return render_template(
            'relatorios/relatorios.html',
            total_produtos=total_produtos,
            produtos_ativos=produtos_ativos,
            produtos_inativos=produtos_inativos,
            produtos_em_falta=produtos_em_falta,
            valor_total_estoque=f'{valor_total:.2f}',
            produtos_maior_valor=produtos_maior_valor,
            movimentacoes_mes=movimentacoes_mes
        )
