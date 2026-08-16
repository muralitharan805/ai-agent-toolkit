---
trigger: always_on
description: "Enforces that all Dockerfiles produced or modified in the workspace must explicitly define a non-root USER instruction in the final runtime stage."
---
# No Root User in Dockerfile Rule

## Description
This rule strictly forbids running production container workloads under the `root` user privilege. Every Dockerfile generated or edited must specify a low-privilege `USER` (e.g. `USER node`, `USER 10001`) before the entrypoint or command declaration.

## Constraints
- The agent MUST include a `USER [non-root-user]` instruction in the final production stage of every Dockerfile.
- The agent MUST NOT leave default root execution active in container entrypoints.

## Examples
- **Correct implementation:**
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY --chown=node:node . .
USER node
CMD ["node", "server.js"]
```

- **Incorrect implementation:**
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY . .
# Missing USER instruction - defaults to root!
CMD ["node", "server.js"]
```
