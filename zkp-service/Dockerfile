# =========================================
# Stage 0 — Build circom + fetch circomlib (Alpine)
# =========================================
FROM alpine:3.18 AS zkp-build
ARG CARGO_HOME=/root/.cargo
ARG RUSTUP_HOME=/root/.rustup
WORKDIR /tmp

# Build deps for circom
RUN apk add --no-cache curl git build-base musl-dev

# Install Rust (non-interactive)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="${CARGO_HOME}/bin:${PATH}"

# Clone sources we also want available at runtime
RUN git clone https://github.com/iden3/circom.git
RUN git clone https://github.com/iden3/circomlib.git

# Build circom (binary ends up in target/release/circom)
WORKDIR /tmp/circom
RUN cargo build --release

# =========================================
# Stage 1 — Node deps (dev) on Alpine
# =========================================
FROM node:20-alpine AS deps
WORKDIR /app/services/api
RUN apk add --no-cache python3 make g++ git

COPY services/api/package*.json ./
RUN npm ci --include=dev

# =========================================
# Stage 2 — Build TypeScript
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

# ---- System tools & runtime libs ----
# bash      -> run your scripts
# coreutils -> tee
# libstdc++ -> required by circom binary
# gmp       -> required by circom/snarkjs
# wget      -> healthcheck
RUN apk add --no-cache bash coreutils libstdc++ gmp wget \
 && ln -sf /bin/bash /usr/bin/bash

# ---- App deps (prod only) ----
COPY services/api/package*.json ./
RUN npm ci --omit=dev

# ---- App code ----
COPY --from=build /app/services/api/dist ./dist

# ---- circom binary ----
COPY --from=zkp-build /tmp/circom/target/release/circom /usr/local/bin/circom
RUN chmod +x /usr/local/bin/circom

# ---- Bring circom & circomlib repos (folders) at the same level ----
# You asked that "circom is a folder and should be on the same level as circomlib".
# We place them under /zkp/{circom, circomlib}
RUN mkdir -p /zkp
COPY --from=zkp-build /tmp/circom     /zkp/circom
COPY --from=zkp-build /tmp/circomlib  /zkp/circomlib

# ---- Circuits (project sources) ----
# If your repo has circuits/src at project root:
RUN mkdir -p /circuits/src /circuits/ptau
COPY circuits/src /circuits/src

# ---- Global npm (snarkjs) ----
ENV PATH="/usr/local/bin:/usr/bin:/bin:${PATH}"
RUN npm config set prefix /usr/local && npm install -g snarkjs@0.7.5

# ---- Scripts ----
COPY scripts /scripts
RUN chmod +x /scripts/*.sh && sed -i 's/\r$//' /scripts/*.sh

# ---- Env for your scripts (avoid path guessing) ----
ENV CIRCUITS_SRC_DIR=/circuits/src
ENV CIRCOMLIB_PATH=/zkp/circomlib/circuits
ENV CIRCOM_BIN=/usr/local/bin/circom
# (Optional, in case your scripts want to know where the repo is)
ENV CIRCOM_ROOT=/zkp/circom

# ---- Sanity checks (optional, safe to keep) ----
RUN test -x "$CIRCOM_BIN" \
 && test -d "$CIRCUITS_SRC_DIR" \
 && test -f "$CIRCOMLIB_PATH/poseidon.circom"

# ---- Run setup scripts with live logs ----
WORKDIR /scripts
RUN bash -x ./initial-project-setup.sh 2>&1 | tee /initial_setup.log
RUN bash -x ./scheme-compilation.sh     2>&1 | tee /scheme_compilation.log
RUN bash -x ./ptau-download.sh          2>&1 | tee /ptau_download.log
RUN bash -x ./generate-zkeys.sh /circuits/ptau/hez13.ptau "MVP Contribution" 2>&1 | tee /generate_zkeys.log

# ---- Ensure circuits are accessible from /app and keys land in /app/keys ----
RUN ln -s /circuits /app/circuits || true
ENV CIRCUITS_SRC_DIR=/app/circuits/src

# ---- Runtime app ----
WORKDIR /app/services/api
# Create default data dirs the app expects and grant permissions to node
# Also create logs directory for file-based logging
RUN mkdir -p /app/data/input /app/data/output /app/logs \
 && chown -R node:node /app

# (optional) your circuits live at /circuits/src but your code defaults to /app/circuits/src.
# Provide a friendly symlink so existing code keeps working.
RUN ln -s /circuits /app/circuits || true
# Keys expected at /app/keys but were created under /keys -> symlink them
RUN ln -s /keys /app/keys || true
USER node

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3000/health || exit 1

CMD ["npm", "run", "start"]
