"""Cliente de seguridad DNS y filtrado web para Cisco Umbrella.

Cisco Umbrella expone tres APIs independientes, cada una con sus
propias credenciales (ver config.UmbrellaConfig). Este cliente unifica
las tres detrás de una sola interfaz:

- query_domain():  Investigate API — reputación/categorización de un dominio.
- add_to_blocklist(): Enforcement API — agrega un dominio a la lista de bloqueo.
- get_activity():  Reporting API v2 — actividad DNS/web reciente.

Las credenciales SIEMPRE provienen de variables de entorno
RUVIC_UMBRELLA_* (ver config.UmbrellaConfig.from_env). Prohibido
hardcodearlas.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from .config import UmbrellaConfig
from .exceptions import UmbrellaAuthError, UmbrellaDataError, UmbrellaNetworkError
from .logging_utils import get_logger

_INVESTIGATE_BASE = "https://investigate.api.umbrella.com"
_ENFORCEMENT_BASE = "https://s-platform.api.opendns.com/1.0"
_REPORTING_AUTH_URL = "https://api.umbrella.com/auth/v2/token"
_REPORTING_BASE = "https://api.umbrella.com/reports/v2"


class UmbrellaClient:
    """Cliente de seguridad DNS y filtrado web en Cisco Umbrella.

    Args:
        config: configuración de conexión. Si se omite, se lee de las
            variables de entorno RUVIC_UMBRELLA_* (comportamiento
            estándar en el runtime de la plataforma).

    Ejemplo:
        >>> client = UmbrellaClient()  # lee RUVIC_UMBRELLA_* del entorno
        >>> client.query_domain("evil-example.com")
        {'status': -1, 'securityCategories': [...], ...}
    """

    def __init__(self, config: UmbrellaConfig | None = None) -> None:
        self.config = config or UmbrellaConfig.from_env()
        self._logger = get_logger()
        self._reporting_token: str | None = None
        self._reporting_token_expires_at: float = 0.0

    # ------------------------------------------------------------------ #
    # Helper HTTP genérico
    # ------------------------------------------------------------------ #

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        try:
            return requests.request(method, url, timeout=self.config.connect_timeout, **kwargs)
        except requests.exceptions.RequestException as exc:
            raise UmbrellaNetworkError(f"No se pudo alcanzar Cisco Umbrella: {exc}") from exc

    def _raise_for_status(self, response: requests.Response) -> None:
        if response.status_code in (401, 403):
            raise UmbrellaAuthError(
                "Credenciales inválidas o sin permiso suficiente para esta operación."
            )
        if response.status_code >= 400:
            raise UmbrellaDataError(
                f"Cisco Umbrella respondió {response.status_code}: {response.text[:300]}"
            )

    def ping(self) -> bool:
        """Verifica la conexión consultando la categorización de un
        dominio de referencia (cisco.com) vía la Investigate API.

        Returns:
            True si la conexión funciona.

        Raises:
            UmbrellaAuthError / UmbrellaNetworkError / UmbrellaDataError
            según el fallo.
        """
        self.query_domain("cisco.com")
        self._logger.info("Ping exitoso a Cisco Umbrella (Investigate API)")
        return True

    # ------------------------------------------------------------------ #
    # Capacidad 1: consultar reputación/categorización de un dominio
    # ------------------------------------------------------------------ #

    def query_domain(self, domain: str) -> dict[str, Any]:
        """Consulta la reputación y categorización de seguridad de un
        dominio (Investigate API).

        Args:
            domain: dominio a consultar (ej. "evil-example.com").

        Returns:
            Dict con `status` (-1 malicioso, 0 desconocido, 1 benigno) y
            `securityCategories` (lista de categorías de riesgo, si las
            hay).

        Ejemplo:
            >>> client.query_domain("evil-example.com")
            {'status': -1, 'securityCategories': ['Malware'], ...}
        """
        domain = (domain or "").strip().lower()
        if not domain:
            raise UmbrellaDataError("domain no puede estar vacío.")
        response = self._request(
            "GET",
            f"{_INVESTIGATE_BASE}/domains/categorization/{domain}",
            params={"showLabels": "true"},
            headers={"Authorization": f"Bearer {self.config.investigate_api_key}"},
        )
        self._raise_for_status(response)
        data = response.json().get(domain, {})
        self._logger.info("Dominio consultado: %s (status=%s)", domain, data.get("status"))
        return data

    # ------------------------------------------------------------------ #
    # Capacidad 2: agregar dominio a la lista de bloqueo
    # ------------------------------------------------------------------ #

    def add_to_blocklist(self, domain: str) -> dict[str, Any]:
        """Agrega un dominio a la lista de bloqueo (Enforcement API).

        Args:
            domain: dominio a bloquear (ej. "evil-example.com").

        Returns:
            Dict con la respuesta de la Enforcement API (incluye `id`
            del evento de bloqueo creado).

        Ejemplo:
            >>> client.add_to_blocklist("evil-example.com")
            {'id': '...', 'disposition': 'added', ...}
        """
        domain = (domain or "").strip().lower()
        if not domain:
            raise UmbrellaDataError("domain no puede estar vacío.")
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        body = {
            "alertTime": now,
            "deviceId": "ruvic-connector",
            "deviceVersion": "1.0",
            "dstDomain": domain,
            "dstUrl": f"http://{domain}",
            "eventTime": now,
            "protocolVersion": "1.0a",
            "providerName": "Security Platform",
        }
        response = self._request(
            "POST",
            f"{_ENFORCEMENT_BASE}/events",
            params={"customerKey": self.config.enforcement_customer_key},
            json=body,
        )
        self._raise_for_status(response)
        result = response.json() if response.content else {}
        self._logger.info("Dominio agregado a la lista de bloqueo: %s", domain)
        return result

    # ------------------------------------------------------------------ #
    # Capacidad 3: consultar actividad reciente
    # ------------------------------------------------------------------ #

    def _get_reporting_token(self) -> str:
        """Obtiene (y cachea) un access token OAuth2 para la Reporting API v2."""
        if self._reporting_token and time.time() < self._reporting_token_expires_at:
            return self._reporting_token
        response = self._request(
            "POST",
            _REPORTING_AUTH_URL,
            data={"grant_type": "client_credentials"},
            auth=(self.config.reporting_key, self.config.reporting_secret),
        )
        self._raise_for_status(response)
        data = response.json()
        self._reporting_token = data["access_token"]
        self._reporting_token_expires_at = time.time() + int(data.get("expires_in", 3600)) - 30
        return self._reporting_token

    def get_activity(self, hours: int = 24, limit: int = 50) -> list[dict[str, Any]]:
        """Consulta la actividad DNS/web reciente de la organización
        (Reporting API v2).

        Args:
            hours: ventana de tiempo hacia atrás, en horas. Default 24.
            limit: cantidad máxima de eventos a retornar. Default 50.

        Returns:
            Lista de dicts, uno por evento de actividad.

        Ejemplo:
            >>> client.get_activity(hours=1, limit=10)
            [{'timestamp': ..., 'domain': 'evil-example.com', 'verdict': 'Blocked', ...}]
        """
        if hours <= 0:
            raise UmbrellaDataError("hours debe ser mayor a 0.")
        if limit <= 0:
            raise UmbrellaDataError("limit debe ser mayor a 0.")
        token = self._get_reporting_token()
        now_ms = int(time.time() * 1000)
        from_ms = now_ms - hours * 3600 * 1000
        response = self._request(
            "GET",
            f"{_REPORTING_BASE}/organizations/{self.config.org_id}/activity",
            params={"from": from_ms, "to": now_ms, "limit": limit},
            headers={"Authorization": f"Bearer {token}"},
        )
        self._raise_for_status(response)
        events = response.json().get("data", [])
        self._logger.info("Actividad consultada: %d evento(s) en las últimas %dh", len(events), hours)
        return events
