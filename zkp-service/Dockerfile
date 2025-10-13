# -----------------------------------------
# Stage 1 — Dependencies (with dev deps)
# -----------------------------------------
FROM node:20-alpine AS deps
WORKDIR /app/services/api

# Copy package manifests from inside the service
COPY services/api/package*.json ./
RUN npm ci --include=dev

# -----------------------------------------
# Stage 2 — Build TypeScript -> dist
# -----------------------------------------
FROM deps AS build
WORKDIR /app/services/api

# Copy tsconfig and sources relative to service root
COPY services/api/tsconfig.json ./
COPY services/api/src ./src

RUN npm run build

# -----------------------------------------
# Stage 3 — Runtime (prod-only)
# -----------------------------------------
FROM node:20-alpine AS runtime
WORKDIR /app/services/api
ENV NODE_ENV=production

# Install only prod deps
COPY services/api/package*.json ./
RUN npm ci --omit=dev

# Copy compiled JS from build stage
COPY --from=build /app/services/api/dist ./dist

# Optional: copy env/config files if needed
# COPY services/api/.env ./

USER node
EXPOSE 3000

# Optional healthcheck
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/health || exit 1

CMD ["npm", "run", "start"]
