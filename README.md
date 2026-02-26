# SystemLR - Gestão de Estoque

Um sistema web completo de gerenciamento de estoque para conveniências, desenvolvido com Flask e otimizado para funcionar em PC e dispositivos móveis.

**Website**: [systemlr.com](https://systemlr.com)

## 🎯 Funcionalidades

- ✅ **Dashboard** - Visualize estatísticas e alertas em tempo real
- 📦 **Gerenciamento de Produtos** - Cadastre, edite, visualize e delete produtos
- 🏷️ **Categorias** - Organize produtos por categorias
- 📊 **Movimentações** - Registre entradas e saídas de estoque
- 📈 **Relatórios** - Gere relatórios completos do estoque
- 📱 **Responsivo** - Interface adaptável para mobile e desktop
- 🔔 **Alertas** - Notificações de produtos em falta
- 💰 **Análise Financeira** - Cálculo de lucro e margem de lucro
- 💳 **Sistema de Vendas** - pedidos, mesas e caixas diretamente pela interface web

## 🛠️ Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## 📦 Instalação

### 1. Clonar ou extrair o projeto

```bash
cd c:\Users\lucas\OneDrive\Desktop\conveniencia
```

### 2. Criar ambiente virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

## 🚀 Como Usar

### 📁 Auto‑commit (opcional)
Se desejar que todas as alterações sejam registradas automaticamente no Git, há um pequeno script
`autocommit.ps1` na raiz. Abra o PowerShell na pasta do projeto e execute:

```powershell
.\.\autocommit.ps1
```

O script observa o diretório e faz `git add -A && git commit` com uma mensagem de timestamp cada
vez que um arquivo é modificado/criado/excluído. Pressione Enter para parar o watcher.



### 1. Executar a aplicação

```bash
python app.py
```

### 2. Acessar no navegador

- **Desktop**: http://localhost:5000
- **Mobile**: Acesse via IP da máquina (http://seu-ip:5000)

### 3. Primeiro acesso

- O banco de dados SQLite será criado automaticamente
- **Primeira vez**: Você será direcionado para criar a conta do administrador
- Comece criando categorias de produtos
- Cadastre seus produtos
- Registre movimentações de estoque
- Configure caixas e mesas para iniciar vendas
- Abra pedidos e acompanhe vendas
- Acompanhe relatórios e alertas

### 🔐 Autenticação e Controle de Acesso

O SystemLR agora oferece um sistema completo de autenticação com controle de acesso por função (role-based).

#### Roles Disponíveis:
- **🔴 Admin** - Acesso total ao sistema, gerenciamento de funcionários
- **🟠 Gerente** - Acesso a vendas, pedidos, relatórios e gerenciamento de operadores/caixas
- **🟡 Caixa** - Acesso a vendas, pedidos e movimentação de estoque
- **🟢 Operador** - Acesso limitado a movimentação de estoque e leitura de relatórios

#### Login/Registro:
1. **Primeira vez**: Crie a conta do administrador em `/registro`
2. **Novos funcionários**: Admin cria conta em `Funcionários → Novo Funcionário`
3. **Login**: Acesse `/login` com email e senha

#### Proteger Rotas:
Todas as rotas do sistema (exceto login/registro) requerem autenticação. Tente acessar qualquer página sem logar e será redirecionado para o login.

## 📁 Estrutura do Projeto

```
conveniencia/
├── app.py                 # Aplicação principal Flask
├── config.py              # Configurações
├── models.py              # Modelos de dados (SQLAlchemy)
├── requirements.txt       # Dependências do projeto
├── templates/             # Arquivos HTML
│   ├── base.html          # Template base
│   ├── sistema/           # Autenticação e sistema
│   │   ├── boas_vindas.html
│   │   ├── login.html     # Login
│   │   └── registro.html  # Registro de novo usuário
│   ├── funcionarios/      # Gerenciamento de funcionários (admin/gerente)
│   │   ├── listar.html
│   │   ├── criar.html
│   │   └── editar.html
│   ├── dashboard/         # Dashboard principal
│   │   └── index.html
│   ├── produtos/          # CRUD de produtos
│   │   ├── produtos.html
│   │   ├── novo_produto.html
│   │   ├── editar_produto.html
│   │   └── visualizar_produto.html
│   ├── categorias/        # CRUD de categorias
│   │   ├── categorias.html
│   │   ├── nova_categoria.html
│   │   └── editar_categoria.html
│   ├── movimentacoes/     # Histórico e registro de movimentações
│   │   ├── movimentacoes.html
│   │   ├── nova_movimentacao.html
│   │   └── movimentacao_rapida.html
│   ├── relatorios/        # Relatórios
│   │   └── relatorios.html
│   ├── caixas/            # CRUD de caixas
│   │   ├── caixas.html
│   │   ├── nova_caixa.html
│   │   └── editar_caixa.html
│   ├── mesas/             # CRUD de mesas
│   │   ├── mesas.html
│   │   ├── nova_mesa.html
│   │   └── editar_mesa.html
│   ├── pedidos/           # Pedidos (comandas)
│   │   ├── pedidos.html
│   │   ├── novo_pedido.html
│   │   └── editar_pedido.html
│   ├── vendas/            # Lista de vendas
│   │   └── vendas.html
│   ├── fornecedores/      # CRUD de fornecedores
│   │   ├── fornecedores.html
│   │   ├── novo_fornecedor.html
│   │   └── editar_fornecedor.html
│   ├── errors/            # Páginas de erro
│   │   ├── 404.html
│   │   └── 500.html
├── static/                # Arquivos estáticos
│   ├── css/
│   │   └── style.css      # Estilos responsivos
│   ├── js/
│   │   ├── main.js        # JavaScript e menus
│   │   └── quagga.min.js  # Leitura de código de barras
│   └── img/               # Imagens
└── estoque.db             # Banco de dados (criado automaticamente)
```

## 💾 Banco de Dados

O projeto usa **SQLite** com as seguintes tabelas:

### 1. **categorias**
- id (PK)
- nome (único)
- descricao
- criado_em

### 2. **produtos**
- id (PK)
- codigo (único)
- nome
- descricao
- categoria_id (FK)
- preco_custo
- preco_venda
- quantidade_estoque
- quantidade_minima
- ativo
- criado_em
- atualizado_em

### 3. **movimentacoes**
- id (PK)
- produto_id (FK)
- tipo (entrada/saida)
- quantidade
- motivo
- observacoes
- criado_em

### 4. **funcionarios** (Novo)
- id (PK)
- nome
- email (único)
- senha_hash (bcrypt)
- role (admin/gerente/caixa/operador)
- ativo
- criado_em
- atualizado_em

## 🎨 Design Responsivo

O sistema é totalmente responsivo com breakpoints para:

- **Desktop** (1200px+) - Visualização completa com múltiplas colunas
- **Tablet** (768px - 1199px) - Adaptação de grid e navegação
- **Mobile** (até 767px) - Layout vertical otimizado para toque

### Recursos Mobile:
- Menu hamburger colapsável
- Tabelas em modo de cards no mobile
- Botões grandes e fáceis de tocar
- Navegação intuitiva
- Otimização de performance

## 📊 Principais Funcionalidades

### Dashboard
- Total de produtos cadastrados
- Quantidade de produtos em falta
- Valor total de estoque
- Últimas movimentações registradas

### Produtos
- Busca e filtro por categoria
- Visualização de estoque e status
- Cálculo automático de lucro e margem
- Alertas de produtos em falta

### Movimentações
- Registro de entradas e saídas
- Filtro por produto e tipo
- Histórico completo com timestamps
- Atualização automática de estoque

### Relatórios
- Produtos em falta
- Produtos com maior valor em estoque
- Estatísticas gerais
- Movimentações do mês

## 🔒 Segurança

- ✅ **Autenticação**: Sistema de login com email e senha (bcrypt hashing)
- ✅ **Controle de Acesso**: Role-based access control (RBAC) com 4 níveis
- ✅ **Proteção de Rotas**: Todas as rotas protegidas com @login_required
- ✅ **Sessão Segura**: Cookies de sessão com SameSite=Lax
- ✅ **Senhas Criptografadas**: Uso de werkzeug.security para hash bcrypt
- ⚠️ **Produção**: Configure SECRET_KEY com um valor aleatório forte em produção
- ⚠️ **HTTPS**: Use HTTPS em produção
- ⚠️ **Variáveis de Ambiente**: Nunca commite credenciais no repositório

## 🚦 Fazendo Builds e Deploy

### Para Produção

1. Mude a configuração de debug:
   ```python
   app.run(debug=False)
   ```

2. Configure um servidor WSGI (Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. Use um proxy reverso (Nginx) para melhor performance

## 📝 Exemplos de Uso

### Criar primeira categoria
1. Acesse "Categorias"
2. Clique em "➕ Nova Categoria"
3. Preencha o nome (ex: "Bebidas")
4. Clique em "✓ Salvar Categoria"

### Adicionar produto
1. Vá para "Produtos"
2. Clique em "➕ Novo Produto"
3. Preencha os dados:
   - Código: PROD001
   - Nome: Refrigerante 2L
   - Categoria: Bebidas
   - Preço de Custo: 3.50
   - Preço de Venda: 5.50
4. Clique em "✓ Salvar Produto"

### Registrar movimentação
1. Acesse "Movimentações"
2. Clique em "➕ Nova Movimentação"
3. Selecione o produto
4. Escolha o tipo (Entrada/Saída)
5. Informe quantidade e motivo
6. Clique em "✓ Registrar Movimentação"

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'flask'"
→ Certifique-se de instalar as dependências: `pip install -r requirements.txt`

### "Erro ao conectar ao banco de dados"
→ Delete o arquivo `estoque.db` e execute novamente. O banco será recriado.

### Aplicação não acessível via mobile
→ Certifique-se de usar o IP correto: `ipconfig` (Windows) ou `ifconfig` (Linux)

## 📞 Suporte e Contribuições

Para melhorias e sugestões, considere adicionar:
- Sistema de backup automático
- Exportação de relatórios em PDF/Excel
- Autenticação de usuários
- Múltiplas validações de entrada
- Notificações por email
- Integração com sistemas de pagamento

## 📄 Licença

Este projeto é fornecido como está para uso educacional e comercial.

## 🌐 Sobre SystemLR

**SystemLR** é uma marca registrada dedicada a fornecer soluções de gestão de estoque simples, intuitivas e poderosas para pequenos e médios negócios.

- 🌟 Website: [systemlr.com](https://systemlr.com)
- 📧 Suporte disponível em tempo real
- 🚀 Sempre inovando para melhor atender seus clientes

---

**Desenvolvido com ❤️ em Flask | SystemLR - Sua Gestão Simplificada**
