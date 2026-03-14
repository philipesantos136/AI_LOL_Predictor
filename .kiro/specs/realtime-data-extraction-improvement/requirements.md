# Documento de Requisitos

## Introdução

Este documento especifica os requisitos para melhorar o sistema de extração de dados em tempo real de partidas profissionais de League of Legends Esports. O sistema atual apresenta falhas ao exibir dados ao vivo, mostrando "Escalação indisponível" mesmo quando os dados deveriam estar disponíveis na API do LoL Esports.

O objetivo é implementar um sistema robusto de retry, cache inteligente, polling automático e melhor feedback visual para garantir que os dados das partidas ao vivo sejam exibidos de forma confiável aos usuários.

## Glossário

- **Live_Data_Service**: Módulo Python responsável por buscar e processar dados ao vivo da API do LoL Esports
- **LoL_Esports_API**: API pública do LoL Esports (feed.lolesports.com/livestats/v1)
- **Game_Window**: Endpoint da API que retorna estatísticas gerais de times e jogadores
- **Game_Details**: Endpoint da API que retorna dados detalhados como itens dos jogadores
- **Retry_System**: Sistema que tenta novamente requisições falhadas com estratégia exponencial
- **Cache_Layer**: Camada de armazenamento temporário de dados para reduzir chamadas à API
- **Polling_Service**: Serviço que busca dados periodicamente em intervalos regulares
- **Health_Monitor**: Componente que verifica a disponibilidade da API
- **UI_Feedback**: Interface visual que informa o estado do carregamento ao usuário
- **Game_ID**: Identificador único de uma partida específica retornado pela API
- **Match_ID**: Identificador único de uma série de partidas (BO3, BO5)
- **Frame**: Snapshot dos dados da partida em um momento específico
- **Timestamp**: Marcador temporal RFC460 usado para sincronizar requisições

## Requisitos

### Requisito 1: Sistema de Retry Inteligente

**User Story:** Como desenvolvedor, eu quero que o sistema tente novamente requisições falhadas automaticamente, para que erros temporários da API não resultem em dados indisponíveis para o usuário.

#### Acceptance Criteria

1. WHEN THE Game_Window endpoint retorna erro 400, THE Retry_System SHALL tentar novamente sem o parâmetro startingTime
2. WHEN THE Game_Details endpoint retorna erro 400, THE Retry_System SHALL tentar novamente sem o parâmetro startingTime
3. WHEN uma requisição à API falha, THE Retry_System SHALL aguardar 2 segundos antes da primeira tentativa
4. WHEN uma segunda tentativa falha, THE Retry_System SHALL aguardar 4 segundos antes da próxima tentativa
5. WHEN uma terceira tentativa falha, THE Retry_System SHALL aguardar 8 segundos antes da próxima tentativa
6. THE Retry_System SHALL realizar no máximo 3 tentativas antes de retornar erro
7. WHEN todas as tentativas falharem, THE Live_Data_Service SHALL registrar o erro com detalhes completos no log

### Requisito 2: Cache Inteligente de Dados

**User Story:** Como desenvolvedor, eu quero implementar cache de dados da API, para que requisições repetidas não sobrecarreguem a API e melhorem o tempo de resposta.

#### Acceptance Criteria

1. THE Cache_Layer SHALL armazenar dados do Game_Window por 5 segundos
2. THE Cache_Layer SHALL armazenar dados do Game_Details por 5 segundos
3. WHEN dados em cache existem e não expiraram, THE Live_Data_Service SHALL retornar os dados em cache
4. WHEN dados em cache expiraram, THE Live_Data_Service SHALL buscar novos dados da API
5. THE Cache_Layer SHALL usar o Game_ID como chave de identificação
6. THE Cache_Layer SHALL armazenar o timestamp de criação junto com os dados
7. WHEN o Game_ID é "unknown", THE Cache_Layer SHALL não armazenar dados em cache

### Requisito 3: Polling Automático

**User Story:** Como usuário, eu quero que os dados da partida sejam atualizados automaticamente, para que eu não precise clicar manualmente no botão de atualizar.

#### Acceptance Criteria

1. THE Polling_Service SHALL buscar dados atualizados a cada 10 segundos
2. WHEN uma partida está em andamento, THE Polling_Service SHALL estar ativo
3. WHEN nenhuma partida está em andamento, THE Polling_Service SHALL estar inativo
4. THE Polling_Service SHALL usar o cache para evitar requisições duplicadas
5. WHEN o usuário navega para outra página, THE Polling_Service SHALL ser interrompido
6. THE Polling_Service SHALL exibir um indicador visual de "Atualizando" durante a busca

### Requisito 4: Feedback Visual Aprimorado

**User Story:** Como usuário, eu quero ver claramente o estado do carregamento dos dados, para que eu saiba se o sistema está funcionando ou se há algum problema.

#### Acceptance Criteria

1. WHEN dados estão sendo carregados pela primeira vez, THE UI_Feedback SHALL exibir "Carregando dados da partida..."
2. WHEN dados estão sendo atualizados em background, THE UI_Feedback SHALL exibir um ícone de atualização discreto
3. WHEN a API retorna erro 400, THE UI_Feedback SHALL exibir "Dados ainda não disponíveis. Tentando novamente..."
4. WHEN todas as tentativas falharem, THE UI_Feedback SHALL exibir "Erro ao carregar dados. Tente novamente em alguns instantes"
5. WHEN o Game_ID é "unknown", THE UI_Feedback SHALL exibir "Aguardando início da partida..."
6. WHEN dados são carregados com sucesso, THE UI_Feedback SHALL exibir o timestamp da última atualização
7. THE UI_Feedback SHALL usar cores distintas para estados diferentes (azul para carregando, amarelo para aguardando, vermelho para erro)

### Requisito 5: Tratamento de Game_ID Unknown

**User Story:** Como desenvolvedor, eu quero melhorar o tratamento quando o Game_ID é "unknown", para que o sistema continue tentando obter o ID correto automaticamente.

#### Acceptance Criteria

1. WHEN o Game_ID é "unknown", THE Live_Data_Service SHALL buscar a lista de jogos ao vivo a cada 15 segundos
2. WHEN um novo Game_ID é encontrado para o Match_ID, THE Live_Data_Service SHALL atualizar automaticamente
3. WHEN o Game_ID permanece "unknown" por mais de 5 minutos, THE Live_Data_Service SHALL exibir mensagem informativa
4. THE Live_Data_Service SHALL registrar no log cada tentativa de resolver Game_ID "unknown"
5. WHEN o Game_ID é resolvido, THE Live_Data_Service SHALL limpar o cache anterior

### Requisito 6: Sistema de Logs Detalhados

**User Story:** Como desenvolvedor, eu quero logs detalhados de todas as operações da API, para que eu possa diagnosticar problemas rapidamente.

#### Acceptance Criteria

1. THE Live_Data_Service SHALL registrar cada requisição à API com timestamp, endpoint e parâmetros
2. THE Live_Data_Service SHALL registrar cada resposta da API com status code e tempo de resposta
3. WHEN uma requisição falha, THE Live_Data_Service SHALL registrar o erro completo com stack trace
4. THE Live_Data_Service SHALL registrar operações de cache (hit, miss, expiration)
5. THE Live_Data_Service SHALL registrar início e fim do polling
6. THE Live_Data_Service SHALL usar níveis de log apropriados (DEBUG, INFO, WARNING, ERROR)
7. THE Live_Data_Service SHALL incluir o Game_ID e Match_ID em todas as mensagens de log relevantes

### Requisito 7: Health Check da API

**User Story:** Como desenvolvedor, eu quero monitorar a saúde da API do LoL Esports, para que eu possa detectar problemas de disponibilidade proativamente.

#### Acceptance Criteria

1. THE Health_Monitor SHALL verificar a disponibilidade da API a cada 60 segundos
2. THE Health_Monitor SHALL fazer uma requisição leve ao endpoint getLive
3. WHEN a API responde com sucesso, THE Health_Monitor SHALL marcar status como "healthy"
4. WHEN a API falha 3 vezes consecutivas, THE Health_Monitor SHALL marcar status como "unhealthy"
5. WHEN o status muda para "unhealthy", THE Health_Monitor SHALL registrar alerta no log
6. THE Health_Monitor SHALL expor o status atual via endpoint /api/health
7. WHEN a API está "unhealthy", THE UI_Feedback SHALL exibir aviso ao usuário

### Requisito 8: Otimização de Requisições com Timestamp

**User Story:** Como desenvolvedor, eu quero usar timestamps corretos nas requisições, para que a API retorne os dados mais recentes disponíveis.

#### Acceptance Criteria

1. WHEN buscar Game_Window, THE Live_Data_Service SHALL usar timestamp arredondado para múltiplos de 10 segundos
2. WHEN buscar Game_Details, THE Live_Data_Service SHALL usar o timestamp RFC460 do frame do Game_Window
3. WHEN o timestamp causa erro 400, THE Live_Data_Service SHALL tentar sem timestamp
4. THE Live_Data_Service SHALL subtrair 60 segundos do timestamp atual para evitar dados futuros
5. THE Live_Data_Service SHALL incluir cache buster em todas as requisições
6. WHEN o Frame não contém timestamp RFC460, THE Live_Data_Service SHALL usar timestamp calculado

### Requisito 9: Gerenciamento de Estado de Partidas

**User Story:** Como desenvolvedor, eu quero detectar corretamente quando uma partida terminou, para que o sistema pare de fazer polling desnecessário.

#### Acceptance Criteria

1. WHEN o gameState do Frame é "finished", THE Polling_Service SHALL ser interrompido
2. WHEN todos os games de uma série estão "completed", THE Live_Data_Service SHALL marcar a série como finalizada
3. WHEN um time atinge o número de vitórias necessário, THE Live_Data_Service SHALL marcar a série como finalizada
4. THE Live_Data_Service SHALL verificar o estado da partida antes de cada polling
5. WHEN uma partida finaliza, THE UI_Feedback SHALL exibir "Partida finalizada"
6. THE Live_Data_Service SHALL limpar o cache quando uma partida finaliza

### Requisito 10: Fallback para Schedule

**User Story:** Como desenvolvedor, eu quero usar dados do schedule como fallback, para que partidas recém-iniciadas sejam detectadas mesmo se getLive ainda não as lista.

#### Acceptance Criteria

1. WHEN getLive não retorna uma partida esperada, THE Live_Data_Service SHALL consultar getSchedule
2. WHEN uma partida no schedule começou há menos de 4 horas, THE Live_Data_Service SHALL incluí-la na lista de jogos ao vivo
3. WHEN uma partida no schedule começa em menos de 10 minutos, THE Live_Data_Service SHALL incluí-la na lista de jogos ao vivo
4. THE Live_Data_Service SHALL evitar duplicatas entre getLive e getSchedule usando Match_ID
5. WHEN o schedule indica que a partida terminou, THE Live_Data_Service SHALL não incluí-la no fallback
6. THE Live_Data_Service SHALL registrar no log quando usar fallback do schedule
