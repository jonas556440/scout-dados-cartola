# 🖥️ Serviços Cartola FC 2026

## ✅ Serviços Ativos (Systemd)

### Backend API (Porta 8000)
```bash
# Ver status
sudo systemctl status cartolafc-backend.service

# Iniciar
sudo systemctl start cartolafc-backend.service

# Parar
sudo systemctl stop cartolafc-backend.service

# Reiniciar
sudo systemctl restart cartolafc-backend.service

# Ver logs
sudo journalctl -u cartolafc-backend.service -f
```

**Configuração:** `/etc/systemd/system/cartolafc-backend.service`
**Comando:** `uvicorn api_server:app --host 0.0.0.0 --port 8000`  
**WorkingDirectory:** `/root/cartolafc2026`

---

### Scheduler Service (Background)
Serviço responsável por atualizações automáticas, fechamento de mercado e cálculo de scouts.

```bash
# Ver status
sudo systemctl status cartolafc-scheduler.service

# Iniciar
sudo systemctl start cartolafc-scheduler.service

# Parar
sudo systemctl stop cartolafc-scheduler.service

# Reiniciar
sudo systemctl restart cartolafc-scheduler.service

# Ver logs
sudo journalctl -u cartolafc-scheduler.service -f
# Ou logs diretos:
tail -f /root/cartolafc2026/scheduler.log
```

**Configuração:** `/etc/systemd/system/cartolafc-scheduler.service`
**Comando:** `python3 scheduler_service.py`

---

### Frontend React (Estáticos via OpenLiteSpeed)

**Em produção, não há serviço frontend separado.** O OpenLiteSpeed serve os arquivos estáticos do diretório `frontend/dist/`.

```bash
# Build do frontend (gera dist/)
cd /www/wwwroot/scoutdados.com.br/frontend && bun run build

# Reiniciar OpenLiteSpeed para servir novos arquivos
/usr/local/lsws/bin/lswsctrl restart
```

**Para desenvolvimento local:**
```bash
cd /www/wwwroot/scoutdados.com.br/frontend
bun run dev  # Porta 5176 com hot reload
```

**Configuração:** OpenLiteSpeed virtual host aponta para `frontend/dist/`  
**Produção:** Arquivos estáticos (HTML/CSS/JS) sem processo Node  
**Dev:** Vite dev server com HMR


## 🔍 Verificação Rápida

### Ambos os serviços
```bash
sudo systemctl status cartolafc-backend.service cartolafc-scheduler.service
```

### Testar endpoints
```bash
# Backend
curl http://localhost:8000/api/status

# Frontend (produção via OpenLiteSpeed na porta 443/80)
curl https://scoutdados.com.br

# Frontend (dev, se rodando)
curl http://localhost:5176
```

### Verificar portas
```bash
# Ver processos nas portas
sudo lsof -i :8000  # Backend FastAPI
sudo lsof -i :80    # OpenLiteSpeed HTTP
sudo lsof -i :443   # OpenLiteSpeed HTTPS
sudo lsof -i :5176  # Vite dev (só se rodando localmente)

# Ou
sudo netstat -tlnp | grep -E "8000|5176"
```

---

## 🔄 Reiniciar Tudo

```bash
# Reiniciar ambos
sudo systemctl restart cartolafc-backend.service cartolafc-frontend.service

# Ver status
sudo systemctl status cartolafc-backend.service cartolafc-frontend.service
```

---

## 📊 Logs em Tempo Real

```bash
# Backend e Frontend juntos
sudo journalctl -u cartolafc-backend.service -u cartolafc-frontend.service -f

# Últimas 100 linhas
sudo journalctl -u cartolafc-backend.service -n 100
```

---

## 🚀 Inicialização Automática

Ambos os serviços estão configurados para iniciar automaticamente no boot:

```bash
# Ver se estão habilitados
sudo systemctl is-enabled cartolafc-backend.service
sudo systemctl is-enabled cartolafc-frontend.service

# Habilitar (já está habilitado)
sudo systemctl enable cartolafc-backend.service
sudo systemctl enable cartolafc-frontend.service

# Desabilitar inicialização automática
sudo systemctl disable cartolafc-backend.service
sudo systemctl disable cartolafc-frontend.service
```

---

## ⚙️ Configurações dos Serviços

### Backend
```ini
[Unit]
Description=Cartola FC 2026 - Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cartolafc2026
ExecStart=/usr/bin/python3 /usr/local/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### Frontend
```ini
[Unit]
Description=Cartola FC 2026 - Frontend React
After=network.target cartolafc-backend.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/cartolafc2026/frontend
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npx vite --host 0.0.0.0 --port 5176 --strictPort
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

---

## 🛠️ Troubleshooting

### Serviço não inicia
```bash
# Ver erro detalhado
sudo journalctl -u cartolafc-backend.service -xe

# Recarregar configurações systemd
sudo systemctl daemon-reload

# Tentar iniciar novamente
sudo systemctl start cartolafc-backend.service
```

### Porta ocupada
```bash
# Ver processo na porta
sudo lsof -i :8000

# Matar processo específico
sudo kill -9 <PID>

# Reiniciar serviço
sudo systemctl restart cartolafc-backend.service
```

### Alterar configuração
```bash
# Editar serviço
sudo nano /etc/systemd/system/cartolafc-backend.service

# Recarregar
sudo systemctl daemon-reload

# Reiniciar
sudo systemctl restart cartolafc-backend.service
```

---

## ❌ Scripts Manuais (REMOVIDOS)

Os seguintes scripts foram **REMOVIDOS** pois são obsoletos:
- ~~`start_server.sh`~~ - Use systemd ao invés
- ~~`monitor.sh`~~ - systemd já faz restart automático

**Motivo:** Systemd é mais confiável, inicia no boot e gerencia logs automaticamente.

---

## 📝 Acesso

- **Backend API:** http://localhost:8000
- **Frontend:** http://localhost:5176
- **Docs API:** http://localhost:8000/docs

---

**Última atualização:** 30/01/2026 18:30
