# Build stage: base images are pinned by digest (a tag can be moved, a digest cannot).
FROM node:25-alpine@sha256:bdf2cca6fe3dabd014ea60163eca3f0f7015fbd5c7ee1b0e9ccb4ced6eb02ef4 AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src
ARG VERSION=dev
ARG COMMIT=local
ENV VITE_VERSION=${VERSION} VITE_COMMIT=${COMMIT}
RUN npm run build

# Runtime: nginx as an unprivileged user (uid 101) on port 8080; only static files, no Node.js.
FROM nginxinc/nginx-unprivileged:1.30-alpine@sha256:ed04ec1ff34502c339ee5c3ae3f855442398edc1d05591e2b98981dcbbd20b1e
# Apply Alpine security fixes published after the base image was built (the Trivy gate found pcre2
# CVE-2026-103111 in 1.30-alpine). Then drop back to the unprivileged user.
USER 0
RUN apk upgrade --no-cache
USER 101
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
