# docker-compose.yml — Beginner Explanation

> **Source file:** `containers/docker-compose.yml`

---

## 1. What is this file?

`docker-compose.yml` is a configuration file that tells Docker how to start and run multiple services (programs in containers) together with a single command.

In this project it defines two services: **PostgreSQL** (the database) and **Redis** (the cache). Instead of installing and configuring both on your Mac manually, Docker reads this file and starts them automatically, each isolated in its own container.

---

## 2. Why does this file exist?

**The problem:** Every developer who works on this project, and every server it runs on, needs the exact same database and cache setup. If you install PostgreSQL manually, you might get version 14. Someone else might have version 15. The production server might have version 16. Things break when versions differ.

**The solution:** Docker containers. A container is like a sealed box that includes the program and everything it needs. This file tells Docker exactly which box to use, how to configure it, and how to connect it to your computer.

---

## 3. Where does it fit in the project?

```
Your Terminal
     ↓
pnpm docker:up  (defined in root package.json)
     ↓
docker compose -f containers/docker-compose.yml up -d
     ↓
Docker reads this file
     ↓
Starts PostgreSQL container → backend/src/infrastructure/database/client.ts connects to it
Starts Redis container     → backend/src/infrastructure/redis/client.ts connects to it
```

Without these two containers running, the backend server's `/health` endpoint returns `error` for database and Redis.

---

## 4. Technology involved

- **Docker:** A program that runs other programs in isolated containers. Each container has its own filesystem, its own network, its own installed software — completely separate from your Mac.
- **Docker Compose:** A tool built into Docker that lets you define and run multiple containers together using a YAML file.
- **YAML:** A plain-text configuration format that uses indentation (spaces) to show hierarchy. It is what this file is written in.

---

## 5. Line-by-line explanation

### `services:`

```yaml
services:
```

`services` is the top-level key. Everything underneath it describes individual containers. Think of "services" as "programs I want to run."

---

### The `postgres` service

```yaml
  postgres:
    image: postgres:16-alpine
```

**`postgres:`** — This is the name we give this service. We chose "postgres" but we could have called it anything. This name is used to reference this container from other containers.

**`image: postgres:16-alpine`** — The exact pre-built Docker image (a frozen snapshot of a program) to use.
- `postgres` — the official PostgreSQL image from Docker Hub (a public library of images)
- `16` — PostgreSQL major version 16. We pin this so everyone uses the same version
- `alpine` — a variant built on Alpine Linux (a tiny Linux distribution). "Alpine" images are much smaller than regular ones, which speeds up downloading

If you changed `16-alpine` to `15-alpine`, you'd get a different PostgreSQL version. This could break the project if our schema uses features that only exist in version 16.

---

```yaml
    container_name: screener-postgres
```

**`container_name: screener-postgres`** — Gives the running container a fixed, human-readable name instead of a random auto-generated one. This makes it easier to run commands like `docker exec screener-postgres psql -U screener`. Without this, Docker would generate a name like `containers_postgres_1` or something random.

---

```yaml
    environment:
      POSTGRES_USER: screener
      POSTGRES_PASSWORD: screener
      POSTGRES_DB: screener
```

**`environment:`** — Passes environment variables into the container. PostgreSQL reads these when it starts up for the first time to create its initial user and database.

- **`POSTGRES_USER: screener`** — Creates a PostgreSQL user (login) named `screener`. This is the username the backend uses to connect. If you changed this, you'd also need to change `DATABASE_URL` in `.env`.
- **`POSTGRES_PASSWORD: screener`** — Sets the password for the `screener` user to `screener`. In development this is fine since it runs locally. Never use simple passwords in production.
- **`POSTGRES_DB: screener`** — Creates a database named `screener`. This is the container that holds all our tables. The backend's `DATABASE_URL` connects to this specific database.

These three together mean: "When PostgreSQL starts, create a database named `screener`, accessible by user `screener` with password `screener`."

---

```yaml
    ports:
      - "5433:5432"
```

**`ports:`** — Maps a port on your Mac (host) to a port inside the container.

- The format is `"HOST_PORT:CONTAINER_PORT"`
- `5432` is the port PostgreSQL listens on inside the container (that's its default port)
- `5433` is the port we expose on your Mac

**Why 5433 instead of 5432?**

If you have PostgreSQL installed directly on your Mac via Homebrew (very common), it's already listening on port 5432. Two programs cannot share the same port. So we map Docker's PostgreSQL to host port 5433 to avoid the conflict.

This is why `DATABASE_URL` in `.env.example` ends with `@localhost:5433/screener` — it connects on port 5433 (host), which Docker then routes to port 5432 inside the container.

If you didn't have a local PostgreSQL installation, you could use `"5432:5432"` instead and simplify the URL.

---

```yaml
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

**`volumes:`** — Connects a storage location on your Mac to a path inside the container.

- `/var/lib/postgresql/data` is where PostgreSQL stores all its database files inside the container
- `postgres_data` is a "named volume" — Docker manages this storage on your Mac automatically

**Why this matters:** Containers are ephemeral — when you stop and remove a container, everything inside it disappears. Without this volume, every time you ran `docker:down` you'd lose all your database tables and data. The volume stores the data safely outside the container so it survives restarts.

---

```yaml
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U screener -d screener"]
      interval: 5s
      timeout: 5s
      retries: 5
```

**`healthcheck:`** — Tells Docker how to check if PostgreSQL is actually ready to accept connections (not just started).

- **`test:`** — The command Docker runs to check health. `pg_isready` is a PostgreSQL tool that checks if the server is accepting connections. `-U screener` checks for the `screener` user, `-d screener` checks the `screener` database.
- **`interval: 5s`** — Check every 5 seconds
- **`timeout: 5s`** — If the check takes longer than 5 seconds, consider it failed
- **`retries: 5`** — After 5 consecutive failures, mark the container as "unhealthy"

Without this, other services (or your scripts) might try to connect before PostgreSQL has finished starting up, causing "connection refused" errors.

---

### The `redis` service

```yaml
  redis:
    image: redis:7-alpine
    container_name: screener-redis
```

Same pattern as postgres: uses the official Redis image, version 7, Alpine variant, with a fixed container name.

---

```yaml
    command: redis-server --save 60 1 --loglevel warning
```

**`command:`** — Overrides the default command that runs when the container starts.

Without `command:`, Redis starts with its default settings (no persistence). We add flags:

- **`--save 60 1`** — Save a snapshot to disk every 60 seconds if at least 1 key has changed. This is Redis's RDB persistence — it writes the in-memory data to a file so it survives restarts.
- **`--loglevel warning`** — Only log warnings and above. Redis without this logs every single operation, which is very noisy during development.

---

```yaml
    ports:
      - "6379:6379"
```

Redis's default port is 6379 and we have no conflict here (unlike PostgreSQL), so we map it 1:1.

---

```yaml
    volumes:
      - redis_data:/data
```

`/data` is where Redis writes its snapshot files inside the container. The `redis_data` named volume keeps these across restarts, so cached data from development sessions is preserved.

---

```yaml
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

- **`redis-cli ping`** — The official Redis health check. Redis responds with `PONG` if it's healthy. Our backend's `checkRedisHealth()` does the same thing.
- The shorter `timeout: 3s` is fine because Redis responds almost instantly.

---

### The `volumes` section at the bottom

```yaml
volumes:
  postgres_data:
  redis_data:
```

This declares the two named volumes used above. Without declaring them here, Docker would refuse to start because the volumes would be referenced but not defined.

Named volumes are managed by Docker — you can see them with `docker volume ls`. Docker stores them somewhere on your Mac's filesystem under its own directory. You don't need to know the exact path.

To delete the data (reset the database completely): `docker volume rm screener_postgres_data`.

---

## 6. How it works

```
pnpm docker:up
      ↓
docker compose -f containers/docker-compose.yml up -d
      ↓
Docker reads this file
      ↓
Pulls postgres:16-alpine and redis:7-alpine from Docker Hub (first time only)
      ↓
Creates containers with the names screener-postgres and screener-redis
      ↓
Mounts the postgres_data and redis_data volumes
      ↓
Passes environment variables to postgres
      ↓
Starts both containers in the background (-d = detached)
      ↓
PostgreSQL listens on host port 5433, Redis on 6379
      ↓
backend/src/infrastructure/database/client.ts connects to postgres on 5433
backend/src/infrastructure/redis/client.ts connects to redis on 6379
```

---

## 7. Dependencies

| This file depends on | Why |
|---------------------|-----|
| Docker being installed | Docker must be running on your Mac |
| `postgres:16-alpine` image | Downloaded from Docker Hub automatically |
| `redis:7-alpine` image | Downloaded from Docker Hub automatically |

| What depends on this file | Why |
|--------------------------|-----|
| `backend/src/infrastructure/database/client.ts` | Connects to the postgres container |
| `backend/src/infrastructure/redis/client.ts` | Connects to the redis container |
| `backend/.env` / `.env.example` | DATABASE_URL and REDIS_URL point to these containers |
| Root `package.json` scripts | `docker:up`, `docker:down`, `docker:logs` reference this file |

---

## 8. What happens if I change or remove something?

| Change | Consequence |
|--------|-------------|
| Remove `postgres` service | Backend cannot connect to database, health check fails |
| Change `POSTGRES_USER` | `DATABASE_URL` must match, or backend gets "role does not exist" error |
| Change `"5433:5432"` to `"5432:5432"` | Works if no local PostgreSQL is installed; conflicts if there is |
| Remove volumes section | Data is lost every time containers restart |
| Change `redis` service name | No impact unless scripts reference the container name directly |
| Remove healthcheck | Containers still work, but Docker won't mark them as healthy/unhealthy |

---

## 9. Beginner concepts to learn

- **What is Docker?** — A system for running programs in isolated containers
- **What is a container?** — A running instance of an image
- **What is an image?** — A frozen snapshot of a program + its operating system
- **What is a port?** — A numbered "door" on a computer. Programs listen on ports. Clients connect to ports.
- **What is a volume?** — Persistent storage that survives container restarts
- **What is YAML?** — A file format using indentation to show hierarchy (like JSON but more readable)

---

## 10. Simple mental model

Think of this file like a **recipe for a kitchen setup**:

- "I need two appliances in my kitchen: a refrigerator and a microwave."
- "The fridge should be a Samsung model 2024, hold food at exactly 4°C, and the food should be saved even if unplugged."
- "The microwave should be a LG model 2023, connected to socket number 6 on the wall."

Docker reads this recipe and sets up both appliances. You don't have to go buy, install, or configure them individually — Docker handles it from the recipe.
