"""Excepciones propias del conector Cisco Umbrella.

Separan los tres tipos de fallo que el usuario debe distinguir:
autenticación, red/servidor y datos. Nunca exponemos excepciones
crípticas del cliente HTTP subyacente.
"""


class UmbrellaConnectorError(Exception):
    """Error base del conector."""


class UmbrellaAuthError(UmbrellaConnectorError):
    """Credenciales inválidas o permisos insuficientes."""


class UmbrellaNetworkError(UmbrellaConnectorError):
    """No se pudo alcanzar la API de Cisco Umbrella (red/timeout)."""


class UmbrellaDataError(UmbrellaConnectorError):
    """La operación es válida pero el dominio/parámetro es inválido."""
