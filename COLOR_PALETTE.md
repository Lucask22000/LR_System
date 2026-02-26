# 🎨 Paleta de Cores - SystemLR

## Padrão de Cores Moderno e Consistente

Todo o projeto SystemLR agora utiliza uma paleta de cores padronizada e moderna baseada em roxo/lavanda como cor primária.

### Cores Principais

| Cor | Hex | Uso | Exemplo |
|-----|-----|-----|---------|
| **Primária** | `#667eea` | Botões, links, navbar, destaque | Botões principais, hover nav |
| **Primária Escura** | `#5568d3` | Hover de botões primários | Efeito hover em CTAs |
| **Secundária** | `#764ba2` | Acentos, alternativas | Menu secundário, tags |
| **Sucesso** | `#28a745` | Ações positivas, confirmações | Botão "Salvar", alertas de sucesso |
| **Perigo** | `#dc3545` | Erros, exclusões, alertas | Botão "Deletar", alertas de erro |
| **Aviso** | `#ffc107` | Avisos, atenções | Alertas de aviso, badges |
| **Informação** | `#17a2b8` | Informações gerais | Alertas informativos |

### Cores Neutras (Cinzas)

| Cor | Hex | Uso |
|-----|-----|-----|
| **Escuro** | `#343a40` | Texto principal, headings |
| **Médio** | `#6c757d` | Texto secundário, placeholders |
| **Claro** | `#f8f9fa` | Fundos, cartas, containers |
| **Borda** | `#dee2e6` | Linhas, divisores, bordas |

## Implementação

### CSS (static/css/style.css)

As cores estão definidas como variáveis CSS no `:root`:

```css
:root {
    --primary: #667eea;
    --primary-dark: #5568d3;
    --secondary: #764ba2;
    --success: #28a745;
    --danger: #dc3545;
    --warning: #ffc107;
    --info: #17a2b8;
    --light: #f8f9fa;
    --dark: #343a40;
    --border: #dee2e6;
    --shadow: 0 2px 4px rgba(0,0,0,0.1);
}
```

### Classes de Utilidade

O CSS fornece classes prontas para usar:

```html
<!-- Botões -->
<button class="btn btn-primary">Salvar</button>
<button class="btn btn-success">Confirmar</button>
<button class="btn btn-danger">Deletar</button>
<button class="btn btn-warning">Atenção</button>
<button class="btn btn-info">Informação</button>

<!-- Alertas -->
<div class="alert alert-success">Sucesso!</div>
<div class="alert alert-danger">Erro!</div>
<div class="alert alert-warning">Aviso!</div>
<div class="alert alert-info">Informação</div>
```

### Usando Variáveis CSS

Para novos estilos, use as variáveis CSS:

```css
.meu-elemento {
    background-color: var(--primary);
    color: white;
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
}

.meu-elemento:hover {
    background-color: var(--primary-dark);
}
```

### Inline Styles (Quando Necessário)

Se precisar de cores inline em templates HTML, use apenas a paleta:

```html
<!-- ✅ Correto -->
<div style="color: #667eea;">Roxo primário</div>
<div style="background-color: #28a745;">Verde de sucesso</div>
<div style="border-color: #dee2e6;">Borda padrão</div>

<!-- ❌ Evitar -->
<div style="color: #999;">Número aleatório</div>
<div style="background-color: #f5f9f1;">Cor não padronizada</div>
```

## Guia de Uso por Contexto

### Navbar e Cabeçalhos
- Fundo: `--primary` (#667eea)
- Texto: branco
- Hover: `--primary-dark` (#5568d3)

### Formulários
- Label: `--dark` (#343a40)
- Border: `--border` (#dee2e6)
- Focus: `--primary` (#667eea)
- Background: branco

### Tabelas
- Header Background: `--light` (#f8f9fa)
- Header Text: `--dark` (#343a40)
- Border: `--border` (#dee2e6)
- Row Hover: `--light` (#f8f9fa)

### Status de Funcionários
- Admin: `--danger` (#dc3545) - Vermelho
- Gerente: `--warning` (#ffc107) - Amarelo
- Caixa: `--info` (#17a2b8) - Azul
- Operador: `--secondary` (#6c757d) - Cinza

### Alertas/Notificações
- Sucesso: `--success` (#28a745)
- Erro: `--danger` (#dc3545)
- Aviso: `--warning` (#ffc107)
- Info: `--info` (#17a2b8)
- Fundo: `--light` (#f8f9fa)

## Acessibilidade

A paleta foi escolhida com consideração para:
- ✅ Contraste suficiente (WCAG AA)
- ✅ Diferenciação por cor + padrão
- ✅ Amigável para daltônicos (cores neutras adicionais)

## Adicionando Novos Componentes

Ao criar novos componentes, SEMPRE use as variáveis CSS:

### ❌ Antes (Ruim)
```html
<div style="background-color: #4CAF50; color: white;">
    Novo componente
</div>
```

### ✅ Depois (Correto)
```html
<div style="background-color: var(--success); color: white;">
    Novo componente
</div>
```

Ou na classe CSS:
```css
.novo-componente {
    background-color: var(--success);
    color: white;
}
```

## Referência Rápida

```
Primária:      #667eea (roxo)
Dark Primária: #5568d3 (roxo escuro)
Secundária:    #764ba2 (roxo mais escuro)
Sucesso:       #28a745 (verde)
Perigo:        #dc3545 (vermelho)
Aviso:         #ffc107 (amarelo)
Info:          #17a2b8 (azul)
Escuro:        #343a40 (cinza escuro)
Médio:         #6c757d (cinza médio)
Claro:         #f8f9fa (cinza claro)
Borda:         #dee2e6 (cinza borda)
```

---

**Última Atualização**: 26 de fevereiro de 2026
**Versão**: 1.0.0 - Paleta Padrão Moderna SystemLR
