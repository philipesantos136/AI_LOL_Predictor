"""
test_socket_manager.py
Testes unitários para o ConnectionManager do socket_manager.py
Usa IsolatedAsyncioTestCase para compatibilidade com Python 3.10+.

Cobre:
  - connect adiciona WebSocket ao registry
  - connect inicia background task apenas uma vez por match_id
  - disconnect remove WebSocket e cancela task quando set fica vazio
  - disconnect não cancela task se ainda há clientes
  - broadcast envia mensagem para todos os clientes
  - broadcast remove clientes mortos silenciosamente
"""

import asyncio
import json
import sys
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_ws(send_ok: bool = True) -> MagicMock:
    """Cria um mock de WebSocket compatível com o ConnectionManager."""
    ws = MagicMock()
    ws.accept = AsyncMock()
    if send_ok:
        ws.send_text = AsyncMock()
    else:
        ws.send_text = AsyncMock(side_effect=Exception("WebSocket fechado"))
    return ws


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _noop_polling(*args, **kwargs):
    """Substituto de _polling_task que dorme indefinidamente (não bloqueia)."""
    await asyncio.sleep(9999)


# ---------------------------------------------------------------------------
# Tests: connect
# ---------------------------------------------------------------------------

class TestConnectionManagerConnect(unittest.IsolatedAsyncioTestCase):
    """Testa registro de clientes na conexão."""

    def setUp(self):
        from interface.socket_manager import ConnectionManager
        self.manager = ConnectionManager()

    def tearDown(self):
        for task in list(self.manager._tasks.values()):
            task.cancel()

    async def test_connect_adds_client_to_registry(self):
        ws = _make_ws()
        with patch.object(self.manager, '_polling_task', _noop_polling):
            await self.manager.connect("match1", ws)
        self.assertIn("match1", self.manager._clients)
        self.assertIn(ws, self.manager._clients["match1"])

    async def test_connect_multiple_clients_same_match(self):
        ws1, ws2 = _make_ws(), _make_ws()
        with patch.object(self.manager, '_polling_task', _noop_polling):
            await self.manager.connect("match1", ws1)
            await self.manager.connect("match1", ws2)
        self.assertEqual(len(self.manager._clients["match1"]), 2)

    async def test_connect_creates_one_task_per_match(self):
        ws1, ws2 = _make_ws(), _make_ws()
        with patch.object(self.manager, '_polling_task', _noop_polling):
            await self.manager.connect("match1", ws1)
            task_before = self.manager._tasks.get("match1")
            await self.manager.connect("match1", ws2)
            task_after = self.manager._tasks.get("match1")
        # Deve ser a mesma task — não criou uma segunda
        self.assertIs(task_before, task_after)


# ---------------------------------------------------------------------------
# Tests: disconnect
# ---------------------------------------------------------------------------

class TestConnectionManagerDisconnect(unittest.IsolatedAsyncioTestCase):
    """Testa remoção de clientes e cancelamento de tasks."""

    def setUp(self):
        from interface.socket_manager import ConnectionManager
        self.manager = ConnectionManager()

    async def test_disconnect_removes_client_and_clears_registry(self):
        ws = _make_ws()
        with patch.object(self.manager, '_polling_task', _noop_polling):
            await self.manager.connect("match1", ws)
        self.manager.disconnect("match1", ws)
        self.assertNotIn("match1", self.manager._clients)

    async def test_disconnect_cancels_task_when_no_clients_remain(self):
        ws = _make_ws()
        with patch.object(self.manager, '_polling_task', _noop_polling):
            await self.manager.connect("match1", ws)
        task = self.manager._tasks.get("match1")
        self.manager.disconnect("match1", ws)
        # Dá ao event loop um ciclo para processar o cancelamento
        await asyncio.sleep(0)
        self.assertIsNotNone(task)
        self.assertTrue(task.cancelled() or task.done())

    async def test_disconnect_keeps_task_if_other_clients_remain(self):
        ws1, ws2 = _make_ws(), _make_ws()
        with patch.object(self.manager, '_polling_task', _noop_polling):
            await self.manager.connect("match1", ws1)
            await self.manager.connect("match1", ws2)
        task = self.manager._tasks.get("match1")
        self.manager.disconnect("match1", ws1)
        # ws2 ainda conectado → task deve seguir rodando
        self.assertIn("match1", self.manager._tasks)
        self.assertFalse(task.cancelled())


# ---------------------------------------------------------------------------
# Tests: broadcast
# ---------------------------------------------------------------------------

class TestConnectionManagerBroadcast(unittest.IsolatedAsyncioTestCase):
    """Testa envio de mensagens para clientes conectados."""

    def setUp(self):
        from interface.socket_manager import ConnectionManager
        self.manager = ConnectionManager()

    async def test_broadcast_sends_json_to_all_clients(self):
        ws1, ws2 = _make_ws(), _make_ws()
        self.manager._clients["match1"] = {ws1, ws2}
        data = {"blue_gold": 1000, "red_gold": 900}
        await self.manager.broadcast("match1", data)
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()
        payload = json.loads(ws1.send_text.call_args[0][0])
        self.assertEqual(payload["blue_gold"], 1000)

    async def test_broadcast_removes_dead_clients_silently(self):
        ws_ok = _make_ws(send_ok=True)
        ws_dead = _make_ws(send_ok=False)
        self.manager._clients["match1"] = {ws_ok, ws_dead}
        # Não deve levantar exceção
        await self.manager.broadcast("match1", {"data": True})
        self.assertNotIn(ws_dead, self.manager._clients.get("match1", set()))
        self.assertIn(ws_ok, self.manager._clients.get("match1", set()))

    async def test_broadcast_does_nothing_for_unknown_match(self):
        # Não deve lançar exceção para match_id sem clientes
        await self.manager.broadcast("unknown_match", {"data": True})


if __name__ == "__main__":
    unittest.main()
