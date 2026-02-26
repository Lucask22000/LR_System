# Configuração DNS e Hosting para systemlr.com

## 🌐 Registros DNS Recomendados

Para apontar seu domínio `systemlr.com` para o servidor:

### A Record (IPv4)
```
Nome: @
Tipo: A
Valor: [SEU_IP_DO_SERVIDOR]
TTL: 3600
```

### AAAA Record (IPv6) - Opcional
```
Nome: @
Tipo: AAAA
Valor: [SEU_IPv6_DO_SERVIDOR]
TTL: 3600
```

### WWW Record
```
Nome: www
Tipo: CNAME
Valor: systemlr.com
TTL: 3600
```

### MX Record (para Email)
```
Nome: @
Tipo: MX
Valor: mail.systemlr.com
Prioridade: 10
TTL: 3600
```

## 🔒 SSL/TLS Certificate

### Opção 1: Let's Encrypt (Gratuito)
```bash
sudo certbot certonly --standalone -d systemlr.com -d www.systemlr.com
```

### Opção 2: Namecheap / GoDaddy / etc
Compre um certificado e faça upload no servidor.

## 🔧 Nginx Configuration para systemlr.com

Criar arquivo `/etc/nginx/sites-available/systemlr.com`:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name systemlr.com www.systemlr.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server Block
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name systemlr.com www.systemlr.com;

    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/systemlr.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/systemlr.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;

    # Root directory
    root /var/www/systemlr;

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Static files
    location /static/ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
    }
}
```

### Ativar o site
```bash
sudo ln -s /etc/nginx/sites-available/systemlr.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🚀 Systemd Service para Gunicorn

Criar arquivo `/etc/systemd/system/systemlr.service`:

```ini
[Unit]
Description=SystemLR Flask Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/systemlr
Environment="PATH=/var/www/systemlr/venv/bin"
ExecStart=/var/www/systemlr/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

### Ativar o serviço
```bash
sudo systemctl daemon-reload
sudo systemctl enable systemlr
sudo systemctl start systemlr
sudo systemctl status systemlr
```

## 📊 Monitoramento

### Verificar logs
```bash
sudo journalctl -u systemlr -f
tail -f /var/log/nginx/systemlr.com.access.log
tail -f /var/log/nginx/systemlr.com.error.log
```

### Ferramentas de Monitoramento
- **UptimeRobot**: Monitorar se o site está online
- **Sentry**: Rastrear erros de aplicação
- **Loki/Prometheus**: Logs e métricas

## 🔄 Auto-renew SSL Certificate

```bash
# Testar renovação
sudo certbot renew --dry-run

# Criar cron job para renovação automática
sudo crontab -e
# Adicione: 0 3 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx
```

## 🛡️ Firewall Configuration

```bash
# Abrir portas
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## 📈 Performance Tips

1. **Cache Headers** - Já configurado no Nginx
2. **Compression** - Gzip enabled
3. **Database** - Usar PostgreSQL em produção
4. **CDN** - Considerar Cloudflare
5. **Load Balancing** - Para múltiplos servidores

## 🆘 Troubleshooting

### Site não acessível
```bash
# Verificar DNS
nslookup systemlr.com
# Verificar se Nginx está rodando
sudo systemctl status nginx
# Verificar Gunicorn
sudo systemctl status systemlr
```

### SSL não funciona
```bash
# Validar certificado
sudo certbot certificates
# Renovar certificado
sudo certbot renew --force-renewal
```

### Lentidão
```bash
# Aumentar workers do Gunicorn no systemd service
# ExecStart=/var/www/systemlr/venv/bin/gunicorn -w 8 -b 127.0.0.1:8000 app:app
```

---

**SystemLR - Sua Gestão Simplificada na Nuvem**
