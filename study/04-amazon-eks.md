# 4. Amazon EKS

## What is it?

**Kubernetes** runs containers on a group of machines and keeps them running. **Amazon EKS** (Elastic Kubernetes Service) is Kubernetes where AWS runs the "brain" for you.

| Part | Who runs it | Job |
|---|---|---|
| **Control plane** | AWS | the Kubernetes API server, scheduler, etcd database |
| **Managed node group** | AWS creates and updates the EC2 machines; you choose size and count | the worker nodes that run your pods |
| **Add-ons** | AWS-provided, installed by you | cluster plumbing: networking, DNS, identity |

## Why this project uses it

Running your own Kubernetes control plane means patching, backups and high availability. EKS does that, integrates with IAM and load balancers, and is very common in job descriptions.

**Alternatives:** self-managed Kubernetes on EC2, Amazon ECS (simpler, AWS-only), AWS Fargate (no nodes), GKE/AKS on other clouds.

## How it works: the settings that matter

| Setting | Value here | Why |
|---|---|---|
| Kubernetes version | 1.37 | the newest version in standard support at build time |
| Subnets | private only | nodes never get public IPs |
| Control plane logs | api, audit, authenticator (7 days) | who did what in the cluster |
| Secrets encryption | a dedicated **KMS** key | Kubernetes secrets are encrypted with your key, not just at disk level |
| Authentication mode | `API` (**access entries**) | IAM identities mapped to Kubernetes permissions as code |
| Node group | 2 × t3.medium, Amazon Linux 2023, 20 GB gp3, encrypted | small, cheap, two zones |
| Instance metadata | **IMDSv2 required, hop limit 1** | pods cannot reach the node's AWS credentials |

### Access entries

Old EKS clusters mapped IAM users to Kubernetes users in a ConfigMap called `aws-auth`, edited by hand. **Access entries** do it through the EKS API, as code:
- the IAM user that ran Terraform becomes cluster admin (`enable_cluster_creator_admin_permissions = true`),
- the pipeline's role gets `AmazonEKSEditPolicy` **only in the namespace `profile-card`** (chapter 8).

### IMDSv2 and the hop limit

Every EC2 machine has an **instance metadata service (IMDS)** at `169.254.169.254`. It hands out, among other things, the machine's temporary AWS credentials. If a pod can reach it, a compromised app can steal the node's credentials.
- **IMDSv2 required** means you first need a session token (a `PUT` request), so simple tricks like SSRF with a `GET` do not work.
- **Hop limit 1** means the token's response packet can only travel one network hop: it reaches the node itself, but not a pod behind it.

Recorded from a pod in the cluster: the token request **timed out**, and the old token-less request was answered with **401**.

### Add-ons

| Add-on | Job |
|---|---|
| `vpc-cni` | gives pods VPC IP addresses; here also **enforces NetworkPolicies** (`enableNetworkPolicy = "true"`) |
| `coredns` | DNS inside the cluster |
| `kube-proxy` | Service networking on each node |
| `eks-pod-identity-agent` | lets pods get AWS permissions without keys (**Pod Identity**, chapter 10) |

**Pod Identity** replaces the older **IRSA** mechanism. IRSA needs an extra IAM OIDC provider per cluster; the project switches it off (`enable_irsa = false`), which is why the apply created 72 resources and not the 73 from the first plan. Fewer global IAM objects in a shared account is better.

## Where it is configured

[`terraform/eks.tf`](../terraform/eks.tf) (module `terraform-aws-modules/eks/aws` 21.26.0), shortened:

```hcl
module "eks" {
  name               = local.name
  kubernetes_version = var.kubernetes_version          # "1.37"
  subnet_ids         = module.vpc.private_subnets

  endpoint_public_access  = true                      # see chapter 6: an accepted risk
  endpoint_private_access = true

  enabled_log_types               = ["api", "audit", "authenticator"]
  encryption_config               = { resources = ["secrets"] }
  kms_key_deletion_window_in_days = 7

  enable_irsa                              = false
  authentication_mode                      = "API"
  enable_cluster_creator_admin_permissions = true

  eks_managed_node_groups = {
    default = {
      instance_types   = [var.node_instance_type]     # t3.medium
      min_size         = 2
      max_size         = 3
      desired_size     = 2
      metadata_options = { http_tokens = "required", http_put_response_hop_limit = 1 }
    }
  }
}
```

The same file creates the app **namespace** with Pod Security `restricted` (chapter 11) and the readiness gate label (chapter 12).

Recorded timings: control plane **8 min 44 s**, node group **1 min 59 s**. `kubectl get nodes -o wide` showed two Ready nodes, v1.37.0, in 10.42.14.x and 10.42.30.x (two zones), with **EXTERNAL-IP `<none>`**.

## Try it

```bash
aws eks update-kubeconfig --name eks-devsecops --region eu-central-1
kubectl get nodes -o wide
kubectl get pods -n kube-system
aws eks describe-cluster --name eks-devsecops \
  --query '{logs: cluster.logging.clusterLogging[?enabled].types | [0], auth: cluster.accessConfig.authenticationMode}'
```

Use a kubectl within one minor version of the cluster (1.36–1.38 for 1.37).

## Common mistakes

- Leaving IMDS reachable from pods (hop limit 2 is the default for many setups).
- Editing `aws-auth` by hand and locking yourself out.
- Giving the CI pipeline `cluster-admin` "to make it work".
- A kubectl that is too old or too new for the cluster version.

## Check yourself

1. What does AWS run for you in EKS, and what do you still decide?
2. What do access entries replace?
3. Why does a hop limit of 1 protect the node's credentials from pods?

### Answers

<details><summary>Answers</summary>

1. AWS runs the control plane (API server, etcd, scheduler) and manages the node machines' lifecycle; you decide the version, networking, node size and count, add-ons and permissions.
2. The `aws-auth` ConfigMap: IAM-to-Kubernetes mappings are now made through the EKS API (as code), with scoped access policies.
3. The IMDSv2 session token's response can only travel one network hop. A pod's traffic passes an extra hop (its own network namespace), so it never receives the token and cannot read the credentials.

</details>

Next: [5. Containers for the app](05-containers-for-the-app.md)
