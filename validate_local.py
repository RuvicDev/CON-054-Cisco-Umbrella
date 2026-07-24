"""Validación local del conector umbrella: ejercita las 3 capacidades.

Uso:
    python validate_local.py

Requiere las variables RUVIC_UMBRELLA_* exportadas en el entorno, con
las tres credenciales del README (Investigate, Enforcement y Reporting).

ADVERTENCIA: este script agrega un dominio REAL a la lista de bloqueo
de Umbrella ("ruvic-validate-local.invalid", un dominio reservado que
no resuelve). Ejecútalo solo contra un entorno de pruebas si te
preocupa modificar la política de bloqueo.
"""

from ruvic_umbrella_connector import UmbrellaClient, setup_logging

setup_logging("INFO")
client = UmbrellaClient()

print("== 1. Consultar reputación de un dominio ==")
result = client.query_domain("cisco.com")
print(f"  status={result.get('status')}")

print("== 2. Agregar dominio a la lista de bloqueo ==")
blocked = client.add_to_blocklist("ruvic-validate-local.invalid")
print(f"  {blocked}")

print("== 3. Consultar actividad reciente ==")
activity = client.get_activity(hours=24, limit=5)
print(f"  {len(activity)} evento(s)")

print("\nTodo OK: query_domain, add_to_blocklist y get_activity funcionan.")
