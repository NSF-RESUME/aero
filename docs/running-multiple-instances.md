# Running two aero-server instances on one host

How to run a second, independent aero-server deployment on the same machine and reach
either one. File links below are relative to this file's location (`docs/`).

## Current architecture (what one stack looks like)

From [docker-compose.yml](../docker-compose.yml), one deployment is four services on a
single Compose-created network:

| Service | Image / build | Host-published ports | Internal port | Notes |
|---|---|---|---|---|
| `web` | `Dockerfile.server.dev` | **none** | `8081` (uvicorn) | mounts `./aero`, `./data`; talks to `database` |
| `nginx` | `nginx` | **80, 443** | 80 | proxies `/` → `web:8081`, `/adminer` → `adminer:8080` |
| `database` | `postgres:17.4` | **5432** | 5432 | volume `osprey-postgres-data` (`external: true`) |
| `adminer` | `adminer` | **8080** | 8080 | DB web UI |

Key facts that determine how to run a second copy:

1. **Service-to-service traffic uses service names on a per-project network.** `nginx`
   reaches the app as `web:8081`, and the app reaches Postgres as `database` (via
   `DATABASE_HOST`, see [aero/config.py:18](../aero/config.py#L18)). Each Compose *project*
   gets its own isolated network, so these names never collide between stacks — **no nginx
   upstream or DB-host changes are needed** for a second instance.
2. **Container and network names are namespaced by the Compose project name**
   (`-p` / `COMPOSE_PROJECT_NAME`). Two different project names ⇒ no container-name clashes
   automatically.
3. **Only two things actually collide between two stacks:**
   - **Host-published ports** — 80, 443, 5432, 8080 can each be bound by only one stack.
   - **The Postgres volume** — `osprey-postgres-data` is declared `external: true`, so *both*
     stacks would mount the **same** volume and stomp on each other's database. The second
     instance needs its own volume.

## The core idea

Docker Compose isolates almost everything by **project name**. So running a second instance
is really just: pick a second project name, remap the host ports that are published, and give
it a separate Postgres volume. Everything internal (service DNS, the `web:8081` upstream)
keeps working unchanged.

## Gotcha: don't use a naive override file for the ports

Compose **concatenates** (does not replace) list-valued fields like `ports` and `volumes`
when you layer `-f base.yml -f override.yml`. So an override that adds `"8090:80"` leaves the
original `"80:80"` in place and you still get a conflict. Because of that, prefer **one of
these two** approaches instead of a partial override.

## Recommended approach — parameterize ports + volume, run twice

Make the published ports and the DB volume name variables in `docker-compose.yml`:

```yaml
  nginx:
    ports:
      - "${HTTP_PORT:-80}:80"
      - "${HTTPS_PORT:-443}:443"

  database:
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  adminer:
    ports:
      - "${ADMINER_PORT:-8080}:8080"

volumes:
  pgdata:
    external: true
    name: ${PG_VOLUME:-osprey-postgres-data}
```

Note the `name:` field on the volume — that's how you keep it `external` while letting the
*actual* volume name vary per instance (the top-level key `pgdata` stays static, which
Compose requires).

Then two env files (used only for compose-variable interpolation):

`.env.instance1`
```
HTTP_PORT=80
HTTPS_PORT=443
DB_PORT=5432
ADMINER_PORT=8080
PG_VOLUME=osprey-postgres-data
```

`.env.instance2`
```
HTTP_PORT=8090
HTTPS_PORT=8443
DB_PORT=5433
ADMINER_PORT=8091
PG_VOLUME=osprey-postgres-data-2
```

Create the second external volume once, then bring both up with distinct project names:

```bash
docker volume create osprey-postgres-data      # if it doesn't already exist
docker volume create osprey-postgres-data-2

docker compose -p aero1 --env-file .env.instance1 up -d
docker compose -p aero2 --env-file .env.instance2 up -d
```

## Alternative approach — duplicate the compose file

If you'd rather not template it, copy `docker-compose.yml` to `docker-compose.instance2.yml`,
hard-code the remapped ports (8090/8443/5433/8091) and a second volume, and run:

```bash
docker compose -p aero1 up -d
docker compose -p aero2 -f docker-compose.instance2.yml up -d
```

Same result; more duplication, but no interpolation to reason about.

## How you reach each instance

| | Instance 1 (`aero1`) | Instance 2 (`aero2`) |
|---|---|---|
| API (via nginx) | `http://<host>/` | `http://<host>:8090/` |
| Adminer (via nginx) | `http://<host>/adminer` | `http://<host>:8090/adminer` |
| Adminer (direct) | `http://<host>:8080` | `http://<host>:8091` |
| Postgres (host) | `<host>:5432` | `<host>:5433` |

The nginx `server_name aero.cels.anl.gov;` in [nginx/aero-app.conf](../nginx/aero-app.conf)
doesn't filter here — it's the only/default server block — so **port-based access works
without DNS**.

### Optional: one hostname per instance instead of ports

If you want `aero1.example.org` and `aero2.example.org` on port 80 instead of different ports,
put a **single front reverse proxy** in front (its own container on :80/:443) that routes by
`Host:` header to each stack's nginx (e.g. `aero1-nginx:80` / `aero2-nginx:80`) over a shared
external Docker network. That's more moving parts than the port approach — only worth it if
you need clean public hostnames/TLS per instance.

## Important application-level caveat (beyond Docker)

Port/volume isolation gives you two independent servers + databases, but both `web` services
currently load the **same app env** (`env_file: scripts/setup_env.sh`, which also drives
Globus/GCS). If both instances share:

- `SEARCH_INDEX` → they write to the **same Globus Search index**,
- the GCS mapped-collection / storage-gateway IDs → they share the **same data collection**,
- `GLOBUS_WORKER_UUID` / client credentials → shared identity,

then the two servers aren't truly independent at the data layer even though the Postgres DBs
are separate. For genuine isolation, give instance 2 its **own app env file** with a distinct
`SEARCH_INDEX`, GCS collection, and worker identity, and point its `web` service at that file.

> Side note: `env_file` points at `scripts/setup_env.sh`, which isn't present in the repo
> right now (only `test_env.sh` exists, and it sets `DATABASE_HOST=127.0.0.1` — which would be
> wrong inside Compose, where it should be the service name `database`). You'll want a real
> per-instance env file with `DATABASE_HOST=database`.
