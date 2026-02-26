from datetime import datetime
from flask import render_template, request, redirect, url_for, flash

from models import db, Caixa, Mesa, Pedido, Produto, ItemPedido, Movimentacao


def register_vendas_routes(app, login_required):
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
                for i in range(int(request.form.get('item_count', 0))):
                    pid = request.form.get(f'produto_{i}')
                    qty = int(request.form.get(f'quantidade_{i}', 1))
                    if not pid:
                        continue
                    prod = Produto.query.get(pid)
                    if not prod:
                        continue
                    ip = ItemPedido(
                        pedido_id=pedido.id,
                        produto_id=prod.id,
                        quantidade=qty,
                        preco_unitario=prod.preco_venda
                    )
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

                pedido.itens.clear()
                total = 0
                for i in range(int(request.form.get('item_count', 0))):
                    pid = request.form.get(f'produto_{i}')
                    qty = int(request.form.get(f'quantidade_{i}', 1))
                    if not pid:
                        continue
                    prod = Produto.query.get(pid)
                    if not prod:
                        continue
                    ip = ItemPedido(
                        pedido_id=pedido.id,
                        produto_id=prod.id,
                        quantidade=qty,
                        preco_unitario=prod.preco_venda
                    )
                    db.session.add(ip)
                    total += qty * prod.preco_venda
                pedido.total = total

                if pedido.status == 'fechado' and not pedido.fechado_em:
                    pedido.fechado_em = datetime.utcnow()
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
            flash('Pedido excluido.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir pedido: {str(e)}', 'error')
        return redirect(url_for('listar_pedidos'))

    @app.route('/vendas')
    @login_required
    def listar_vendas():
        vendas = Pedido.query.filter_by(status='fechado').all()
        return render_template('vendas/vendas.html', vendas=vendas)
