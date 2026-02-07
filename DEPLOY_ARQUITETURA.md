# ⚠️ IMPORTANTE: Arquitetura de Deploy

## OpenLiteSpeed serve `frontend/dist/` DIRETAMENTE

**NUNCA copie arquivos do `frontend/dist/` para o root do projeto.**

### Estrutura Correta:
```
/www/wwwroot/scoutdados.com.br/
├── frontend/
│   ├── src/              # Código-fonte React
│   └── dist/             # ✅ Build final (OLS serve DAQUI)
│       ├── index.html    # ✅ ESTE é servido
│       └── assets/       # ✅ ESTES são servidos
├── api_server.py         # Backend FastAPI
└── deploy.sh             # Script de deploy
```

### ❌ NÃO FAZER:
- Copiar `frontend/dist/index.html` → `/www/wwwroot/scoutdados.com.br/index.html`
- Copiar `frontend/dist/assets/` → `/www/wwwroot/scoutdados.com.br/assets/`
- Editar arquivos em `frontend/dist/` manualmente

### ✅ Deploy Correto:
```bash
# Só frontend (95% dos casos)
./deploy.sh

# Frontend + Backend + Scheduler
./deploy.sh --full
```

O script `deploy.sh`:
1. Faz build em `frontend/dist/`
2. OpenLiteSpeed serve `frontend/dist/` diretamente
3. **NÃO copia nada para o root**

### 🐛 Troubleshooting

**Problema: "Site mostra versão antiga após deploy"**

**Causa:** Arquivos `index.html` ou `/assets/` antigos no root do projeto sobrescrevendo o `frontend/dist/`.

**Solução:**
```bash
cd /www/wwwroot/scoutdados.com.br
rm -f index.html        # Remover index.html do root
rm -rf assets/          # Remover /assets/ do root
./deploy.sh --full      # Rebuild + restart
```

### 📝 Histórico
- **07/02/2026**: Problema identificado e corrigido
  - Arquivos antigos `index.html` e `/assets/` no root causavam cache
  - Movidos para `.OLD` e adicionados ao `.gitignore`
  - Deploy agora funciona corretamente
