---
name: loom-deploy
description: Deploy or refresh LoomAI environments on the designated servers by pulling the latest container images and recreating services with the environment-specific compose commands. Use when asked to deploy, update, restart, or verify LoomAI on the dev or production servers. This skill pins `dev` to `image-gen-202509` and `prod` to `image-gen-202509-3`, with fixed rollout commands for each environment.
---

# Loom Deploy

## Overview

Deploy LoomAI with a single project-specific workflow that branches by environment.
Treat both servers as image-based deployment targets: do not `git pull` on the server unless the user explicitly asks.

## Environment Map

- `dev`
  - branch expectation: `dev`
  - SSH alias: `image-gen-202509`
  - remote directory: `~/loom-ai`
  - compose base:

```bash
docker compose --profile production -f docker-compose.yml -f docker-compose.dev.yml
```

- `prod`
  - branch expectation: `main`
  - SSH alias: `image-gen-202509-3`
  - remote directory: `~/loom-ai`
  - compose base:

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production
```

## Standard Workflow

1. Identify whether the user wants `dev` or `prod`.
2. Confirm the relevant GitHub Actions image build has completed successfully when the deployment depends on a fresh push.
3. SSH to the pinned server for that environment.
4. Change directory to `~/loom-ai`.
5. Pull the latest images with the environment-specific compose command.
6. Recreate the stack with `up -d --force-recreate`.
7. Check final service state with `ps`.

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
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production pull
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production up -d --force-recreate
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile production ps
```

## Constraints

- Do not run `git pull` on either server for routine deployments.
- Do not overwrite `.env` unless the user explicitly asks; if the user already changed `.env`, keep it and just recreate containers.
- Keep `dev` pinned to `image-gen-202509` and `prod` pinned to `image-gen-202509-3`.
- Keep `dev` associated with `dev` builds and `prod` associated with `main` builds when discussing rollout expectations.
- Prefer the exact compose command for each environment rather than switching between `docker compose` and `docker-compose`.
- Report final container states after deployment.

## Verification

After deployment, verify at minimum:

- `backend` is `Up`
- `frontend` is `Up`
- `nginx` is `Up`
- `redis` is `Up (healthy)` or `Healthy`

If the user asks for functional verification, perform a focused smoke test for the changed feature after containers are healthy.
