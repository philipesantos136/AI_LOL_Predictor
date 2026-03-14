"""
polling_service.py
Serviço de polling automático para dados ao vivo de partidas.

Gerencia o ciclo de vida do polling em thread daemon separada,
com suporte a pausa/resume e logging detalhado de transições de estado.
"""

from enum import Enum
import threading
import time
import logging
from typing import Optional, Callable, Any


class PollingState(Enum):
    """Estados do polling service."""
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class PollingService:
    """Serviço de polling automático para dados ao vivo."""

    def __init__(
        self,
        fetch_callback: Callable[[], Any],
        interval_seconds: int = 10,
        logger: logging.Logger = None
    ):
        """
        Inicializa o polling service.

        Args:
            fetch_callback: Função a ser chamada periodicamente
            interval_seconds: Intervalo entre chamadas em segundos (padrão: 10)
            logger: Logger para registrar operações (cria novo se None)
        """
        self.fetch_callback = fetch_callback
        self.interval_seconds = interval_seconds
        self.logger = logger or logging.getLogger(__name__)

        self._state = PollingState.IDLE
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially (set = can proceed)

    def start(self) -> None:
        """Inicia o polling em thread daemon separada."""
        with self._lock:
            if self._state == PollingState.ACTIVE:
                self.logger.warning("PollingService já está ativo")
                return
            if self._state == PollingState.STOPPED:
                self.logger.warning("PollingService foi parado; crie uma nova instância para reiniciar")
                return

            self._stop_event.clear()
            self._pause_event.set()
            self._state = PollingState.ACTIVE

        self._thread = threading.Thread(
            target=self._polling_loop,
            name="polling-service",
            daemon=True
        )
        self._thread.start()

        self.logger.info(
            f"PollingService iniciado (intervalo: {self.interval_seconds}s)",
            extra={"polling_state": PollingState.ACTIVE.value}
        )

    def stop(self) -> None:
        """Para o polling gracefully."""
        with self._lock:
            if self._state == PollingState.STOPPED:
                return
            self._state = PollingState.STOPPED

        # Unblock pause if paused so the loop can exit
        self._pause_event.set()
        self._stop_event.set()

        # Avoid joining the thread from within itself (would deadlock)
        current = threading.current_thread()
        if self._thread is not None and self._thread.is_alive() and current is not self._thread:
            self._thread.join(timeout=self.interval_seconds + 5)
            if self._thread.is_alive():
                self.logger.warning("PollingService não finalizou dentro do timeout")

        self._thread = None
        self.logger.info(
            "PollingService parado",
            extra={"polling_state": PollingState.STOPPED.value}
        )

    def pause(self) -> None:
        """Pausa o polling temporariamente."""
        with self._lock:
            if self._state != PollingState.ACTIVE:
                return
            self._state = PollingState.PAUSED

        self._pause_event.clear()  # Block the loop
        self.logger.info(
            "PollingService pausado",
            extra={"polling_state": PollingState.PAUSED.value}
        )

    def resume(self) -> None:
        """Resume o polling pausado."""
        with self._lock:
            if self._state != PollingState.PAUSED:
                return
            self._state = PollingState.ACTIVE

        self._pause_event.set()  # Unblock the loop
        self.logger.info(
            "PollingService resumido",
            extra={"polling_state": PollingState.ACTIVE.value}
        )

    def _polling_loop(self) -> None:
        """Loop principal de polling (executa em thread daemon separada)."""
        self.logger.info(
            "Ciclo de polling iniciado",
            extra={"polling_state": PollingState.ACTIVE.value}
        )

        while not self._stop_event.is_set():
            # Wait if paused (blocks until resumed or stopped)
            self._pause_event.wait()

            if self._stop_event.is_set():
                break

            # Execute the fetch callback
            try:
                self.logger.info(
                    "Iniciando iteração de polling",
                    extra={"polling_state": self._state.value}
                )
                self.fetch_callback()
                self.logger.info(
                    "Iteração de polling concluída",
                    extra={"polling_state": self._state.value}
                )
            except Exception as e:
                self.logger.error(
                    f"Erro durante iteração de polling: {e}",
                    exc_info=True,
                    extra={"polling_state": self._state.value}
                )

            # Wait for the interval or until stopped
            self._stop_event.wait(timeout=self.interval_seconds)

        self.logger.info(
            "Ciclo de polling finalizado",
            extra={"polling_state": PollingState.STOPPED.value}
        )

    def get_state(self) -> PollingState:
        """Retorna estado atual do polling."""
        with self._lock:
            return self._state
