---
name: umbrella
description: >
  Usa la librería ruvic_umbrella_connector para seguridad DNS y
  filtrado web con Cisco Umbrella - consultar la reputación de un
  dominio (query_domain), agregar un dominio a la lista de bloqueo
  (add_to_blocklist), y consultar la actividad DNS/web reciente
  (get_activity). Úsala cuando el usuario pida investigar un dominio,
  bloquearlo o revisar actividad reciente de la red.
triggers:
- cisco umbrella
- umbrella
- dns
- filtrado web
- lista de bloqueo
- reputacion de dominio
---

# Conector Cisco Umbrella (ruvic_umbrella_connector)

Librería Python de seguridad DNS y filtrado web para Cisco Umbrella.
Está **preinstalada en el runtime** cuando el conector está configurado
(si no, instálala con `pip install git+https://github.com/Dgirto/Cisco-Umbrella.git#subdirectory=lib`).

## Regla crítica de credenciales

El código generado **NUNCA hardcodea credenciales**. Siempre se leen de
variables de entorno, disponibles cuando el conector `umbrella` está
configurado:

| Variable | Contenido |
|----------|-----------|
| `RUVIC_UMBRELLA_INVESTIGATE_API_KEY` | Token de la Investigate API |
| `RUVIC_UMBRELLA_ENFORCEMENT_CUSTOMER_KEY` | Customer Key de la Enforcement API |
| `RUVIC_UMBRELLA_REPORTING_KEY` / `RUVIC_UMBRELLA_REPORTING_SECRET` | Credenciales OAuth2 de la Reporting API v2 |
| `RUVIC_UMBRELLA_ORG_ID` | ID de la organización |

Si estas variables NO existen, el conector no está configurado: no
generes código que lo use; indica al usuario que lo configure en
**Settings → Conectores**.

## Este conector combina lectura y escritura

`query_domain` y `get_activity` son de solo lectura. `add_to_blocklist`
**SÍ escribe**: modifica la política de bloqueo real de la
organización. Confirma con el usuario antes de bloquear un dominio si
la acción no fue explícitamente solicitada.

## Conexión (siempre igual)

```python
from ruvic_umbrella_connector import UmbrellaClient

client = UmbrellaClient()  # lee RUVIC_UMBRELLA_* del entorno automáticamente
```

## Capacidad 1 — Consultar reputación de un dominio

```python
resultado = client.query_domain("evil-example.com")
# resultado["status"]: -1 malicioso, 0 desconocido, 1 benigno
```

## Capacidad 2 — Agregar un dominio a la lista de bloqueo

```python
client.add_to_blocklist("evil-example.com")
```

## Capacidad 3 — Consultar actividad reciente

```python
eventos = client.get_activity(hours=24, limit=50)
```

## Manejo de errores

```python
from ruvic_umbrella_connector import (
    UmbrellaAuthError, UmbrellaDataError, UmbrellaNetworkError,
)

try:
    client.add_to_blocklist("evil-example.com")
except UmbrellaAuthError:
    print("Credenciales inválidas o sin permiso suficiente")
except UmbrellaNetworkError:
    print("No se pudo alcanzar Cisco Umbrella — reintenta en unos segundos")
except UmbrellaDataError as e:
    print(f"Error de datos: {e}")
```

## Buenas prácticas al generar código

1. Lee credenciales SOLO de las variables `RUVIC_UMBRELLA_*` (el constructor de `UmbrellaClient` ya lo hace).
2. Nunca imprimas ninguna de las credenciales en logs ni en la salida.
3. `add_to_blocklist` modifica la política real de la organización: no lo llames sin que el usuario lo haya pedido explícitamente.
4. Antes de bloquear un dominio, si el usuario no lo pidió explícitamente, considera primero llamar a `query_domain` y mostrarle el resultado para confirmar.
5. `get_activity` acepta una ventana relativa en horas, no fechas absolutas — ajusta `hours` según lo que pida el usuario ("última hora" → `hours=1`).
