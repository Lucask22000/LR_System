# SystemLR - Configuração de Domínio e Branding

## 🌐 Informações de Domínio

**Domínio**: systemlr.com  
**Sistema**: SystemLR - Gestão de Estoque  
**Versão**: 1.0.0

## 🎨 Branding

### Cores Oficiais
- **Primária**: #4CAF50 (Verde)
- **Logo**: 📦 SystemLR
- **Tagline**: "Sua Gestão Simplificada"

### Typography
- **Font**: Segoe UI, Tahoma, Geneva, Verdana, sans-serif
- **Títulos**: Bold
- **Corpo**: Regular

### Design Guidelines
- Minimalista e intuitivo
- Responsivo para todas as plataformas
- Acessibilidade WCAG AA
- Suporte a múltiplos idiomas (português implementado)

## 📱 Plataformas Suportadas

- ✅ Desktop (Windows, Mac, Linux)
- ✅ Mobile (iOS, Android)
- ✅ Tablet
- ✅ Responsivo em qualquer resolução

## 🚀 Deployment para systemlr.com

### Pré-requisitos
- Nginx ou Apache como proxy reverso
- SSL Certificate (HTTPS)
- Python 3.8+ server
- PostgreSQL (para produção)

### Passos para Deploy

1. **Configurar servidor**
   ```bash
   sudo apt-get update
   sudo apt-get install nginx python3-pip postgresql
   ```

2. **Clonar projeto**
   ```bash
   git clone https://github.com/seu-repo/systemlr.git /var/www/systemlr
   ```

3. **Instalar dependências**
   ```bash
   cd /var/www/systemlr
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configurar Gunicorn**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 127.0.0.1:8000 app:app
   ```

5. **Configurar Nginx**
   ```nginx
   server {
       listen 80;
       server_name systemlr.com www.systemlr.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

6. **Configurar SSL com Let's Encrypt**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d systemlr.com -d www.systemlr.com
   ```

## 🗄️ Banco de Dados para Produção

Alterar no `config.py`:
```python
# De SQLite
SQLALCHEMY_DATABASE_URI = 'sqlite:///estoque.db'

# Para PostgreSQL
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/systemlr_db'
```

## 🔐 Variáveis de Ambiente

Criar arquivo `.env`:
```
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/systemlr_db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## 📊 Monitoramento

### Ferramentas Recomendadas
- Sentry (error tracking)
- Google Analytics
- Uptime Robot (status monitoring)
- New Relic (performance)

## 🎯 Roadmap

### v1.1
- [ ] Autenticação de usuários
- [ ] Múltiplas filiais
- [ ] Backup automático
- [ ] Relatórios em PDF/Excel

### v1.2
- [ ] App móvel nativa (iOS/Android)
- [ ] Integração com NFC
- [ ] API pública para integrações
- [ ] Sincronização em nuvem

### v2.0
- [ ] PDV integrado
- [ ] Gestão de fornecedores
- [ ] Sistema de filas para compras
- [ ] IA para previsão de demanda

## 📞 Suporte

- Email: support@systemlr.com
- Website: systemlr.com
- GitHub Issues: [Repo Issues]
- WhatsApp: [Número]

## 📜 Licença

© 2026 SystemLR. Todos os direitos reservados.

---

**SystemLR - Gestão Simplificada para seu Negócio**
