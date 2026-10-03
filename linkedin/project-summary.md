# Project summary

**EKS DevSecOps Platform: React on Amazon EKS with Terraform and GitHub Actions** · Senior

**What it does:** Terraform builds a production-style platform in one AWS region (eu-central-1): a VPC over two
availability zones (private node subnets, public subnets for the load balancer only, one NAT gateway, flow logs), an
EKS 1.37 cluster (KMS-encrypted secrets, audit logs, access entries, IMDSv2 hop limit 1, VPC CNI network policies,
Pod Identity), an immutable ECR repository with scan on push, the AWS Load Balancer Controller, and a GitHub OIDC role.
A React + Vite app ships in a non-root, read-only nginx image and is exposed through an Ingress → ALB.

**Pipeline:** CI runs gitleaks, lint/tests/npm audit, hadolint + Trivy image gate, Terraform validate + Trivy
misconfiguration scan + kubeconform, and pinned-actions/actionlint/zizmor. CD builds and scans without cloud access,
then (production environment, OIDC) pushes by digest, waits for ECR's scan, signs with cosign, deploys the exact
digest, asserts its namespace-only permissions with `kubectl auth can-i`, and smoke-tests the ALB.

**Measured (real AWS account, 62 minutes):** apply 72 resources in 12 min 30 s; push to live 3 min 37 s; Trivy
blocked a HIGH CVE in the base image; privileged pod, pod egress and IMDS credential theft refused; lateral movement
from another namespace worked, was fixed and then blocked; 3/280 failed requests during a rollout → 401/401 after
readiness gates, preStop and deregistration delay; teardown 72 destroyed and verified clean; estimated cost ≈ $0.35.

**Stack:** Terraform 1.15 (AWS provider 6.67, VPC 6.7.3, EKS 21.26.0), Amazon EKS 1.37, AWS Load Balancer Controller
3.5.0, ECR, React 19 + Vite 8, nginx-unprivileged 1.30, GitHub Actions, Trivy 0.75, cosign 3.1, Syft 1.54, gitleaks,
hadolint, kubeconform, actionlint, zizmor.
