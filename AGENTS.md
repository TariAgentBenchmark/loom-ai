# LoomAI Agent Notes

## Deployment

Use `agents/loom-deploy/SKILL.md` as the source of truth for LoomAI deployment steps, environment mapping, GitHub Actions checks, compose commands, and post-deploy verification.

## Non-Negotiable Rules

- Do not overwrite `.env` unless explicitly asked.
- Keep test deployments tied to `dev`; keep production deployments tied to `main`.
- Before production deployment, verify there are no actively processing tasks; deploy only when the queue is idle unless a forced deploy is explicitly requested.
- In production, only rebuild `backend` and `frontend`; do not recreate or restart `redis`, `nginx`, Safeline containers, PostgreSQL, or other infrastructure containers unless explicitly requested.
- If compose files or deployment scripts changed, make sure the server checkout is synced to the target branch before deployment.
- For risky or paid features, run a focused smoke test only when requested.
