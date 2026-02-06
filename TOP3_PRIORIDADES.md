# 🎯 TOP 3 PRIORIDADES - ScoutDados

## 🔴 1. CORRIGIR DADOS DESATUALIZADOS (CRÍTICO - 1h)

### Problema
Top Valorizadores e Top Pontuadores mostram dados de **Rodada 1** quando Rodada 2 está ativa.

```
Gabriel Menino: C$10.8 (+79.5%)  ← RODADA 1, não rodada 2!
```

### Causa
O backend usa `variacao_num` que é histórico. Precisa usar **predição** para a rodada atual.

### Solução

**Arquivo**: `/www/wwwroot/scoutdados.com.br/api_server.py` (linha ~840)

Trocar:
```python
# ❌ ERRADO - mostra histórico
top_valor = sorted(atletas_provaveis, key=lambda x: x.get("variacao_num", 0), reverse=True)[:5]
```

Por:
```python
# ✅ CORRETO - usa predição rodada atual
# Usar a análise do MPVCalculator ao invés de apenas variacao_num
from src.analysis.mpv_calculator import MPVCalculator

mpv_calc = MPVCalculator()
top_valor_com_mpv = []
for atleta in atletas_provaveis:
    mpv_score = mpv_calc.calcular_mpv(atleta, confronto_info=None)
    top_valor_com_mpv.append({
        **atleta,
        "mpv_score": mpv_score
    })

top_valor = sorted(top_valor_com_mpv, key=lambda x: x.get("mpv_score", 0), reverse=True)[:5]
```

**Tempo estimado**: 30 minutos  
**Impacto**: Enorme (dados corretos = confiança do usuário)

---

## 🟡 2. MELHORAR TRATAMENTO DE ERROS (IMPORTANTE - 2h)

### Problema
Quando há erro, o frontend fica em branco ou mostra erro genérico.

### Solução A: Error Boundary (React)

**Criar**: `/www/wwwroot/scoutdados.com.br/frontend/src/components/ErrorBoundary.tsx`

```typescript
import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  children: React.ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    console.error('Erro capturado:', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
          <div className="text-center max-w-md">
            <AlertCircle className="w-16 h-16 text-destructive mx-auto mb-4" />
            <h1 className="text-2xl font-bold mb-2">Oops! Algo deu errado</h1>
            <p className="text-muted-foreground mb-6">
              {this.state.error?.message || 'Erro desconhecido'}
            </p>
            <Button 
              onClick={() => window.location.reload()}
              className="gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Tentar Novamente
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Usar em**: `frontend/src/App.tsx`
```typescript
import { ErrorBoundary } from '@/components/ErrorBoundary';

const App = () => (
  <ErrorBoundary>
    {/* Rest of app */}
  </ErrorBoundary>
);
```

### Solução B: Handle API Errors

**Atualizar**: `frontend/src/hooks/useCartolaApi.ts`

```typescript
export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/dashboard');
        if (!response.ok) {
          throw new Error(`API retornou ${response.status}`);
        }
        return response.json();
      } catch (error) {
        throw new Error(
          error instanceof Error 
            ? error.message 
            : 'Falha ao carregar dados'
        );
      }
    },
    retry: 2,
    retryDelay: 1000,
  });
}
```

**Tempo estimado**: 1.5 horas  
**Impacto**: Alto (melhor UX em caso de erro)

---

## 🟢 3. IMPLEMENTAR CACHE LOCAL (IMPORTANTE - 2h)

### Problema
Cada vez que usuário recarrega página, faz requisição para API  
→ Demora 2-3 segundos para carregar  
→ Péssima experiência em mobile

### Solução: localStorage + React Query

**Criar**: `frontend/src/lib/persistor.ts`

```typescript
// LocalStorage persister para React Query
export const localStoragePersistor = {
  persistClient: async (client: QueryClient) => {
    const cache = client.getQueryData(['dashboard']);
    if (cache) {
      localStorage.setItem('dashboard-cache', JSON.stringify(cache));
    }
  },

  restoreClient: async (): Promise<QueryClient | undefined> => {
    const cached = localStorage.getItem('dashboard-cache');
    if (!cached) return undefined;
    return JSON.parse(cached);
  },
};
```

**Usar em hooks**:

```typescript
export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: () => fetch('/api/dashboard').then(r => r.json()),
    staleTime: 5 * 60 * 1000, // 5 minutos
    gcTime: 24 * 60 * 60 * 1000, // Cache por 24h
    initialData: () => {
      const cached = localStorage.getItem('dashboard-cache');
      return cached ? JSON.parse(cached) : undefined;
    },
  });
}
```

**Tempo estimado**: 2 horas  
**Impacto**: Altíssimo (reduz 2s em 95% das visitas)

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### Dia 1: Corrigir Dados
- [ ] Atualizar api_server.py linha 840
- [ ] Usar MPVCalculator ao invés de variacao_num
- [ ] Testar com `curl -s https://scoutdados.com.br/api/dashboard`
- [ ] Rebuild frontend e deploy
- [ ] **TEMPO: 1h**

### Dia 2: Error Handling
- [ ] Criar ErrorBoundary.tsx
- [ ] Implementar retry logic
- [ ] Criar fallback data
- [ ] Testar desligando backend
- [ ] **TEMPO: 2h**

### Dia 2-3: Cache Local
- [ ] Implementar localStorage persistor
- [ ] Adicionar ao React Query
- [ ] Testar modo offline
- [ ] Benchmark carregamento
- [ ] **TEMPO: 2h**

### Dia 3: Deploy e Testes
- [ ] Build frontend: `bun run build`
- [ ] Deploy: `cp -r frontend/dist/* .`
- [ ] Teste no navegador
- [ ] Teste em mobile
- [ ] **TEMPO: 1h**

**TOTAL: ~6 horas de trabalho**

---

## 📊 IMPACTO ESTIMADO

| Melhorias | Antes | Depois | Ganho |
|-----------|-------|--------|-------|
| **Dados desatualizados** | ❌ | ✅ | +50% confiança |
| **Tempo carregamento** | 2-3s | 0.5s | 6x mais rápido |
| **Experiência erro** | Branco | Mensagem clara | +80% retenção |
| **Uso offline** | ❌ | ✅ | Funciona sem internet |

---

## 🚀 DEPOIS DISSO?

1. **Ativar Google Analytics**
   - Trocar `G-XXXXXXXXXX` no index.html
   - Pegar ID em: https://analytics.google.com

2. **Criar Blog (3-5 artigos)**
   - "Como escolher capitão cartola"
   - "Importância do mando de campo"
   - "Estratégia de valorização"
   - "Como usar ScoutDados"
   - "Top 5 maiores valorizações Cartola 2026"

3. **Lançar em Communities**
   - Reddit: r/CartolaBrazil
   - Discord: Cartola FC
   - WhatsApp groups
   - Twitter: #CartolaBrasil

---

## 📞 SUPORTE

Se tiver dúvidas ao implementar:
1. Verificar `/ANALISE_COMPLETA_APLICACAO.md` para detalhes
2. Comparar com código existente
3. Testar localmente antes de deploy
