"""
socket_manager.py
Publisher-Subscriber WebSocket manager para transmissão de dados ao vivo.

Arquitetura:
  - Um único background task por match_id ativo.
  - O task resolve o game_id uma única vez (via getEventDetails) e
    depois faz polling apenas em window + details a cada 3s.
  - Window e details são buscados em paralelo (asyncio.gather).
  - Só faz broadcast quando os dados mudam (comparação por hash).
  - Quando o último cliente desconecta, o task é cancelado automaticamente.
"""

import asyncio
import hashlib
import json
import logging
from typing import Dict, Set, Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# Intervalo otimizado: 3s é um compromisso entre latência e carga na API.
# A Riot atualiza frames a cada ~10s, mas polling mais rápido captura
# o novo frame quase imediatamente após disponível.
POLL_INTERVAL = 3  # segundos

# Intervalo para re-resolver o game_id (troca de mapa em BO3/BO5)
GAME_ID_REFRESH_INTERVAL = 30  # segundos


class ConnectionManager:
    """Gerencia conexões WebSocket ativas e background polling tasks."""

    def __init__(self) -> None:
        # match_id → conjunto de WebSockets conectados
        self._clients: Dict[str, Set[WebSocket]] = {}
        # match_id → asyncio.Task de polling
        self._tasks: Dict[str, asyncio.Task] = {}

    # ─── Conexão / Desconexão ────────────────────────────────────────────────

    async def connect(self, match_id: str, websocket: WebSocket) -> None:
        """Aceita a conexão WS e inicia um polling task se necessário."""
        await websocket.accept()

        if match_id not in self._clients:
            self._clients[match_id] = set()

        self._clients[match_id].add(websocket)
        logger.info(f"[WS] Cliente conectado: match_id={match_id} "
                    f"total={len(self._clients[match_id])}")

        # Inicia o background task apenas se ainda não existe
        if match_id not in self._tasks or self._tasks[match_id].done():
            task = asyncio.create_task(self._polling_task(match_id))
            self._tasks[match_id] = task
            logger.info(f"[WS] Background task iniciado para match_id={match_id}")

    def disconnect(self, match_id: str, websocket: WebSocket) -> None:
        """Remove cliente do registry e cancela o task se não há mais clientes."""
        clients = self._clients.get(match_id, set())
        clients.discard(websocket)

        remaining = len(clients)
        logger.info(f"[WS] Cliente desconectado: match_id={match_id} "
                    f"restantes={remaining}")

        if remaining == 0:
            # Limpa o set vazio
            self._clients.pop(match_id, None)
            # Cancela o task de polling
            task = self._tasks.pop(match_id, None)
            if task and not task.done():
                task.cancel()
                logger.info(f"[WS] Background task cancelado para match_id={match_id}")

    # ─── Broadcast ──────────────────────────────────────────────────────────

    async def broadcast(self, match_id: str, data: dict) -> None:
        """Envia JSON para todos os clientes de um match. Remove clientes mortos."""
        clients = self._clients.get(match_id, set())
        if not clients:
            return

        payload = json.dumps(data)
        dead: list[WebSocket] = []

        for ws in list(clients):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(match_id, ws)

    # ─── Background Polling Task (Otimizado) ─────────────────────────────────

    async def _polling_task(self, match_id: str) -> None:
        """
        Loop otimizado que roda enquanto há clientes conectados para um match_id.

        Estratégia:
          1. Resolve game_id uma vez via getEventDetails (chamada pesada).
          2. A cada POLL_INTERVAL, busca window + details em paralelo (chamadas leves).
          3. Só faz broadcast quando os dados mudaram (comparação por hash).
          4. Re-resolve game_id a cada GAME_ID_REFRESH_INTERVAL para detectar
             mudanças de mapa em BO3/BO5.
        """
        # Import tardio para evitar circular imports
        from interface.live_service import (
            resolve_active_game_id,
            get_fast_match_telemetry,
        )

        last_hash: str = ""
        cached_game_id: Optional[str] = None
        cycles_since_resolve: int = 0
        resolve_every_n_cycles = max(1, GAME_ID_REFRESH_INTERVAL // POLL_INTERVAL)

        logger.info(f"[WS] Polling task rodando para match_id={match_id} "
                    f"(intervalo={POLL_INTERVAL}s)")

        try:
            while self._clients.get(match_id):
                try:
                    # Re-resolve game_id periodicamente ou na primeira iteração
                    if cached_game_id is None or cycles_since_resolve >= resolve_every_n_cycles:
                        new_game_id = await resolve_active_game_id(match_id)
                        if new_game_id and new_game_id != "unknown":
                            if new_game_id != cached_game_id:
                                logger.info(
                                    f"[WS] game_id resolvido: {cached_game_id} → {new_game_id} "
                                    f"para match_id={match_id}"
                                )
                                cached_game_id = new_game_id
                                last_hash = ""  # Força broadcast no novo game
                        cycles_since_resolve = 0

                    cycles_since_resolve += 1

                    if not cached_game_id or cached_game_id == "unknown":
                        # Ainda não conseguiu resolver, tenta no próximo ciclo
                        await asyncio.sleep(POLL_INTERVAL)
                        continue

                    # Busca telemetria leve (window + details em paralelo)
                    data = await get_fast_match_telemetry(match_id, cached_game_id)

                    if data:
                        # Serializa para string estável e calcula hash
                        serialized = json.dumps(data, sort_keys=True, default=str)
                        current_hash = hashlib.md5(serialized.encode()).hexdigest()

                        if current_hash != last_hash:
                            last_hash = current_hash
                            await self.broadcast(match_id, data)
                            logger.debug(f"[WS] Broadcast enviado para match_id={match_id}")
                        else:
                            logger.debug(f"[WS] Sem mudanças, broadcast ignorado para match_id={match_id}")

                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"[WS] Erro no polling de match_id={match_id}: {e}")

                await asyncio.sleep(POLL_INTERVAL)

        except asyncio.CancelledError:
            logger.info(f"[WS] Polling task cancelado para match_id={match_id}")
        finally:
            logger.info(f"[WS] Polling task encerrado para match_id={match_id}")


# Singleton global — importado em api.py
manager = ConnectionManager()
