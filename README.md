# Conector Cisco Umbrella (CON-054)

Conector Ruvic de seguridad DNS y filtrado web para Cisco Umbrella.
Permite consultar la reputación/categorización de un dominio, agregar
un dominio a la lista de bloqueo, y consultar la actividad DNS/web
reciente de la organización.

## Instalación

```bash
pip install git+https://github.com/Dgirto/Cisco-Umbrella.git#subdirectory=lib
```

Python 3.10+. Dependencia única: `requests>=2.31,<3.0`.

## Tres APIs, tres credenciales

Cisco Umbrella no tiene una única API unificada: cada capacidad de este
conector usa una API distinta con sus propias credenciales.

| Capacidad | API de Cisco Umbrella | Credencial |
|-----------|------------------------|------------|
| `query_domain` | Investigate API | Investigate API Key (Bearer token) |
| `add_to_blocklist` | Enforcement API | Enforcement Customer Key |
| `get_activity` | Reporting API v2 | Reporting Key + Secret (OAuth2 client credentials) |

### Investigate API Key

**Admin → API Keys → Umbrella Investigate → Create**. Es de solo
lectura: solo permite consultar reputación y categorización.

### Enforcement Customer Key

**Policies → Security Settings → Integrations → Enforcement API →
Enable**. Permite agregar destinos a la lista de bloqueo, pero no
administra políticas ni usuarios.

### Reporting API Key/Secret

**Admin → API Keys → Umbrella Reporting/Management → Create** con el
rol de acceso **Read-Only Reporting** (no uses un rol con permisos de
administración de la organización). Genera un par Key/Secret usado
para obtener un access token OAuth2 (`client_credentials`).

### Organization ID

Visible en **Admin → Account Settings** o en la URL del dashboard
(`/o/<org_id>/`).

## Variables de entorno (`RUVIC_UMBRELLA_*`)

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `RUVIC_UMBRELLA_INVESTIGATE_API_KEY` | Sí | Token de la Investigate API |
| `RUVIC_UMBRELLA_ENFORCEMENT_CUSTOMER_KEY` | Sí | Customer Key de la Enforcement API |
| `RUVIC_UMBRELLA_REPORTING_KEY` | Sí | Key de la Reporting API v2 |
| `RUVIC_UMBRELLA_REPORTING_SECRET` | Sí | Secret de la Reporting API v2 |
| `RUVIC_UMBRELLA_ORG_ID` | Sí | ID de la organización |
| `RUVIC_UMBRELLA_CONNECT_TIMEOUT` | No (default `15`) | Timeout de conexión en segundos |

## Pruebas locales

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ./lib

export RUVIC_UMBRELLA_INVESTIGATE_API_KEY=tu-investigate-key
export RUVIC_UMBRELLA_ENFORCEMENT_CUSTOMER_KEY=tu-enforcement-key
export RUVIC_UMBRELLA_REPORTING_KEY=tu-reporting-key
export RUVIC_UMBRELLA_REPORTING_SECRET=tu-reporting-secret
export RUVIC_UMBRELLA_ORG_ID=tu-org-id

python test_connection.py
python validate_local.py
```

Prueba también los casos de error (credenciales inválidas, dominio
vacío, ventana de tiempo inválida) y verifica que los mensajes sean
claros.

## Notas de integración

- `query_domain` y `get_activity` son de **solo lectura**.
  `add_to_blocklist` **SÍ escribe**: agrega un destino real a la
  política de bloqueo de la organización. Confirma con el usuario
  antes de bloquear un dominio si no lo pidió explícitamente.
- `query_domain` retorna `status`: `-1` (malicioso conocido), `0`
  (desconocido/no categorizado), `1` (benigno).
- El access token de la Reporting API se cachea en memoria durante la
  vida del proceso y se renueva automáticamente 30 segundos antes de
  expirar; no hace falta gestionarlo manualmente.
- `get_activity` consulta por ventana de tiempo relativa (`hours`
  hacia atrás desde ahora), no por fechas absolutas.
