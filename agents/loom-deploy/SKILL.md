---
name: loom-deploy
description: Deploy or refresh LoomAI environments on the designated servers by pulling container images and recreating only the intended services with the environment-specific compose commands. Use when asked to deploy, update, restart, or verify LoomAI on the dev or production servers. This skill pins `dev` to `image-gen-202509` and `prod` to `image-gen-202509-3`; production deploys are limited to backend and frontend unless explicitly requested otherwise.
---

# Loom Deploy

## Overview

Deploy LoomAI with a single project-specific workflow that branches by environment.
Treat routine deployments as image-based rollouts: do not `git pull` on the server unless the user explicitly asks. If compose files or deployment scripts changed, make sure the server checkout is synced to the target branch before running compose commands.

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

## Environment Map

- `dev`
  - branch expectation: `dev`
  - image tag: `dev`
  - SSH alias: `image-gen-202509`
  - remote directory: `~/loom-ai`
  - compose base:

```bash
docker compose --profile production -f docker-compose.yml -f docker-compose.dev.yml
```

- `prod`
  - branch expectation: `main`
  - image tag: `latest`
  - SSH alias: `image-gen-202509-3`
  - remote directory: `~/loom-ai`
  - compose base:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production
```

## Standard Workflow

1. Identify whether the user wants `dev` or `prod`.
2. Confirm the relevant GitHub Actions image build has completed successfully when the deployment depends on a fresh push.
3. For `prod`, verify there are no actively processing tasks and deploy only when the queue is idle unless the user explicitly forces deployment.
4. If compose files or deployment scripts changed, ensure the server checkout is synced to the target branch before deployment.
5. SSH to the pinned server for that environment.
6. Change directory to `~/loom-ai`.
7. Pull the latest images with the environment-specific compose command.
8. Recreate services with the environment-specific command: full recreate for `dev`; `backend frontend` only with `--no-deps` for `prod`.
9. Check final service state with `ps`.

## Commands

### Dev

Run these commands exactly for `dev` unless the user explicitly asks for a different flow:

```bash
ssh image-gen-202509
cd ~/loom-ai
docker compose --profile production -f docker-compose.yml -f docker-compose.dev.yml pull
docker compose --profile production -f docker-compose.yml -f docker-compose.dev.yml up -d --force-recreate
docker compose --profile production -f docker-compose.yml -f docker-compose.dev.yml ps
```

### Prod

Run these commands exactly for `prod` unless the user explicitly asks for a different flow:

```bash
ssh image-gen-202509-3
cd ~/loom-ai
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production pull backend frontend
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d --no-deps backend frontend
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production ps
```

## Constraints

- Do not run `git pull` on either server for routine deployments. If compose files or deployment scripts changed, explicitly ensure the server checkout is synced to the target branch before deploying.
- Do not overwrite `.env` unless the user explicitly asks; if the user already changed `.env`, keep it and just recreate containers.
- Keep `dev` pinned to `image-gen-202509` and `prod` pinned to `image-gen-202509-3`.
- Keep `dev` associated with `dev` builds and `prod` associated with `main` builds when discussing rollout expectations.
- For production, only pull/recreate `backend` and `frontend`; do not recreate or restart `redis`, `nginx`, Safeline containers, PostgreSQL, or other infrastructure containers unless explicitly requested.
- For production, verify the queue is idle before deployment unless the user explicitly forces deployment.
- Prefer the exact compose command for each environment rather than switching between `docker compose` and `docker-compose`.
- Report final container states after deployment.

## Verification

After deployment, verify at minimum:

- `backend` is `Up`
- `frontend` is `Up`
- `nginx` is `Up`
- `redis` is `Up (healthy)` or `Healthy`

If the user asks for functional verification, perform a focused smoke test for the changed feature after containers are healthy.
