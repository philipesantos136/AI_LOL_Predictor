"""
health_monitor.py
Monitor de saúde da API do LoL Esports.

Verifica periodicamente a disponibilidade da API, rastreia falhas consecutivas
e expõe o status atual via get_status(). Usa threading para monitoramento
em background sem bloquear a aplicação principal.
"""

from typing import Optional
from dataclasses import dataclass
from datetime import datetime
import threading
import time
import requests
import logging


@dataclass
class HealthStatus:
    """Status de saúde da API."""
    is_healthy: bool
    last_check: datetime
    consecutive_failures: int
    last_error: Optional[str] = None
    response_time_ms: Optional[float] = None


class HealthMonitor:
    """Monitor de saúde da API externa."""

    def __init__(
        self,
        check_url: str,
        check_interval: int = 60,
        failure_threshold: int = 3,
        logger: logging.Logger = None,
        headers: dict = None
    ):
        """
        Inicializa o monitor de saúde.

        Args:
            check_url: URL para health check (endpoint getLive)
            check_interval: Intervalo entre checks em segundos (padrão: 60)
            failure_threshold: Número de falhas consecutivas para marcar unhealthy (padrão: 3)
            logger: Logger para registrar operações (cria novo se None)
            headers: Headers HTTP opcionais para a requisição de health check
        """
        self.check_url = check_url
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.headers = headers or {}
        self.logger = logger or logging.getLogger(__name__)

        self._status = HealthStatus(
            is_healthy=True,
            last_check=datetime.now(),
            consecutive_failures=0
        )
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Inicia monitoramento em thread separada."""
        if self._thread is not None and self._thread.is_alive():
            self.logger.warning("Health monitor já está em execução")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._monitoring_loop,
            name="health-monitor",
            daemon=True
        )
        self._thread.start()
        self.logger.info(
            f"Health monitor iniciado (intervalo: {self.check_interval}s, "
            f"threshold: {self.failure_threshold} falhas)"
        )

    def stop(self) -> None:
        """Para o monitoramento gracefully."""
        if self._thread is None or not self._thread.is_alive():
            return

        self._stop_event.set()
        self._thread.join(timeout=self.check_interval + 5)

        if self._thread.is_alive():
            self.logger.warning("Health monitor não finalizou dentro do timeout")
        else:
            self.logger.info("Health monitor parado")

        self._thread = None

    def get_status(self) -> HealthStatus:
        """
        Retorna status atual de saúde.

        Returns:
            HealthStatus com is_healthy, last_check, consecutive_failures,
            last_error e response_time_ms
        """
        with self._lock:
            return HealthStatus(
                is_healthy=self._status.is_healthy,
                last_check=self._status.last_check,
                consecutive_failures=self._status.consecutive_failures,
                last_error=self._status.last_error,
                response_time_ms=self._status.response_time_ms
            )

    def _check_health(self) -> bool:
        """
        Executa check de saúde fazendo requisição leve ao endpoint getLive.

        Atualiza o status interno com resultado do check, incluindo
        tempo de resposta e mensagem de erro se houver.

        Returns:
            True se a API está healthy, False caso contrário
        """
        start_time = time.time()
        error_msg: Optional[str] = None
        response_time_ms: Optional[float] = None

        try:
            response = requests.get(self.check_url, headers=self.headers, timeout=10)
            response_time_ms = (time.time() - start_time) * 1000

            if 200 <= response.status_code < 300:
                # Sucesso: reseta falhas e marca healthy
                with self._lock:
                    was_unhealthy = not self._status.is_healthy
                    self._status = HealthStatus(
                        is_healthy=True,
                        last_check=datetime.now(),
                        consecutive_failures=0,
                        last_error=None,
                        response_time_ms=round(response_time_ms, 2)
                    )

                if was_unhealthy:
                    self.logger.info(
                        f"API recuperada - status voltou para healthy "
                        f"(tempo de resposta: {response_time_ms:.1f}ms)"
                    )
                else:
                    self.logger.debug(
                        f"Health check OK - {response_time_ms:.1f}ms"
                    )
                return True
            else:
                error_msg = f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = "Timeout na requisição de health check"
            self.logger.warning(error_msg)

        except requests.exceptions.ConnectionError as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Erro de conexão: {str(e)}"
            self.logger.warning(f"Health check falhou - {error_msg}")

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Erro inesperado: {str(e)}"
            self.logger.error(f"Health check erro inesperado: {error_msg}", exc_info=True)

        # Falha: incrementa contador
        with self._lock:
            new_failures = self._status.consecutive_failures + 1
            was_healthy = self._status.is_healthy
            became_unhealthy = was_healthy and new_failures >= self.failure_threshold

            self._status = HealthStatus(
                is_healthy=new_failures < self.failure_threshold,
                last_check=datetime.now(),
                consecutive_failures=new_failures,
                last_error=error_msg,
                response_time_ms=round(response_time_ms, 2) if response_time_ms is not None else None
            )

        if became_unhealthy:
            self.logger.error(
                f"ALERTA: API marcada como unhealthy após {new_failures} falhas consecutivas. "
                f"Último erro: {error_msg}"
            )
        else:
            self.logger.warning(
                f"Health check falhou ({new_failures}/{self.failure_threshold}): {error_msg}"
            )

        return False

    def _monitoring_loop(self) -> None:
        """Loop principal de monitoramento (executa em thread separada)."""
        self.logger.debug("Loop de monitoramento iniciado")

        while not self._stop_event.is_set():
            try:
                self._check_health()
            except Exception as e:
                self.logger.error(
                    f"Erro não tratado no loop de monitoramento: {e}",
                    exc_info=True
                )

            # Aguarda o intervalo ou até receber sinal de parada
            self._stop_event.wait(timeout=self.check_interval)

        self.logger.debug("Loop de monitoramento finalizado")
