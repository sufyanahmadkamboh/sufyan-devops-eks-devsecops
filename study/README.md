# Study guide: learn every tool used in this project

This guide is for engineers who are **new to AWS, Kubernetes and DevSecOps**. You don't need to know any of these tools before you start. Each chapter explains:

1. **What** the tool or idea is, in plain language
2. **Why** this project uses it, and the alternatives
3. **How** it works: the few concepts you really need
4. **Where** it is configured in this repository, with real file paths and snippets
5. **Try it:** commands to run (locally, or in your own AWS account)
6. **Common mistakes** people make with it
7. **Check yourself:** short questions (answers at the end of each chapter)

> 📄 **Prefer one file?** Download the whole guide as a single PDF: **[study-guide.pdf](study-guide.pdf)** (answers expanded, ready to print).
> Rebuild it after editing with `python study/tools/build_pdf.py`.

## How to use this guide

Read the chapters in order. Each one builds on the previous ones. Everything in the guide was really built, run, attacked and deleted on an AWS account; the measured numbers are in [docs/test-results.md](../docs/test-results.md).

| Step | Chapter | You will understand |
|---|---|---|
| 0 | [The big picture](00-big-picture.md) | What the whole project does, in 5 minutes, with no jargon |
| 1 | [AWS basics for this project](01-aws-basics.md) | Regions, availability zones, accounts, IAM, tags and cost |
| 2 | [VPC networking](02-vpc-networking.md) | Subnets, internet gateway, NAT gateway, route tables, security groups, flow logs |
| 3 | [Terraform](03-terraform.md) | Providers, modules, state, plan/apply/destroy, and guard rails for a shared account |
| 4 | [Amazon EKS](04-amazon-eks.md) | Control plane, managed nodes, add-ons, access entries, KMS, audit logs, IMDSv2 |
| 5 | [Containers for the app](05-containers-for-the-app.md) | React + Vite, a multi-stage Dockerfile, non-root nginx, security headers, digests |
| 6 | [Trivy and scanning](06-trivy-and-scanning.md) | The image gate, misconfiguration scans, written-down exceptions, a real finding |
| 7 | [GitHub Actions CI](07-github-actions-ci.md) | The five CI jobs, pinned actions, gitleaks, actionlint, zizmor |
| 8 | [OIDC and least privilege](08-oidc-and-least-privilege.md) | AWS access without keys, the trust policy, the immutable subject, namespace-scoped access |
| 9 | [The deploy pipeline](09-deploy-pipeline.md) | Two jobs, ECR by digest, ECR scan quirks, cosign, Kustomize, smoke test |
| 10 | [Load Balancer Controller and Ingress](10-load-balancer-and-ingress.md) | Ingress → ALB, Pod Identity, subnet tags, target type ip, HTTP without a domain |
| 11 | [Kubernetes workload security](11-workload-security.md) | securityContext, Pod Security "restricted", NetworkPolicy and a real lateral-movement finding |
| 12 | [Zero-downtime deployments](12-zero-downtime.md) | Rolling updates behind an ALB, readiness gates, preStop, deregistration delay, version skew |
| 13 | [Teardown and cost](13-teardown-and-cost.md) | Deleting in the right order, proving it, and what the lab cost |
| 14 | [Hands-on labs](14-hands-on-labs.md) | Nine exercises, from local scans to a full deploy and a verified teardown |
| | [Glossary](glossary.md) | Every term in one place |
| | [Interview questions](interview-questions.md) | 25 questions this project prepares you for, with answers |

## Before you start

For the local parts (chapters 5–7, labs 1–4) you need **Docker**, **git** and a **Bash** terminal (Git Bash works on Windows).

For the AWS parts (labs 5–9) you also need:
- an **AWS account of your own** (never practise in a company account without permission),
- **Terraform** 1.10 or newer, the **AWS CLI** v2, **kubectl** 1.36–1.38 and the **GitHub CLI**,
- a **fork** of this repository.

> 💶 **Cost warning:** while the lab runs on AWS it costs roughly **$0.30 per hour** (EKS control plane, two small nodes, a NAT gateway, a load balancer). The recorded build ran for 62 minutes, an estimated $0.35. **Always run `scripts/teardown.sh` the same day.**

## Time needed

| Part | Time |
|---|---|
| Chapters 0–4 (AWS, network, Terraform, EKS) | 3–4 hours |
| Chapters 5–9 (app, scanning, CI, OIDC, CD) | 3–4 hours |
| Chapters 10–13 (exposure, workload security, rollouts, teardown) | 2–3 hours |
| Labs | 3–5 hours (1–2 hours of it on AWS) |

## Where to go next

After this guide, read the project's [architecture document](../docs/architecture.md) (the decision log explains every trade-off), the [runbook](../docs/runbook.md) and the [troubleshooting notes](../docs/troubleshooting.md).
