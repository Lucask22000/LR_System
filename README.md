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

### 1. Executar a aplicação

```bash
python app.py
```

### 2. Acessar no navegador

- **Desktop**: http://localhost:5000
- **Mobile**: Acesse via IP da máquina (http://seu-ip:5000)

### 3. Primeiro acesso

- O banco de dados SQLite será criado automaticamente
- Comece criando categorias de produtos
- Cadastre seus produtos
- Registre movimentações de estoque
- Acompanhe relatórios e alertas

## 📁 Estrutura do Projeto

```
conveniencia/
├── app.py                 # Aplicação principal Flask
├── config.py              # Configurações
├── models.py              # Modelos de dados (SQLAlchemy)
├── requirements.txt       # Dependências do projeto
├── templates/             # Arquivos HTML
│   ├── base.html          # Template base
│   ├── index.html         # Dashboard
│   ├── produtos.html      # Lista de produtos
│   ├── novo_produto.html  # Formulário novo produto
│   ├── editar_produto.html    # Formulário editar
│   ├── visualizar_produto.html # Detalhes do produto
│   ├── categorias.html    # Gerenciamento de categorias
│   ├── movimentacoes.html # Histórico de movimentações
│   ├── relatorios.html    # Relatórios
│   ├── 404.html           # Página de erro 404
│   └── 500.html           # Página de erro 500
├── static/                # Arquivos estáticos
│   ├── css/
│   │   └── style.css      # Estilos responsivos
│   └── js/
│       └── main.js        # JavaScript
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

- As senhas não são implementadas na versão inicial
- Para produção, adicione autenticação e validação de segurança
- Use variáveis de ambiente para dados sensíveis
- Configure SECRET_KEY em produção

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
