# 🔧 Diagnóstico e Correção: Aplicação Fora do Ar

## 📊 Análise Realizada

### Problemas Identificados

1. **❌ Falta de Tratamento de Exceções**
   - Quando a API externa do Cartola FC falhava (timeout/erro), o FastAPI crashava
   - Endpoints retornavam erro 500 e o servidor ficava instável

2. **⏱️ Timeouts Excessivos**
   - Timeout configurado em 30s
   - API do Cartola às vezes demora 7+ segundos
   - Causava timeouts no navegador e má experiência do usuário

3. **🔁 Sem Retry Automático**
   - Uma falha temporária derrubava toda a requisição
   - Não havia tentativas de reconexão

4. **📉 Sem Monitoramento**
   - Quando o servidor caía, ninguém sabia
   - Não havia logs adequados
   - Sem mecanismo de restart automático

## ✅ Correções Implementadas

### 1. Retry Automático e Timeout Otimizado (`src/api/cartola_api.py`)

```python
- Timeout: 30s → 15s
- Retry automático: 3 tentativas com 1s de intervalo
- Logging detalhado de todas as requisições
- Retorna None ao invés de crash
- Diferencia erros 4xx (não retry) de 5xx/timeout (retry)
```

### 2. Proteção dos Endpoints (`api_server.py`)

Todos os endpoints críticos agora têm `try-except`:
- `/api/status`
- `/api/dashboard` 
- `/api/mercado/atletas`
- `/api/confrontos`
- `/api/escalacao/gerar`

**Resultado**: API do Cartola pode cair temporariamente, mas o servidor continua respondendo com erro 503.

### 3. Scripts de Resiliência

#### 📁 `start_server.sh` - Gerenciador
```bash
./start_server.sh start    # Iniciar
./start_server.sh stop     # Parar
./start_server.sh restart  # Reiniciar
./start_server.sh status   # Ver status
```

#### 📁 `monitor.sh` - Monitoramento Ativo
- Verifica servidor a cada 30 segundos
- Restart automático após 3 falhas consecutivas
- Logs em `logs/monitor.log`

#### 📁 `healthcheck.py` - Checagem de Saúde
```bash
python3 healthcheck.py  # Exit code 0 = OK, 1 = Falha
```

#### 📁 `cartolafc.service` - Systemd Service
Para produção com restart automático via systemd.

## 🚀 Como Usar

### Desenvolvimento Local
```bash
python3 api_server.py
```

### Produção (Recomendado)

**Opção 1: Script + Monitor**
```bash
cd /root/cartolafc2026
./start_server.sh start
nohup ./monitor.sh > /dev/null 2>&1 &
```

**Opção 2: Systemd (Melhor)**
```bash
sudo cp cartolafc.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cartolafc.service
sudo systemctl start cartolafc.service
sudo systemctl status cartolafc.service
```

## 📊 Testes Realizados

✅ Servidor inicia corretamente  
✅ Healthcheck passa  
✅ Endpoints respondem  
✅ Retry funciona em falhas temporárias  
✅ Logs são gravados corretamente  

### Teste da API do Cartola
```
✅ Status: 7.49s - Rodada 2, Status 1
✅ Mercado: 0.17s - 695 atletas
✅ Partidas: 0.06s - 10 jogos
```

### Teste dos Endpoints
```
✅ GET / - Health check OK
✅ GET /api/status - Rodada 2, mercado aberto
✅ GET /api/dashboard - Dashboard com 695 atletas
```

## 📝 Logs e Monitoramento

### Ver logs em tempo real
```bash
tail -f logs/api_server.log
tail -f logs/monitor.log
```

### Ver últimos erros
```bash
grep "❌" logs/api_server.log | tail -20
```

## 🎯 Resultado Final

A aplicação agora:
- ✅ **Não cai** quando a API do Cartola falha temporariamente
- ✅ **Se recupera automaticamente** de crashes (com monitor.sh ou systemd)
- ✅ **Responde mais rápido** (timeout reduzido de 30s para 15s)
- ✅ **Tem visibilidade** via logs detalhados
- ✅ **Reinicia sozinha** em caso de problemas
- ✅ **Retorna erros informativos** ao invés de crashar

## 📚 Documentação Completa

Ver [docs/RESILIENCIA.md](docs/RESILIENCIA.md) para detalhes completos sobre:
- Configuração de produção
- Alertas e monitoramento avançado
- Troubleshooting
- Melhorias futuras

## ⚡ Próximos Passos Recomendados

1. **Iniciar o monitoramento**:
   ```bash
   nohup ./monitor.sh &
   ```

2. **Ou configurar systemd** (produção):
   ```bash
   sudo systemctl enable cartolafc.service
   sudo systemctl start cartolafc.service
   ```

3. **Verificar logs regularmente**:
   ```bash
   ./start_server.sh status
   ```

---

**Data da correção**: 30/01/2026  
**Status**: ✅ Servidor rodando e monitorado
