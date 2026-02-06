# Diagnóstico e Correção de Estabilidade da API

## Problema Reportado
O sistema parava de responder após um tempo de uso, apresentando erros `net::ERR_CONNECTION_REFUSED` no frontend.

## Causa Raiz Identificada
1. **Bloqueio do Event Loop (Principal):** A API estava utilizando definições assíncronas (`async def`) para endpoints que executavam código síncrono bloqueante (chamadas `requests` para a API do Cartola e operações de banco de dados). Quando a API externa demorava para responder, o processo Python inteiro travava, deixando de aceitar novas conexões e eventualmente caindo ou sofrendo timeout.
2. **Concorrência de Banco de Dados:** O SQLite no modo padrão pode sofrer travamentos quando há concorrência de escrita (entre o Scheduler e a API), causando erros e lentidão.

## Correções Aplicadas
1. **Conversão para Thread Pool:** Todos os endpoints em `api_server.py` que realizam operações bloqueantes foram convertidos de `async def` para `def`. Isso faz com que o FastAPI gerencie essas requisições em threads separadas, liberando o loop principal para manter a conexão ativa e aceitar novas requisições.
2. **Ativação do Modo WAL (Write-Ahead Logging):** O gerenciador de banco de dados (`src/database/db_manager.py`) foi atualizado para ativar o modo WAL e `synchronous=NORMAL` no SQLite. Isso permite leituras e escritas simultâneas muito mais eficientes, reduzindo drasticamente a chance de "Database is locked".

## Próximos Passos
O servidor foi reiniciado com as correções. A estabilidade deve melhorar significativamente. Se o problema persistir, verifique os logs em `logs/api_server.log`.
