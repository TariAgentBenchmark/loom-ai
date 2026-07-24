# LoomAI Agent Notes

## Git History and Branch Promotion

- Keep Git history linear from the current aligned baseline forward. Use `dev` as the integration branch and `main` as the production branch.
- Commit application and deployment changes to `dev`; do not create independent commits directly on `main`.
- Promote `dev` to `main` only with a fast-forward. Before promotion, run `git fetch origin` and verify `git merge-base --is-ancestor origin/main origin/dev`; then fast-forward `main` to the exact `origin/dev` commit.
- Never use a merge commit, `--no-ff`, squash merge, or rebase merge for `dev` to `main` promotion. Do not force-push either published branch.
- After each promotion, `main` and `dev` must point to the same commit. If fast-forward is impossible, stop and repair the branch ancestry instead of merging divergent histories.

## Deployment

Use `agents/loom-deploy/SKILL.md` as the source of truth for LoomAI deployment steps, environment mapping, GitHub Actions checks, compose commands, and post-deploy verification.

## Non-Negotiable Rules

- Do not overwrite `.env` unless explicitly asked.
- Keep test deployments tied to `dev`; keep production deployments tied to `main`.
- Before production deployment, verify there are no actively processing tasks; deploy only when the queue is idle unless a forced deploy is explicitly requested.
- In production, only rebuild `backend` and `frontend`; do not recreate or restart `redis`, `nginx`, Safeline containers, PostgreSQL, or other infrastructure containers unless explicitly requested.
- If compose files or deployment scripts changed, make sure the server checkout is synced to the target branch before deployment.
- For risky or paid features, run a focused smoke test only when requested.
