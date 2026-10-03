# Test results

Everything on this page was measured on a real AWS account in **eu-central-1** on 2026-10-03/04, between the first
`terraform apply` and a verified teardown **62 minutes** later. Account identifiers are redacted.

## 1. Infrastructure (Terraform)

| Step | Result |
|---|---|
| `terraform plan` | **73 to add, 0 to change, 0 to destroy** (nothing existing touched) |
| `terraform apply` | **72 resources in 12 min 30 s** (the unused IRSA OIDC provider was switched off after the plan) |
| NAT gateway | 1 min 33 s |
| EKS control plane | 8 min 44 s |
| Managed node group (2 × t3.medium) | 1 min 59 s |
| AWS Load Balancer Controller (Helm) | 21 s |
| Nodes | 2 × Ready, Kubernetes v1.37.0, **EXTERNAL-IP: none**, one per availability zone |
| Cluster | authentication mode API (access entries), control plane logs api/audit/authenticator, secrets encrypted with KMS |

## 2. Pipeline

| Check | Result |
|---|---|
| CI (5 jobs: secrets, app, container, infrastructure, pipeline security) | green |
| Trivy image gate, first image | **failed (correctly)**: pcre2 CVE-2026-103111 (HIGH, fixed in 10.49-r0) in `nginx-unprivileged:1.30-alpine`; fixed with `apk upgrade`, then 0 findings |
| Trivy config scan, Terraform | 3 findings in our configuration (AWS-0040, AWS-0041, AWS-0104), accepted in `.trivyignore.yaml` with reasons and an expiry date |
| Trivy config scan, Kubernetes | 99 passed; 2 LOW (UID ≤ 10000) fixed by running as UID 10101; KSV-0125 (untrusted registry) caught a placeholder registry in the CI test |
| Push to live (deploy run, triggered by a push) | **3 min 37 s** (build and scan 33 s, deploy 2 min 54 s) |
| ECR scan on push | COMPLETE, 0 findings |
| cosign | signed and verified (keyless) |
| Least-privilege check of the deploy role | create deployments in `profile-card`: **yes**; in `kube-system`: no; get secrets in `kube-system`: no; create clusterrolebindings: no; delete namespaces: no |
| Smoke test through the ALB | HTTP 200, all security headers present |

## 3. Attacks against the running cluster

| Attack | Result |
|---|---|
| Privileged pod in `profile-card` | **refused** by Pod Security `restricted` (5 violations listed) |
| Outbound traffic from an app pod (`wget http://example.com`) | **blocked**: `bad address`, the default-deny NetworkPolicy blocks even DNS |
| Node credentials from a pod (IMDSv2 token request) | **blocked**: the PUT times out (hop limit 1); IMDSv1 without a token: 401 |
| Pod in another namespace → app pod IP:8080 | **worked (HTTP 200)** with the first NetworkPolicy ("allow the VPC"), because pod IPs are VPC IPs on EKS; **blocked** after allowing only the load balancer subnets (10.42.48.0/23). Pods stayed ready, the ALB kept answering |
| Requests during a deployment (2 per second) | **3 of 280 failed** (1 × 502, 2 timeouts) with a plain rolling update; **401 of 401 succeeded** after pod readiness gates, a 15 s preStop sleep and a 10 s ALB deregistration delay. Old and new versions were served side by side for about 28 s |

## 4. Teardown

| Step | Result |
|---|---|
| Delete the Ingress | the controller removed the ALB (verified before continuing) |
| `terraform destroy` | **72 resources destroyed** (EKS 3 min 29 s, NAT gateway 1 min 20 s), 15 min in total |
| `scripts/verify-teardown.sh` | every resource type gone (by name and by tag), project IAM roles and policies gone, the shared GitHub OIDC provider **kept** |
| KMS key | PendingDeletion (AWS minimum 7 days, not billed) |
| Region inventory before vs after | VPCs 1/1, Elastic IPs 0/0, NAT 0/0, EKS 0/0, load balancers 0/0, ECR 0/0, instances 0/0 |

Estimated compute cost: about $0.30 per hour × 62 minutes ≈ **$0.35** (on-demand prices; the bill is the final word).

## 5. Problems found and fixed during the build

1. **Trivy blocked the base image** (pcre2 HIGH with a fix available) → `apk upgrade` in the runtime stage.
2. **OIDC role could not be assumed**: new GitHub repositories use an immutable subject
   (`repo:owner@<id>/name@<id>:environment:production`) → the trust policy uses it (`github_oidc_subject_prefix`).
3. **ECR scan waiter** failed with `ScanNotFoundException` right after the push → polling loop.
4. **ECR returns no counts for a clean image** → empty treated as zero.
5. **Lateral movement** through the VPC-wide NetworkPolicy rule → load balancer subnets only.
6. **Dropped requests during rollouts** → readiness gates, preStop, deregistration delay.
7. **Teardown verification**: module-generated IAM names without the project prefix, and the tagging API listing
   deleted resources → checks by prefix + tag and by real state; Terraform now prefixes every IAM name.

Changes made after the recorded run (validated with `terraform validate` and the CI scans, not re-applied on AWS):
the IAM names of the node role and the flow-log role now start with `eks-devsecops-`.
