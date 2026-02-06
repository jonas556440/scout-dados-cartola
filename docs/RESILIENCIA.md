# Cartola FC 2026 - Como Evitar que a Aplicação Fique Fora do Ar

## 🔴 Problemas Identificados

1. **Falta de tratamento de exceções** - API externa pode falhar e derrubar o servidor
2. **Timeouts muito longos** (30s) - Causavam demora excessiva e timeouts do navegador  
3. **Sem retry automático** - Uma falha temporária derrubava requests
4. **Sem monitoramento** - Servidor cai e ninguém sabe até alguém reclamar

## ✅ Correções Aplicadas

### 1. Tratamento de Erros Robusto (`src/api/cartola_api.py`)
- ✅ **Retry automático**: 3 tentativas com delay de 1s entre cada
- ✅ **Timeout reduzido**: De 30s para 15s (melhor UX)
- ✅ **Logging**: Logs detalhados de todas as requisições
- ✅ **Retorno None** ao invés de exception crash
- ✅ Diferenciação entre erros 4xx (não retry) e 5xx/timeout (retry)

### 2. Endpoints Protegidos (`api_server.py`)
Todos os endpoints críticos agora têm `try-except`:
- `/api/status`
- `/api/dashboard`
- `/api/mercado/atletas`
- `/api/confrontos`
- `/api/escalacao/gerar`

**Resultado**: Se a API do Cartola cair, o servidor continua respondendo com erro 503 (Service Unavailable) ao invés de crashar.

### 3. Scripts de Resiliência

#### `start_server.sh` - Gerenciador do servidor
```bash
bash start_server.sh start    # Iniciar
bash start_server.sh stop     # Parar
bash start_server.sh restart  # Reiniciar
bash start_server.sh status   # Ver status
```

#### `monitor.sh` - Monitoramento ativo
- Verifica servidor a cada 30 segundos
- Restart automático após 3 falhas consecutivas
- Logs em `logs/monitor.log`

**Uso**:
```bash
# Em background
nohup bash monitor.sh &

# Ou com screen/tmux
screen -dmS monitor bash monitor.sh
```

#### `healthcheck.py` - Checagem de saúde
```bash
python3 healthcheck.py
# Retorna exit code 0 se OK, 1 se falha
```

### 4. Systemd Service (Produção)

Para rodar como serviço do sistema com restart automático:

```bash
# 1. Copiar arquivo de serviço
sudo cp cartolafc.service /etc/systemd/system/

# 2. Recarregar systemd
sudo systemctl daemon-reload

# 3. Habilitar início automático
sudo systemctl enable cartolafc.service

# 4. Iniciar serviço
sudo systemctl start cartolafc.service

# 5. Ver status
sudo systemctl status cartolafc.service

# 6. Ver logs
sudo journalctl -u cartolafc.service -f
```

**Recursos do systemd**:
- ✅ Restart automático se crashar
- ✅ Limites de recursos (memória/CPU)
- ✅ Logs centralizados
- ✅ Inicia automaticamente no boot

## 📊 Monitoramento Recomendado

### Opção 1: Monitor Script (Simples)
```bash
# Iniciar em background
cd /root/cartolafc2026
nohup bash monitor.sh > /dev/null 2>&1 &

# Ver logs de monitoramento
tail -f logs/monitor.log
```

### Opção 2: Systemd (Produção)
```bash
sudo systemctl start cartolafc.service
sudo systemctl status cartolafc.service
```

### Opção 3: Cron + Healthcheck
Adicionar ao crontab:
```bash
# Verificar a cada 5 minutos e reiniciar se necessário
*/5 * * * * cd /root/cartolafc2026 && python3 healthcheck.py || bash start_server.sh restart
```

## 🚀 Recomendação de Uso

**Para desenvolvimento local**:
```bash
python3 api_server.py
```

**Para produção/servidor**:
```bash
# Opção 1: Systemd (melhor)
sudo systemctl start cartolafc.service

# Opção 2: Script + Monitor
bash start_server.sh start
nohup bash monitor.sh &
```

## 📝 Logs

Todos os logs ficam em `/root/cartolafc2026/logs/`:
- `api_server.log` - Logs do servidor
- `monitor.log` - Logs do monitoramento
- `api_server_error.log` - Apenas erros (systemd)

```bash
# Ver logs em tempo real
tail -f logs/api_server.log

# Ver últimos erros
tail -f logs/monitor.log | grep "❌\|🔴"
```

## 🔧 Troubleshooting

### Servidor não inicia
```bash
# Verificar se porta 8000 está em uso
lsof -i :8000

# Matar processo na porta
lsof -ti:8000 | xargs kill -9

# Tentar iniciar novamente
bash start_server.sh start
```

### API do Cartola fora
- ✅ Servidor continua rodando
- ✅ Retorna erro 503 nos endpoints
- ✅ Frontend deve mostrar mensagem de indisponibilidade
- ✅ Cache evita requests desnecessárias por 5 minutos

### Ver erros recentes
```bash
# Últimos 50 erros da API
grep "❌" logs/api_server.log | tail -50

# Falhas de conexão
grep "Conex" logs/api_server.log | tail -20
```

## 📈 Melhorias Futuras

1. **Alertas**: Integrar com Telegram/Slack/Email para notificar quando cair
2. **Métricas**: Prometheus + Grafana para visualizar uptime e performance
3. **Load Balancer**: Múltiplas instâncias com Nginx/HAProxy
4. **Docker**: Containerização com restart policy
5. **Database connection pool**: Evitar locks no SQLite

## ✅ Checklist de Produção

- [x] Tratamento de exceções em todos os endpoints
- [x] Retry automático nas chamadas externas
- [x] Timeout razoável (15s)
- [x] Logging adequado
- [x] Script de start/stop
- [x] Script de monitoramento
- [x] Healthcheck endpoint
- [x] Systemd service file
- [ ] Configurar alertas
- [ ] Setup de backup automático do banco
- [ ] Documentação de recovery

## 🎯 Resultado Esperado

Com essas mudanças, a aplicação:
- ✅ **Não cai** quando a API do Cartola falha temporariamente
- ✅ **Se recupera automaticamente** de crashes
- ✅ **Responde mais rápido** (timeout reduzido)
- ✅ **Tem visibilidade** via logs e monitoramento
- ✅ **Reinicia sozinha** em caso de problemas
