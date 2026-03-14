# Plano de Implementação: Realtime Data Extraction Improvement

## Visão Geral

Este plano implementa melhorias no sistema de extração de dados em tempo real de partidas profissionais de League of Legends Esports. A implementação está organizada em 4 fases incrementais ao longo de 4 semanas, cada uma construindo sobre a anterior.

## Tasks

### Phase 1: Core Components (Week 1)

- [x] 1. Implementar RetrySystem
  - [x] 1.1 Criar arquivo `interface/retry_system.py` com classe RetrySystem
    - Implementar `__init__` com RetryConfig e logger
    - Implementar `fetch_with_retry` com lógica de retry
    - Implementar `_calculate_delay` para backoff exponencial
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_
  
  - [x] 1.2 Escrever property test para retry com fallback de parâmetro
    - **Property 1: Retry com Fallback de Parâmetro**
    - **Valida: Requirements 1.1, 1.2, 8.3**
  
  - [x] 1.3 Escrever property test para backoff exponencial
    - **Property 2: Backoff Exponencial**
    - **Valida: Requirements 1.3, 1.4, 1.5, 1.6**
  
  - [x] 1.4 Escrever property test para logging completo de requisições
    - **Property 3: Logging Completo de Requisições**
    - **Valida: Requirements 1.7, 6.1, 6.2, 6.3**

- [x] 2. Implementar CacheLayer
  - [x] 2.1 Criar arquivo `interface/cache_layer.py` com classe CacheLayer
    - Implementar `__init__` com dicionário thread-safe
    - Implementar `get` com verificação de expiração
    - Implementar `set` com validação de game_id
    - Implementar `delete`, `clear` e `cleanup_expired`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  
  - [x] 2.2 Escrever property test para cache retorna dados válidos
    - **Property 4: Cache Retorna Dados Válidos**
    - **Valida: Requirements 2.3**
  
  - [x] 2.3 Escrever property test para cache expira e revalida
    - **Property 5: Cache Expira e Revalida**
    - **Valida: Requirements 2.4**
  
  - [x] 2.4 Escrever property test para cache usa game_id como chave
    - **Property 6: Cache Usa Game_ID como Chave**
    - **Valida: Requirements 2.5**
  
  - [x] 2.5 Escrever property test para cache armazena timestamp
    - **Property 7: Cache Armazena Timestamp**
    - **Valida: Requirements 2.6**

- [x] 3. Integrar componentes com live_service.py
  - [x] 3.1 Modificar `interface/live_service.py` para importar novos componentes
    - Adicionar imports de RetrySystem e CacheLayer
    - Configurar logging estruturado
    - Inicializar instâncias globais dos componentes
    - _Requirements: 6.1, 6.6_
  
  - [x] 3.2 Refatorar `get_game_window` para usar cache e retry
    - Adicionar verificação de cache antes de buscar API
    - Usar RetrySystem.fetch_with_retry para requisições
    - Armazenar resultado em cache após sucesso
    - _Requirements: 1.1, 2.1, 2.3, 2.4, 2.5, 8.1_
  
  - [x] 3.3 Refatorar `get_game_details` para usar cache e retry
    - Adicionar verificação de cache antes de buscar API
    - Usar RetrySystem.fetch_with_retry para requisições
    - Armazenar resultado em cache após sucesso
    - _Requirements: 1.2, 2.2, 2.3, 2.4, 2.5, 8.2_
  
  - [x] 3.4 Escrever testes unitários para integração
    - Testar cache hit e cache miss
    - Testar retry em caso de falha
    - Testar logging de operações
    - _Requirements: 2.3, 2.4_

- [x] 4. Checkpoint - Validar componentes core
  - Executar todos os testes unitários e property tests
  - Verificar logs estruturados estão sendo gerados
  - Confirmar cache está funcionando corretamente
  - Perguntar ao usuário se há dúvidas ou ajustes necessários

### Phase 2: Monitoring (Week 2)

- [x] 5. Implementar HealthMonitor
  - [x] 5.1 Criar arquivo `interface/health_monitor.py` com classe HealthMonitor
    - Implementar `__init__` com configuração de check
    - Implementar `start` e `stop` para thread de monitoramento
    - Implementar `_check_health` para verificar API
    - Implementar `_monitoring_loop` para loop contínuo
    - Implementar `get_status` para retornar HealthStatus
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 5.2 Escrever property test para health check usa endpoint correto
    - **Property 14: Health Check Usa Endpoint Correto**
    - **Valida: Requirements 7.2**
  
  - [x] 5.3 Escrever property test para health status reflete sucesso
    - **Property 15: Health Status Reflete Sucesso**
    - **Valida: Requirements 7.3**
  
  - [x] 5.4 Escrever testes unitários para HealthMonitor
    - Testar marcação como unhealthy após 3 falhas
    - Testar reset de contador em sucesso
    - Testar thread safety
    - _Requirements: 7.4_

- [x] 6. Adicionar logging estruturado completo
  - [x] 6.1 Configurar formato de log JSON em live_service.py
    - Adicionar campos match_id e game_id em todas as mensagens
    - Configurar níveis de log apropriados (DEBUG, INFO, WARNING, ERROR)
    - _Requirements: 6.6, 6.7_
  
  - [x] 6.2 Adicionar logging de operações de cache
    - Log de cache hit/miss com nível DEBUG
    - Log de cache expiration com nível DEBUG
    - Log de cache set com nível DEBUG
    - _Requirements: 6.4_
  
  - [x] 6.3 Escrever property test para logging de operações de cache
    - **Property 10: Logging de Operações de Cache**
    - **Valida: Requirements 6.4**
  
  - [x] 6.4 Escrever property test para níveis de log apropriados
    - **Property 12: Níveis de Log Apropriados**
    - **Valida: Requirements 6.6**
  
  - [x] 6.5 Escrever property test para logs contêm identificadores
    - **Property 13: Logs Contêm Identificadores**
    - **Valida: Requirements 6.7**

- [x] 7. Criar endpoint /api/health
  - [x] 7.1 Adicionar endpoint GET /api/health em api.py
    - Retornar status do HealthMonitor
    - Incluir is_healthy, last_check, consecutive_failures
    - Incluir response_time_ms se disponível
    - _Requirements: 7.6_
  
  - [x] 7.2 Inicializar HealthMonitor no startup da aplicação
    - Chamar health_monitor.start() no startup
    - Configurar URL de check para getLive endpoint
    - _Requirements: 7.1_
  
  - [x] 7.3 Escrever property test para health status exposto via API
    - **Property 16: Health Status Exposto via API**
    - **Valida: Requirements 7.6**

- [x] 8. Checkpoint - Validar sistema de monitoramento
  - Executar todos os testes de health monitoring
  - Verificar endpoint /api/health retorna dados corretos
  - Confirmar logs estruturados incluem todos os campos necessários
  - Perguntar ao usuário se há dúvidas ou ajustes necessários

### Phase 3: Polling (Week 3)

- [x] 9. Implementar PollingService
  - [x] 9.1 Criar arquivo `interface/polling_service.py` com classe PollingService
    - Implementar `__init__` com callback e intervalo
    - Implementar `start`, `stop`, `pause`, `resume`
    - Implementar `_polling_loop` para loop contínuo
    - Implementar `get_state` para retornar PollingState
    - _Requirements: 3.1, 3.2, 3.3, 3.5_
  
  - [x] 9.2 Escrever property test para polling ativo durante partida
    - **Property 8: Polling Ativo Durante Partida**
    - **Valida: Requirements 3.2**
  
  - [x] 9.3 Escrever property test para polling usa cache
    - **Property 9: Polling Usa Cache**
    - **Valida: Requirements 3.4**
  
  - [x] 9.4 Escrever property test para logging de ciclo de polling
    - **Property 11: Logging de Ciclo de Polling**
    - **Valida: Requirements 6.5**
  
  - [x] 9.5 Escrever testes unitários para PollingService
    - Testar intervalo de polling correto
    - Testar parada quando não há partidas
    - Testar thread safety
    - _Requirements: 3.1, 3.3_

- [x] 10. Implementar gerenciamento de estado de partidas
  - [x] 10.1 Adicionar lógica de detecção de partida finalizada em live_service.py
    - Verificar gameState == "finished" nos frames
    - Verificar todos os games com estado "completed"
    - Verificar se um time atingiu vitórias necessárias
    - _Requirements: 9.1, 9.2, 9.3_
  
  - [x] 10.2 Integrar detecção de estado com PollingService
    - Parar polling quando partida finaliza
    - Limpar cache quando partida finaliza
    - Verificar estado antes de cada iteração de polling
    - _Requirements: 9.4, 9.6_
  
  - [x] 10.3 Escrever property test para polling para em partida finalizada
    - **Property 22: Polling Para em Partida Finalizada**
    - **Valida: Requirements 9.1**
  
  - [x] 10.4 Escrever property test para série finalizada por games completos
    - **Property 23: Série Finalizada por Games Completos**
    - **Valida: Requirements 9.2**
  
  - [x] 10.5 Escrever property test para série finalizada por vitórias
    - **Property 24: Série Finalizada por Vitórias**
    - **Valida: Requirements 9.3**
  
  - [x] 10.6 Escrever property test para verificação de estado antes de polling
    - **Property 25: Verificação de Estado Antes de Polling**
    - **Valida: Requirements 9.4**
  
  - [x] 10.7 Escrever property test para cache limpo ao finalizar
    - **Property 26: Cache Limpo ao Finalizar**
    - **Valida: Requirements 9.6**

- [x] 11. Implementar tratamento de Game_ID unknown
  - [x] 11.1 Adicionar lógica de resolução de Game_ID unknown em live_service.py
    - Buscar lista de jogos ao vivo a cada 15 segundos
    - Atualizar automaticamente quando novo Game_ID é encontrado
    - Limpar cache anterior ao resolver Game_ID
    - _Requirements: 5.1, 5.2, 5.5_
  
  - [x] 11.2 Adicionar timeout e mensagem informativa para Game_ID unknown
    - Exibir mensagem após 5 minutos sem resolução
    - Registrar cada tentativa de resolução no log
    - _Requirements: 5.3, 5.4_
  
  - [x] 11.3 Escrever property test para resolução de Game_ID unknown
    - **Property 32: Resolução de Game_ID Unknown**
    - **Valida: Requirements 5.1, 5.2**
  
  - [x] 11.4 Escrever property test para logging de tentativas de resolução
    - **Property 33: Logging de Tentativas de Resolução**
    - **Valida: Requirements 5.4**
  
  - [x] 11.5 Escrever property test para cache limpo ao resolver Game_ID
    - **Property 34: Cache Limpo ao Resolver Game_ID**
    - **Valida: Requirements 5.5**

- [x] 12. Implementar feedback visual no frontend
  - [x] 12.1 Criar estados de UI em componente Svelte
    - Estado LOADING implementado com "Carregando partidas..." animado
    - Estado ERROR implementado com mensagem de partida não encontrada
    - Estado SUCCESS implementado com exibição dos dados
    - _Requirements: 4.1, 4.2, 4.7_
  
  - [x] 12.2 Adicionar indicadores visuais para cada estado
    - "Carregando partidas..." com animate-pulse para primeira carga
    - "Partida não encontrada ou dados ainda não disponíveis" para erro/ausência
    - Dados exibidos diretamente quando disponíveis
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [x] 12.3 Integrar polling HTTP no frontend
    - Polling implementado via setInterval a cada 10 segundos em +page.svelte e match/[id]/+page.svelte
    - Polling para automaticamente ao navegar (clearInterval no retorno do onMount)
    - _Requirements: 3.1, 3.5, 3.6_

- [x] 13. Checkpoint - Validar sistema de polling
  - Executar todos os testes de polling
  - Verificar polling inicia e para corretamente
  - Confirmar UI mostra estados corretos
  - Testar resolução de Game_ID unknown
  - Perguntar ao usuário se há dúvidas ou ajustes necessários

### Phase 4: Optimization (Week 4)

- [x] 14. Implementar otimização de timestamps
  - [x] 14.1 Adicionar função para arredondar timestamp para múltiplo de 10
    - Usar em requisições ao game_window endpoint
    - Subtrair 60 segundos do timestamp atual
    - _Requirements: 8.1, 8.4_
  
  - [x] 14.2 Implementar uso de rfc460Timestamp do frame
    - Usar em requisições ao game_details endpoint
    - Implementar fallback para timestamp calculado
    - _Requirements: 8.2, 8.6_
  
  - [x] 14.3 Adicionar cache buster em todas as requisições
    - Incluir parâmetro _ com timestamp + random
    - _Requirements: 8.5_
  
  - [x] 14.4 Escrever property tests para otimização de timestamps
    - **Property 17: Timestamp Múltiplo de 10** — Valida: Requirements 8.1
    - **Property 18: Details Usa Timestamp do Frame** — Valida: Requirements 8.2
    - **Property 19: Timestamp com Offset** — Valida: Requirements 8.4
    - **Property 20: Cache Buster em Requisições** — Valida: Requirements 8.5
    - **Property 21: Fallback de Timestamp** — Valida: Requirements 8.6

- [x] 15. Implementar fallback para schedule
  - [x] 15.1 Adicionar lógica de fallback para schedule em live_service.py
    - Consultar getSchedule quando getLive não retorna partida esperada
    - Incluir partidas que começaram há menos de 4 horas
    - Incluir partidas que começam em menos de 10 minutos
    - _Requirements: 10.1, 10.2, 10.3_
  
  - [x] 15.2 Implementar deduplicação e filtragem
    - Evitar duplicatas usando Match_ID
    - Excluir partidas com estado "completed"
    - Registrar uso de fallback no log
    - _Requirements: 10.4, 10.5, 10.6_
  
  - [x] 15.3 Escrever property tests para fallback de schedule
    - **Property 27: Fallback para Schedule** — Valida: Requirements 10.1
    - **Property 28: Inclusão por Janela Temporal** — Valida: Requirements 10.2, 10.3
    - **Property 29: Deduplicação por Match_ID** — Valida: Requirements 10.4
    - **Property 30: Exclusão de Partidas Finalizadas do Fallback** — Valida: Requirements 10.5
    - **Property 31: Logging de Fallback** — Valida: Requirements 10.6

- [ ] 16. Implementar circuit breaker (opcional)
  - [ ] 16.1 Criar classe CircuitBreaker em retry_system.py
    - Implementar estados: closed, open, half-open
    - Implementar lógica de threshold de falhas
    - Implementar timeout para tentar novamente
  
  - [ ] 16.2 Integrar CircuitBreaker com RetrySystem
    - Usar circuit breaker antes de fazer requisições
    - Lançar exceção quando circuit está open
    - Registrar mudanças de estado no log
  
  - [ ] 16.3 Escrever testes unitários para CircuitBreaker
    - Testar transição de estados
    - Testar threshold de falhas
    - Testar timeout de recuperação

- [x] 17. Tuning de TTLs e configuração
  - [x] 17.1 Criar arquivo de configuração centralizado
    - Criar classe Config com valores de environment variables
    - Adicionar validação de configuração
    - Documentar todas as variáveis de ambiente
    - _Requirements: 2.1, 2.2, 3.1_
  
  - [x] 17.2 Ajustar TTLs baseado em testes
    - Validar TTL de 5s para game_window e game_details
    - Validar TTL de 10s para live_games_list
    - Validar TTL de 60s para schedule_today
    - Ajustar se necessário baseado em métricas

- [x] 18. Implementar endpoint de métricas
  - [x] 18.1 Adicionar endpoint GET /api/metrics em api.py
    - Retornar estatísticas de cache (hit rate, size)
    - Retornar estatísticas de retry (total, success rate)
    - Retornar estado de polling
    - Retornar health status da API
  
  - [x] 18.2 Adicionar coleta de métricas nos componentes
    - Adicionar contadores em CacheLayer
    - Adicionar contadores em RetrySystem
    - Adicionar métricas de tempo de resposta

- [x] 19. Testes de performance e integração final
  - [x] 19.1 Executar todos os property tests
    - Validar todas as 34 propriedades de correção
    - Confirmar 100 iterações por teste
    - Verificar nenhuma falha
  
  - [x] 19.2 Executar testes de integração end-to-end
    - Testar fluxo completo de requisição
    - Testar cenários de erro e recuperação
    - Testar polling com partidas reais
  
  - [x] 19.3 Realizar testes de carga
    - Simular múltiplas requisições simultâneas
    - Verificar cache hit rate > 60%
    - Verificar tempo de resposta < 500ms
    - Verificar P95 < 2s

- [x] 20. Checkpoint final - Validação completa
  - Executar suite completa de testes
  - Verificar todas as métricas de sucesso
  - Confirmar documentação está atualizada
  - Validar com usuário que todos os requisitos foram atendidos

## Notas

- Tasks marcadas com `*` são opcionais e podem ser puladas para MVP mais rápido
- Cada task referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Property tests validam propriedades universais de correção
- Unit tests validam exemplos específicos e edge cases
- Implementação usa Python 3.x conforme especificado no design
