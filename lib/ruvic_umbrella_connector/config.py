"""Configuración del conector leída desde variables de entorno.

Convención de la plataforma: cada campo del formulario de configuración
llega como variable de entorno {ENV_PREFIX}{CAMPO} en mayúsculas.
Para este conector el prefijo es RUVIC_UMBRELLA_.

Cisco Umbrella expone tres APIs con credenciales independientes, cada
una necesaria para una de las tres capacidades del conector:
- Investigate API (investigate_api_key): consultar reputación de dominio.
- Enforcement API (enforcement_customer_key): agregar dominio a la lista de bloqueo.
- Reporting API v2 (reporting_key/reporting_secret + org_id): consultar actividad.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

ENV_PREFIX = "RUVIC_UMBRELLA_"


@dataclass(frozen=True)
class UmbrellaConfig:
    """Parámetros de conexión a las APIs de Cisco Umbrella."""

    investigate_api_key: str
    enforcement_customer_key: str
    reporting_key: str
    reporting_secret: str
    org_id: str
    connect_timeout: int = 15

    @classmethod
    def from_env(cls) -> UmbrellaConfig:
        """Construye la configuración desde las variables RUVIC_UMBRELLA_*.

        Raises:
            ValueError: si falta alguna variable obligatoria.

        Ejemplo:
            >>> config = UmbrellaConfig.from_env()
            >>> config.org_id
            '123456'
        """
        missing = [
            f"{ENV_PREFIX}{name}"
            for name in (
                "INVESTIGATE_API_KEY",
                "ENFORCEMENT_CUSTOMER_KEY",
                "REPORTING_KEY",
                "REPORTING_SECRET",
                "ORG_ID",
            )
            if not os.environ.get(f"{ENV_PREFIX}{name}")
        ]
        if missing:
            raise ValueError(
                "Faltan variables de entorno del conector umbrella: "
                + ", ".join(missing)
                + ". Configura el conector en Settings → Conectores."
            )
        return cls(
            investigate_api_key=os.environ[f"{ENV_PREFIX}INVESTIGATE_API_KEY"],
            enforcement_customer_key=os.environ[f"{ENV_PREFIX}ENFORCEMENT_CUSTOMER_KEY"],
            reporting_key=os.environ[f"{ENV_PREFIX}REPORTING_KEY"],
            reporting_secret=os.environ[f"{ENV_PREFIX}REPORTING_SECRET"],
            org_id=os.environ[f"{ENV_PREFIX}ORG_ID"],
            connect_timeout=int(os.environ.get(f"{ENV_PREFIX}CONNECT_TIMEOUT", "15")),
        )
