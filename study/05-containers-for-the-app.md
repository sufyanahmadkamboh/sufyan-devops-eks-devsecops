# 5. Containers for the app

## What is it?

- **React** is a JavaScript library for user interfaces. **Vite** builds a React app into plain static files: one `index.html`, plus JavaScript and CSS files with a hash in their names (`index-xTPJYkoq.js`).
- A **container image** packages an app with everything it needs to run. A **Dockerfile** is the recipe.
- **nginx** is a fast web server; **nginx-unprivileged** is the official variant that runs as a normal user on port 8080.

## Why this project builds the image this way

The app is just static files. It needs no Node.js at runtime, no shell, no root. Every extra component is something to patch and something an attacker can use. So the image is:
- built in **two stages** (build with Node.js, run with nginx only),
- based on images **pinned by digest**,
- running as a **non-root** user, with a **read-only** file system in Kubernetes,
- sending **strict security headers** with every response.

## How it works

### The app and its tests

[`app/src/App.jsx`](../app/src/App.jsx) renders the profile card from [`app/src/profile.js`](../app/src/profile.js). The footer shows the version and git commit, which the pipeline bakes into each build (`VITE_VERSION`, `VITE_COMMIT`), so you always see what is running.

[`app/src/App.test.jsx`](../app/src/App.test.jsx) has **5 tests** (Vitest + Testing Library): name and role, every skill listed, external links open safely in a new tab, mailto links do not, the build footer is shown. CI also runs `oxlint` and `npm audit --audit-level=high`.

### The multi-stage Dockerfile

[`app/Dockerfile`](../app/Dockerfile):

```dockerfile
FROM node:24-alpine@sha256:ebfe2f90…05ec1c1 AS build
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

FROM nginxinc/nginx-unprivileged:1.30-alpine@sha256:ed04ec1f…dd20b1e
USER 0
RUN apk upgrade --no-cache
USER 101
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
```

- **Stage 1** installs dependencies with `npm ci` (exactly the versions in `package-lock.json`) and builds the static files.
- **Stage 2** starts from nginx and copies only the built files. Node.js and all build tools stay behind.
- `USER 0` → `apk upgrade` → `USER 101`: apply Alpine security fixes that are newer than the base image, then drop back to the unprivileged user. Chapter 6 shows the real vulnerability that made this necessary.
- **Digests** (`@sha256:…`) pin the exact base image content. A tag like `1.30-alpine` can be moved to different content; a digest cannot.

### nginx configuration

[`app/nginx/default.conf`](../app/nginx/default.conf):
- `listen 8080` and `server_tokens off` (no version in error pages)
- `location = /healthz` returns `ok`: used by Kubernetes probes and by the load balancer health check
- `/assets/` (hashed files) are cached for a year; everything else returns `index.html` (single-page app routing) with `Cache-Control: no-cache`

[`app/nginx/security-headers.conf`](../app/nginx/security-headers.conf) is included in every location, because nginx does **not** inherit `add_header` into a location that sets its own headers:

| Header | Effect |
|---|---|
| `Content-Security-Policy: default-src 'self'; …` | the browser only runs scripts and styles from this site |
| `X-Content-Type-Options: nosniff` | no guessing of file types |
| `X-Frame-Options: DENY`, `frame-ancestors 'none'` | the page cannot be embedded (clickjacking) |
| `Referrer-Policy: no-referrer` | no URL leaks to other sites |
| `Permissions-Policy: camera=(), microphone=(), …` | no access to device features |

These headers came back from the real load balancer: `curl -D -` showed all of them with `HTTP/1.1 200 OK`.

## Try it (locally, no AWS)

```bash
docker build -t profile-card:local --build-arg VERSION=0.1.0 --build-arg COMMIT=abcdef1 app
docker run -d --name pc --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges \
  -p 18080:8080 profile-card:local
curl -s localhost:18080/healthz
curl -sI localhost:18080/ | grep -i -E 'content-security|x-frame'
docker exec pc id            # uid=101(nginx)
docker rm -f pc
```

Open http://localhost:18080 in a browser: the footer shows `v0.1.0 · abcdef1`.

## Common mistakes

- Single-stage images that ship Node.js, npm and the source code to production.
- `npm install` instead of `npm ci` in builds (versions drift).
- Adding `add_header` inside one nginx location and silently losing all the security headers there.
- Running the web server as root "because port 80 needs it". Use port 8080 and let the Service map port 80.

## Check yourself

1. What does stage 2 of the Dockerfile copy from stage 1?
2. Why is the image pinned by digest even though the tag `1.30-alpine` exists?
3. Why does the security header snippet have to be included in every nginx location?

### Answers

<details><summary>Answers</summary>

1. Only the built static files (`/app/dist`), nothing else.
2. A tag can be moved to different content at any time; the digest is the hash of the content and guarantees exactly the image that was tested and scanned.
3. nginx does not inherit `add_header` directives into a location that defines its own `add_header` (here: `Cache-Control`), so the headers would disappear from those responses.

</details>

Next: [6. Trivy and scanning](06-trivy-and-scanning.md)
