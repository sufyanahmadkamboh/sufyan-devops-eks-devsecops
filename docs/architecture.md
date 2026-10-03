# Architecture

## Components

| Component | Where | Role |
|---|---|---|
| VPC 10.42.0.0/16 | eu-central-1, 2 AZs | public subnets (ALB, NAT gateway), private subnets (nodes, pods); flow logs; default SG allows nothing |
| EKS 1.37 control plane | AWS-managed | API (public + private endpoint), audit logs, KMS envelope encryption of secrets, access entries |
| Managed node group | private subnets | 2 × t3.medium (AL2023), IMDSv2 required with hop limit 1, encrypted gp3 disks |
| VPC CNI | add-on | pod IPs from the VPC, NetworkPolicy enforcement enabled |
| EKS Pod Identity agent | add-on | AWS permissions for the Load Balancer Controller without keys |
| AWS Load Balancer Controller 3.5.0 | kube-system, 2 replicas | Ingress → internet-facing ALB (target type ip), tags everything it creates |
| ECR `eks-devsecops/profile-card` | regional | immutable tags, scan on push, AES-256, lifecycle: last 10 images |
| IAM role `eks-devsecops-github-deploy` | global | assumed via GitHub OIDC from this repo's `production` environment only |
| `profile-card` namespace | created by Terraform | Pod Security `restricted`, pod readiness gate injection |

## Flow of a release

1. `git push` to `main` → `deploy.yaml`.
2. Job 1 (no cloud permissions): build with version and commit, Trivy gate (fixable CRITICAL/HIGH), SBOM, image saved as an artifact.
3. Job 2 (environment `production`): OIDC → temporary credentials for the deploy role; push to ECR; wait for ECR's scan
   (fails on CRITICAL); keyless cosign signature, verified; `kubectl apply -k` with the exact digest; wait for the
   rollout; `kubectl auth can-i` checks; smoke test through the ALB.
4. Rolling update with `maxUnavailable: 0`: a new pod receives traffic only when the ALB target is healthy (readiness
   gate); an old pod keeps serving for 15 s (preStop) while the ALB deregisters it (10 s).

## Trust boundaries

| Actor | Can | Cannot |
|---|---|---|
| Anyone on the internet | HTTP to the ALB (port 80) | reach nodes (no public IPs) or pods directly |
| A pull request (fork or branch) | run CI (no secrets, no cloud access) | assume the AWS role (subject must be `environment:production`, main only) |
| The deploy role | push to one ECR repo; edit objects in `profile-card` | other namespaces, secrets in kube-system, cluster-wide RBAC, other AWS resources |
| A compromised app pod | serve HTTP | reach the internet (egress denied), other pods (ingress only from ALB subnets), node credentials (IMDS hop limit), escalate (restricted PSA) |
| A pod in another namespace | — | reach the app pods (only the ALB subnets are allowed) |

## Decisions

| # | Decision | Why | Trade-off |
|---|---|---|---|
| 1 | Community Terraform modules (VPC 6.7.3, EKS 21.26.0), pinned | battle-tested defaults, less custom code | module-generated names (now overridden with the project prefix) |
| 2 | Region validation + `allowed_account_ids` | built in a shared company account | — |
| 3 | GitHub OIDC, reusing the account's existing provider read-only | no stored keys; never modify shared IAM | the trust policy must match GitHub's immutable subject |
| 4 | Access entries (`authentication_mode = API`) | IAM ↔ Kubernetes mapping as code, namespace-scoped policies | — |
| 5 | Pod Identity instead of IRSA | no extra IAM OIDC provider per cluster | needs the Pod Identity agent add-on |
| 6 | Public API endpoint | GitHub-hosted runners have no fixed IPs | accepted risk (AWS-0040/0041); fix: private endpoint + self-hosted runners |
| 7 | One NAT gateway | lab cost | single point of failure for egress; production: one per AZ |
| 8 | ALB target type ip + readiness gates + preStop | traffic straight to pods; zero-downtime rollouts (measured) | slower pod termination (15 s) |
| 9 | Scan without credentials, deploy in a separate job | scanners never run next to AWS credentials | image passed as an artifact |
| 10 | HTTP only | no domain → no certificate | add ACM + HTTPS with a domain |
| 11 | Local Terraform state (gitignored) | one operator, short-lived lab | team use needs S3 + locking |
| 12 | Teardown deletes the Ingress first | the ALB is created by the controller, not Terraform | — |
