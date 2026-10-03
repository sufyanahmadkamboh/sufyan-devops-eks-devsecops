# 7. GitHub Actions CI

## What is it?

**GitHub Actions** runs **workflows** (YAML files in `.github/workflows/`) on GitHub's machines when something happens in the repository: a push, a pull request, a button click. A workflow has **jobs**; a job has **steps**; a step runs a command or an **action** (a reusable step published by someone).

**CI** (continuous integration) means: every change is checked automatically before it is merged.

## Why this project uses it

The code lives on GitHub, Actions is free for public repositories, and it can get short-lived cloud credentials through OIDC (chapter 8).

**Alternatives:** GitLab CI, Jenkins, CircleCI, Azure Pipelines, AWS CodePipeline.

## How it works: the five CI jobs

[`.github/workflows/ci.yaml`](../.github/workflows/ci.yaml) runs on every pull request and every push to `main`. **None of its jobs can reach AWS.**

| Job | Steps | Catches |
|---|---|---|
| **Secret scan** | `gitleaks git --redact --exit-code 1 .` on the full history | access keys, passwords and tokens committed by mistake, even in old commits |
| **App** | `npm ci`, `npm run lint` (oxlint), `npm test` (5 tests), `npm audit --audit-level=high`, `npm run build` | broken code, failing tests, vulnerable npm packages |
| **Container** | hadolint on the Dockerfile, `docker build`, Trivy image gate | Dockerfile mistakes, fixable HIGH/CRITICAL CVEs |
| **Infrastructure** | `terraform fmt -check`, `init -backend=false`, `validate`, Trivy config (Terraform), render manifests, `kubeconform -strict`, Trivy config (Kubernetes) | invalid Terraform, risky settings, manifests that do not match the Kubernetes schema |
| **Pipeline security** | `check-pinned-actions.sh`, actionlint, zizmor | unpinned actions, workflow syntax errors, workflow security mistakes |

### Securing the pipeline itself

The pipeline holds the keys to production, so it is protected like production:

- **`permissions: {}`** at the top: no job gets any token permission unless it asks. Each CI job asks only for `contents: read`.
- **Actions pinned to a full commit SHA**, for example
  `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`. A version tag like `v7` can be moved to a malicious commit (this happened to the popular `tj-actions/changed-files` action in 2025); a commit SHA cannot. [`scripts/ci/check-pinned-actions.sh`](../scripts/ci/check-pinned-actions.sh) fails CI if anyone adds an unpinned action.
- **`persist-credentials: false`** on checkout: the job's token is not left on disk for later steps.
- **Tools installed by checksum** ([`scripts/ci/install-tools.sh`](../scripts/ci/install-tools.sh)): gitleaks, Trivy, Syft, cosign, kubeconform, Terraform and actionlint are downloaded from their official releases and checked against pinned SHA-256 values, instead of adding more third-party actions.
- **actionlint** checks workflow syntax and the shell scripts inside `run:` (it found a word-splitting issue during this project).
- **zizmor** audits workflows for security problems such as template injection (`${{ }}` inside `run:`), excessive permissions and credential persistence. It reported **no findings** for both workflows.
- **CODEOWNERS** and **Dependabot** ([`.github/`](../.github/)): changes to workflows, Terraform and manifests need the owner's review; Dependabot proposes updates for actions, npm, Docker base images and Terraform.

## Where it is configured

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]
permissions: {}

jobs:
  secrets:
    runs-on: ubuntu-24.04
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0              # gitleaks needs the full history
          persist-credentials: false
      - run: scripts/ci/install-tools.sh gitleaks
      - run: gitleaks git --redact --no-banner --exit-code 1 .
```

## Try it

```bash
scripts/ci/check-pinned-actions.sh
docker run --rm -v "$PWD:/repo" -w /repo rhysd/actionlint:1.7.12 -color=false
docker run --rm -v "$PWD:/repo" -w /repo python:3.13-slim sh -c \
  "pip install -q --require-hashes -r tools/zizmor-requirements.txt && zizmor --min-severity medium .github/workflows"
docker run --rm -i hadolint/hadolint:v2.15.1 < app/Dockerfile
```

Then make a mistake on purpose (lab 3) and watch which check catches it.

## Common mistakes

- `permissions: write-all` or no `permissions` block at all.
- Using actions by tag (`@v4`) instead of commit SHA.
- `${{ github.event.pull_request.title }}` directly inside `run:` (template injection).
- Scanning only the latest commit for secrets: a key deleted in the next commit is still in the history.

## Check yourself

1. Why does the secret scan check out the full history?
2. What is the difference between a version tag and a commit SHA for an action?
3. Which CI job would fail if someone added `USER root` at the end of the Dockerfile?

### Answers

<details><summary>Answers</summary>

1. A secret committed once stays in git history even if a later commit removes it; scanning only the latest files would miss it.
2. A tag is a movable label the action's owner (or an attacker with their access) can point at any commit; a full commit SHA always means exactly the same code.
3. The **container** job: hadolint rule DL3002 ("last USER should not be root") fails it. In the cluster the pod would still run as UID 10101, because `runAsUser` in the Deployment overrides the image's `USER` (chapter 11): two independent layers. Lab 3 lets you try it.

</details>

Next: [8. OIDC and least privilege](08-oidc-and-least-privilege.md)
