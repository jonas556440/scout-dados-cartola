# 🔒 Auditoria de Segurança - CartolaFC 2026

**Data:** 03/02/2026  
**Status Atual:** ⚠️ **NÃO PRONTO PARA PRODUÇÃO**

---

## 🚨 Vulnerabilidades CRÍTICAS Encontradas

### 1. ❌ CORS Muito Permissivo (api_server.py)

**Problema:** CORS aceita qualquer origem
```python
# VULNERÁVEL:
origins = ["*"]  # Qualquer site pode acessar sua API!
```

**Risco:** 
- Ataques CSRF (Cross-Site Request Forgery)
- Qualquer site malicioso pode fazer requests para sua API
- Roubo de dados via JavaScript em sites de terceiros

**Correção:**
```python
# SEGURO:
ALLOWED_ORIGINS = [
    "https://seudominio.com.br",
    "https://www.seudominio.com.br",
    "http://localhost:5176",  # apenas dev
]
```

---

### 2. ❌ Sem Rate Limiting

**Problema:** API aceita requisições ilimitadas

**Risco:**
- DDoS (Denial of Service) - derrubar servidor com flood de requests
- Scraping massivo de dados
- Custo alto de banda/processamento

**Correção:** Implementar slowapi
```bash
pip install slowapi
```

---

### 3. ❌ Dependências Desatualizadas

**Problema:**
```
requests==2.25.1  # CRÍTICO: CVE-2023-32681 (vulnerabilidade de redirecionamento)
```

**Risco:** Exploits conhecidos em versões antigas

**Correção:**
```bash
pip install --upgrade requests
pip install --upgrade fastapi uvicorn sqlalchemy
```

---

### 4. ❌ Sem HTTPS/SSL

**Problema:** Servidor roda HTTP puro (porta 80)

**Risco:**
- Dados trafegam em texto puro
- Man-in-the-Middle attacks
- Google penaliza sites sem HTTPS no SEO

**Correção:** Implementar Certbot (Let's Encrypt)

---

### 5. ❌ Logs Expõem Informações Sensíveis

**Problema:** Logs podem conter dados privados

**Risco:**
- Vazamento de IPs, comportamento de usuários
- Logs em /tmp podem ser lidos por outros processos

**Correção:**
- Logs em /var/log com permissões restritas
- Rotação de logs (logrotate)

---

### 6. ⚠️ Sem Autenticação na API

**Problema:** Qualquer um pode acessar endpoints

**Risco (MÉDIO):**
- API é pública, mas sem rate limit pode ser abusada
- Para dados públicos do Cartola, é OK
- **MAS:** se adicionar funcionalidades de usuário, PRECISA de auth

**Correção (se adicionar login):**
```bash
pip install python-jose[cryptography] passlib bcrypt
```

---

### 7. ❌ Services Rodando como Root

**Problema:** Services systemd podem estar rodando como root

**Risco:**
- Se invasor explorar vulnerabilidade, tem acesso root total
- Princípio do menor privilégio violado

**Correção:** Criar usuário dedicado

---

### 8. ⚠️ SQL Injection (Baixo Risco)

**Status:** ✅ Protegido pelo SQLAlchemy ORM
- SQLAlchemy usa prepared statements automáticas
- **MAS:** Qualquer query raw SQL seria vulnerável

**Recomendação:** NUNCA usar raw SQL

---

### 9. ❌ Sem Validação de Input

**Problema:** Parâmetros de query não validados estritamente

**Risco:**
- Injeção de valores maliciosos
- Crash do servidor com inputs inválidos

**Correção:** Usar Pydantic models com validadores

---

### 10. ❌ Sem Backup Automático do Banco

**Problema:** Banco SQLite sem backup automatizado

**Risco:**
- Perda de dados em crash/corrupção
- Sem disaster recovery

**Correção:** Cronjob para backup diário

---

## ✅ Pontos POSITIVOS de Segurança

1. ✅ **SQLAlchemy ORM** - protege contra SQL injection
2. ✅ **Pydantic** - validação de tipos nos endpoints
3. ✅ **FastAPI** - framework moderno e seguro
4. ✅ **Sem senhas hardcoded** - não tem credenciais no código
5. ✅ **Sem autenticação desnecessária** - dados são públicos mesmo
6. ✅ **Systemd** - reinicialização automática em crash

---

## 🛡️ Plano de Ação URGENTE (Antes de Produção)

### Prioridade CRÍTICA (obrigatório)

- [ ] **1. Corrigir CORS** - whitelist apenas seu domínio
- [ ] **2. Implementar Rate Limiting** - 100 req/min por IP
- [ ] **3. Atualizar dependências** - requests, fastapi, uvicorn
- [ ] **4. Configurar HTTPS** - Certbot + Let's Encrypt
- [ ] **5. Criar usuário não-root** - para rodar services
- [ ] **6. Firewall** - ufw enable, liberar apenas 80/443

### Prioridade ALTA (recomendado)

- [ ] **7. Implementar logging seguro** - /var/log com rotação
- [ ] **8. Backup automático** - cronjob diário para SQLite
- [ ] **9. Headers de segurança** - CSP, X-Frame-Options, etc
- [ ] **10. Monitoramento** - alertas de erro/downtime

### Prioridade MÉDIA (nice to have)

- [ ] **11. Validação rigorosa** - Pydantic validators custom
- [ ] **12. Testes de segurança** - bandit, safety scan
- [ ] **13. WAF** - Web Application Firewall (CloudFlare free)
- [ ] **14. DDoS protection** - CloudFlare ou Fail2Ban

---

## 📝 Checklist de Produção

### Antes de Apontar Domínio

- [ ] CORS configurado apenas para domínio real
- [ ] Rate limiting ativo
- [ ] Dependências atualizadas
- [ ] HTTPS configurado e testado
- [ ] Firewall ativo (ufw)
- [ ] Services rodando como usuário não-root
- [ ] Logs em /var/log
- [ ] Backup automático configurado
- [ ] Monitoramento básico ativo

### Teste de Segurança Rápido

```bash
# 1. Testar HTTPS
curl -I https://seudominio.com.br

# 2. Verificar headers de segurança
curl -I https://seudominio.com.br | grep -E "X-|Content-Security"

# 3. Testar rate limiting
for i in {1..150}; do curl https://seudominio.com.br/api/status; done

# 4. Scan de portas abertas
nmap -sV SEU_IP

# 5. Verificar usuário dos services
ps aux | grep uvicorn
```

---

## 🔧 Scripts de Correção Rápida

Vou criar scripts para corrigir automaticamente as vulnerabilidades críticas.

---

**⚠️ CONCLUSÃO:** Sistema atual é **INSEGURO** para produção. Precisa das correções críticas (1-6) antes de apontar domínio público.

**Tempo estimado para correções críticas:** 2-3 horas

**Risco se não corrigir:** Alto risco de ataque, vazamento de dados, ou indisponibilidade.
