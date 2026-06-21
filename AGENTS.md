# LoomAI Agent Notes

## GitHub Build

- Workflow: `Build and Push Docker Images` in `.github/workflows/docker-build.yml`.
- It runs on pushes and PRs for `main` and `dev`.
- Push to `dev` builds and pushes Docker images tagged `dev`.
- Push to `main` builds and pushes Docker images tagged `latest`.
- Before deploying a fresh push, verify the matching GitHub Actions run completed successfully.

Useful checks:

```bash
gh run list --repo TariAgentBenchmark/loom-ai --branch dev --limit 5
gh run list --repo TariAgentBenchmark/loom-ai --branch main --limit 5
gh run watch <run-id> --repo TariAgentBenchmark/loom-ai --exit-status
```

## Test Environment

- Branch: `dev`
- Image tag: `dev`
- SSH host: `image-gen-202509`
- Remote directory: `~/loom-ai`
- Compose command:

```bash
ssh image-gen-202509
cd ~/loom-ai
docker compose --profile production -f docker-compose.yml -f docker-compose.dev.yml pull
docker compose --profile production -f docker-compose.yml -f docker-compose.dev.yml up -d --force-recreate
docker compose --profile production -f docker-compose.yml -f docker-compose.dev.yml ps
```

## Production Environment

- Branch: `main`
- Image tag: `latest`
- SSH host: `image-gen-202509-3`
- Remote directory: `~/loom-ai`
- Compose command:

```bash
ssh image-gen-202509-3
cd ~/loom-ai
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production pull backend frontend
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d --no-deps backend frontend
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production ps
```

## Rules

- Before deployment, make sure the server checkout is synced to the target branch when compose files or deployment scripts changed.
- Do not overwrite `.env` unless explicitly asked.
- Keep test deployments tied to `dev`; keep production deployments tied to `main`.
- Use the exact compose syntax for each environment.
- In production, only rebuild `backend` and `frontend`; do not recreate or restart `redis`, `nginx`, Safeline containers, PostgreSQL, or any other infrastructure containers unless explicitly requested.
- Before production deployment, verify there are no actively processing tasks; deploy only when the queue is idle unless a forced deploy is explicitly requested.
- After deployment, verify `backend`, `frontend`, and `nginx` are `Up`, and `redis` is healthy.
- For risky or paid features, run a focused smoke test only when requested.
