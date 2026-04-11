/**
 * liveSocket.ts
 * Utilitário para conexão WebSocket ao vivo com reconexão automática por backoff.
 *
 * Uso:
 *   const socket = createLiveSocket(matchId, (data) => { matchData = data; }, (s) => { wsStatus = s; });
 *   onDestroy(() => socket.close());
 */

export type WsStatus = 'connecting' | 'connected' | 'reconnecting' | 'closed';

export interface LiveSocket {
  close(): void;
}

/**
 * Cria e gerencia uma conexão WebSocket para um match ao vivo.
 *
 * @param matchId       - ID da partida (usado na URL do WS)
 * @param onMessage     - Callback chamado com os dados parseados de cada mensagem
 * @param onStatus      - Callback chamado quando o status do WS muda
 * @param baseUrl       - URL base da API (padrão: ws://localhost:8000)
 */
export function createLiveSocket(
  matchId: string,
  onMessage: (data: Record<string, unknown>) => void,
  onStatus: (status: WsStatus) => void,
  baseUrl = 'ws://localhost:8000'
): LiveSocket {
  let ws: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let attempt = 0;
  let closed = false;

  const MAX_DELAY_MS = 30_000;   // máximo de 30s entre tentativas
  const BASE_DELAY_MS = 1_000;   // começa com 1s

  function getDelay(): number {
    // Backoff exponencial: 1s, 2s, 4s, 8s, 16s, 30s (máx)
    return Math.min(BASE_DELAY_MS * Math.pow(2, attempt), MAX_DELAY_MS);
  }

  function connect(): void {
    if (closed) return;

    onStatus(attempt === 0 ? 'connecting' : 'reconnecting');

    ws = new WebSocket(`${baseUrl}/ws/match/${matchId}`);

    ws.onopen = () => {
      attempt = 0;
      onStatus('connected');
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string) as Record<string, unknown>;
        onMessage(data);
      } catch (e) {
        console.error('[LiveSocket] Erro ao parsear mensagem WS:', e);
      }
    };

    ws.onerror = () => {
      // onerror sempre precede onclose — não precisa agir aqui
    };

    ws.onclose = () => {
      ws = null;
      if (closed) {
        onStatus('closed');
        return;
      }
      // Reconecta automaticamente com backoff
      const delay = getDelay();
      attempt++;
      onStatus('reconnecting');
      reconnectTimer = setTimeout(connect, delay);
    };
  }

  // Inicia conexão imediatamente
  connect();

  return {
    close(): void {
      closed = true;
      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      if (ws) {
        ws.close();
        ws = null;
      }
      onStatus('closed');
    }
  };
}
