# 6. Trivy and scanning

## What is it?

**Trivy** (by Aqua Security, open source) is a security scanner. In this project it does two jobs:

| Mode | Command | Finds |
|---|---|---|
| **Image scan** | `trivy image` | known vulnerabilities (**CVEs**) in the operating-system packages and libraries inside an image |
| **Misconfiguration scan** | `trivy config` | risky settings in Terraform and Kubernetes files (public endpoints, root containers, missing limits…) |

A **CVE** (Common Vulnerabilities and Exposures) is the public ID of a known security bug, for example `CVE-2026-103111`. Each has a **severity**: LOW, MEDIUM, HIGH, CRITICAL.

## Why this project uses it

A vulnerability that already has a fix should never reach production. And a misconfiguration in Terraform is much cheaper to fix before `apply` than after an incident.

**Alternatives:** Grype (images), Snyk, Docker Scout, Amazon Inspector (paid ECR scanning); Checkov, tfsec (now part of Trivy) and kube-score for configuration.

## How it works

### The image gate

```bash
trivy image --quiet --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed profile-card:build
```

- `--severity CRITICAL,HIGH`: only these block the build.
- `--ignore-unfixed`: block only on problems that **have a fix**. A gate that fails on things nobody can fix just teaches people to switch it off.
- `--exit-code 1`: any finding makes the command fail, which fails the pipeline step.

### The real finding

The very first image of this project was **blocked**. The official `nginx-unprivileged:1.30-alpine` base image, pinned to the latest digest, contained:

```
profile-card:local (alpine 3.24.2)
Total: 1 (HIGH: 1, CRITICAL: 0)
│ pcre2 │ CVE-2026-103111 │ HIGH │ fixed │ 10.48-r0 │ 10.49-r0 │ Out-of-bounds write via crafted regular expression
gate exit code: 1
```

The fix already existed in Alpine; the base image was just older than the fix. Three lines in the Dockerfile (`USER 0`, `RUN apk upgrade --no-cache`, `USER 101`) and the scan showed **0 vulnerabilities**, exit code 0.

### Misconfiguration scans

CI scans two things:
1. the Terraform code (skipping `terraform/.terraform`, where the downloaded modules' own examples live),
2. the **rendered** Kubernetes manifests (`kubectl kustomize k8s`), so Trivy sees what is really applied.

Results in this project:
- Kubernetes: 99 checks passed. Two LOW findings ("runs with UID ≤ 10000") were fixed by running as UID **10101**.
- **KSV-0125 (untrusted registry)** caught a test placeholder `registry.example` in the CI render. The real deployment uses ECR, so the test now uses an ECR-style address.
- Terraform: **three real findings in this project's configuration**, which were kept on purpose.

### Written-down exceptions

[`.trivyignore.yaml`](../.trivyignore.yaml):

| ID | Finding | Why accepted | Production fix |
|---|---|---|---|
| AWS-0040 | EKS API endpoint is public | GitHub-hosted runners have no fixed IP; access still needs IAM | private endpoint + self-hosted runners in the VPC |
| AWS-0041 | public endpoint open to 0.0.0.0/0 | same reason | same |
| AWS-0104 | nodes may connect out to any IP | nodes need ECR, EKS, STS and package mirrors via NAT; pod egress is denied separately | egress through a proxy or VPC endpoints |

Each entry has a **statement** (the reason) and an **`expired_at: 2027-04-01`**. On that date the pipeline fails again and someone must review it. An exception without a reason and an end date quietly becomes permanent.

### A second opinion in AWS

ECR also scans every pushed image (**scan on push**, basic scanning, free). The deploy job waits for that result and stops on any CRITICAL finding (chapter 9).

## Where it is integrated

- [`.github/workflows/ci.yaml`](../.github/workflows/ci.yaml): job `container` (image gate), job `infrastructure` (Terraform and Kubernetes scans).
- [`.github/workflows/deploy.yaml`](../.github/workflows/deploy.yaml): job `build-scan` (image gate before anything is pushed).
- Trivy itself is downloaded by [`scripts/ci/install-tools.sh`](../scripts/ci/install-tools.sh) and checked against a pinned SHA-256.

## Try it (locally)

```bash
docker build -t profile-card:local app
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.75.0 \
  image --severity CRITICAL,HIGH --ignore-unfixed profile-card:local
docker run --rm -v "$PWD:/src" -w /src aquasec/trivy:0.75.0 \
  config --severity HIGH,CRITICAL --ignorefile .trivyignore.yaml --skip-dirs terraform/.terraform terraform
```

On Windows (Git Bash) use `//var/run/docker.sock` and `MSYS_NO_PATHCONV=1`.

## Common mistakes

- Blocking on unfixed vulnerabilities: the gate is always red and people stop looking.
- Scanning Terraform including `.terraform/`: you get findings from module examples you do not use.
- Ignoring findings with no reason and no end date.
- Scanning the image *after* pushing it: then a vulnerable image is already in the registry.

## Check yourself

1. What does `--ignore-unfixed` change, and why is it useful?
2. Why was the first image blocked, and how was it fixed?
3. What two things must every accepted exception have?

### Answers

<details><summary>Answers</summary>

1. Only vulnerabilities that already have a fixed version are reported, so the gate fails only on problems the team can actually fix.
2. The nginx base image contained pcre2 10.48 with CVE-2026-103111 (HIGH, fixed in 10.49). Running `apk upgrade` in the runtime stage installed the fixed package.
3. A written reason (with the real fix) and an expiry date, so it is reviewed again.

</details>

Next: [7. GitHub Actions CI](07-github-actions-ci.md)
