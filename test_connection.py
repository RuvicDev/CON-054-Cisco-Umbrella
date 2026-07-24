"""Prueba de conexión estándar del conector umbrella.

Firma estándar Ruvic: def test_connection() -> tuple[bool, str]
- Lee la configuración EXCLUSIVAMENTE de las env vars RUVIC_UMBRELLA_*.
- Nunca lanza excepciones; retorna (ok, mensaje).

Ejecutable también como script para pruebas locales:
    python test_connection.py
"""

from __future__ import annotations


def test_connection() -> tuple[bool, str]:
    """Conecta a la Investigate API de Cisco Umbrella y consulta un
    dominio de referencia usando las env vars RUVIC_UMBRELLA_*."""
    try:
        from ruvic_umbrella_connector import (
            UmbrellaAuthError,
            UmbrellaClient,
            UmbrellaDataError,
            UmbrellaNetworkError,
        )
    except ImportError:
        return (
            False,
            "La librería ruvic-umbrella-connector no está instalada. "
            "Instala con: pip install git+https://github.com/Dgirto/"
            "Cisco-Umbrella.git#subdirectory=lib",
        )

    try:
        client = UmbrellaClient()  # valida que existan las env vars
    except ValueError as exc:
        return False, str(exc)

    try:
        client.ping()
    except UmbrellaAuthError as exc:
        return False, f"Autenticación fallida: {exc}"
    except UmbrellaNetworkError as exc:
        return False, f"Error de red: {exc}"
    except UmbrellaDataError as exc:
        return False, f"Error de datos: {exc}"
    except Exception as exc:  # red de seguridad: jamás propagar
        return False, f"Error inesperado: {exc}"

    return (
        True,
        f"Conexión exitosa a Cisco Umbrella (org_id={client.config.org_id!r})",
    )


if __name__ == "__main__":
    ok, message = test_connection()
    print(f"{'OK' if ok else 'FALLO'}: {message}")
    raise SystemExit(0 if ok else 1)
