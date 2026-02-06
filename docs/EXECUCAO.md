# 🚀 Guia de Execução - Cartola FC 2026

## ✅ Método Recomendado: Systemd

O backend já está configurado para rodar como serviço do sistema via **systemd**, garantindo:
- ✅ Restart automático em caso de falha
- ✅ Início automático no boot do servidor
- ✅ Logs centralizados
- ✅ Gerenciamento simplificado

### 📋 Comandos Principais

```bash
# Iniciar o serviço
sudo systemctl start cartolafc-backend.service

# Parar o serviço
sudo systemctl stop cartolafc-backend.service

# Reiniciar o serviço
sudo systemctl restart cartolafc-backend.service

# Ver status
sudo systemctl status cartolafc-backend.service

# Habilitar início automático no boot
sudo systemctl enable cartolafc-backend.service

# Desabilitar início automático
sudo systemctl disable cartolafc-backend.service
```

### 📊 Ver Logs

```bash
# Logs em tempo real
sudo journalctl -u cartolafc-backend.service -f

# Últimas 100 linhas
sudo journalctl -u cartolafc-backend.service -n 100

# Logs desde hoje
sudo journalctl -u cartolafc-backend.service --since today

# Filtrar por erros
sudo journalctl -u cartolafc-backend.service -p err
```

### ⚙️ Configuração do Serviço

Arquivo: `/etc/systemd/system/cartolafc-backend.service`

```ini
[Unit]
Description=Cartola FC 2026 - Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cartolafc2026
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/local/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 🔧 Modificar Configuração

Se precisar alterar a configuração (porta, host, etc):

```bash
# 1. Editar o arquivo de serviço
sudo nano /etc/systemd/system/cartolafc-backend.service

# 2. Recarregar configurações do systemd
sudo systemctl daemon-reload

# 3. Reiniciar o serviço
sudo systemctl restart cartolafc-backend.service
```

---

## 🔍 Monitoramento

### Healthcheck Manual

```bash
# Verificar se a API está respondendo
python3 healthcheck.py

# Ou via curl
curl http://localhost:8000/
curl http://localhost:8000/api/status
```

### Monitor Automático (Opcional)

Para monitoramento ativo com restart automático:

```bash
# Executar monitor em background
nohup ./monitor.sh > /dev/null 2>&1 &

# Ver logs do monitor
tail -f logs/monitor.log
```

---

## 🐛 Troubleshooting

### Serviço não inicia

```bash
# 1. Ver logs de erro
sudo journalctl -u cartolafc-backend.service -n 50

# 2. Testar manualmente
cd /root/cartolafc2026
python3 api_server.py

# 3. Verificar se porta 8000 está em uso
sudo lsof -i :8000

# 4. Matar processos conflitantes
sudo lsof -ti:8000 | xargs sudo kill -9
```

### Logs não aparecem

```bash
# Ver status detalhado
sudo systemctl status cartolafc-backend.service -l --no-pager

# Verificar permissões
ls -la /root/cartolafc2026/

# Testar execução manual
sudo -u root /usr/local/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### Mudanças no código não aplicam

```bash
# 1. Verificar sintaxe
cd /root/cartolafc2026
python3 -m py_compile api_server.py

# 2. Reiniciar serviço
sudo systemctl restart cartolafc-backend.service

# 3. Confirmar restart
sudo systemctl status cartolafc-backend.service
```

---

## 📦 Frontend

O frontend React também roda via systemd:

```bash
# Status do frontend
sudo systemctl status cartolafc-frontend.service

# Reiniciar frontend
sudo systemctl restart cartolafc-frontend.service

# Logs do frontend
sudo journalctl -u cartolafc-frontend.service -f
```

---

## ⚠️ Scripts Deprecados

Os seguintes scripts foram mantidos apenas para referência, mas **NÃO são recomendados** para uso em produção:

- ~~`start_server.sh`~~ - Usar `systemctl start` ao invés
- ~~`monitor.sh`~~ - Systemd já tem restart automático
- ✅ `healthcheck.py` - **Mantido** (útil para monitoramento externo)

**Por quê usar systemd?**
- ✅ Mais confiável (testado em produção há anos)
- ✅ Integração com logs do sistema
- ✅ Restart mais inteligente (backoff exponencial)
- ✅ Gerenciamento de recursos (CPU, memória)
- ✅ Padrão Linux - funciona em qualquer distro

---

## 🎯 Checklist de Deploy

Ao fazer deploy ou atualização:

- [ ] Parar serviço: `sudo systemctl stop cartolafc-backend.service`
- [ ] Atualizar código (git pull, etc)
- [ ] Testar sintaxe: `python3 -m py_compile api_server.py`
- [ ] Instalar dependências (se houver): `pip install -r requirements_api.txt`
- [ ] Reiniciar serviço: `sudo systemctl restart cartolafc-backend.service`
- [ ] Verificar status: `sudo systemctl status cartolafc-backend.service`
- [ ] Testar API: `python3 healthcheck.py`
- [ ] Ver logs: `sudo journalctl -u cartolafc-backend.service -f`

---

## 📚 Referências

- [Documentação Systemd](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Guia Systemd DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-use-systemctl-to-manage-systemd-services-and-units)
- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)
