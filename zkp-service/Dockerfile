# =========================================
# Stage 0 — Build circom + fetch circomlib
# (Debian so rust/cargo builds smoothly)
# =========================================
FROM debian:bookworm-slim AS zkp-build
ARG CARGO_HOME=/root/.cargo
ARG RUSTUP_HOME=/root/.rustup
WORKDIR /tmp

# Base deps for building circom
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates git build-essential pkg-config \
 && rm -rf /var/lib/apt/lists/*

# Install Rust (non-interactive)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="$CARGO_HOME/bin:${PATH}"

# Build circom from source
RUN git clone https://github.com/iden3/circom.git
WORKDIR /tmp/circom
RUN cargo build --release

# Collect artifacts for later stages
#  - circom binary
#  - circomlib tree (for -l ./circomlib/circuits)
WORKDIR /tmp
RUN git clone https://github.com/iden3/circomlib.git

# =========================================
# Stage 1 — Node deps (with dev) on Alpine
# =========================================
FROM node:20-alpine AS deps
WORKDIR /app/services/api

# Tooling needed for native node modules during npm ci (dev stage only)
RUN apk add --no-cache python3 make g++ git

# Copy package manifests from inside the service
COPY services/api/package*.json ./
RUN npm ci --include=dev

# =========================================
# Stage 2 — Build TS -> dist
# =========================================
FROM deps AS build
WORKDIR /app/services/api
COPY services/api/tsconfig.json ./
COPY services/api/src ./src
RUN npm run build

# =========================================
# Stage 3 — Runtime (prod only)
# =========================================
FROM node:20-alpine AS runtime
WORKDIR /app/services/api
ENV NODE_ENV=production

# 1) Install only prod deps
COPY services/api/package*.json ./
RUN npm ci --omit=dev

# 2) Bring in compiled JS
COPY --from=build /app/services/api/dist ./dist

# 3) Bring in circom binary built on Debian
#    (works fine; it's a static-ish Rust binary. Place it in PATH.)
COPY --from=zkp-build /tmp/circom/target/release/circom /usr/local/bin/circom

# 4) Bring circomlib into the service so "-l ./circomlib/circuits" works
COPY --from=zkp-build /tmp/circomlib ./circomlib

# 5) Install snarkjs CLI globally
#    (install as root, then we can drop privileges)
RUN npm install -g snarkjs

# Optional: copy env/config files if needed
# COPY services/api/.env ./

# Non-root runtime
USER node

EXPOSE 3000

# Optional healthcheck (busybox wget is present on Alpine)
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/health || exit 1

CMD ["npm", "run", "start"]
