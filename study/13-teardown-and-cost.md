# 13. Teardown and cost

## What is it?

**Teardown** means deleting everything a project created. **Verification** means proving it, instead of assuming it.

## Why it matters

- A forgotten lab costs about $7 per day here, and much more with bigger clusters.
- In a shared account, leftovers confuse other people and can block their work (quotas, overlapping names).
- "I ran destroy" is not proof: some resources are created outside Terraform, and some are global.

## How it works

### The order matters

[`scripts/teardown.sh`](../scripts/teardown.sh):

1. **Delete the Ingress** and wait until the ALB `eks-devsecops-profile-card` no longer exists. The ALB, its target groups and security groups were created by the controller, not by Terraform. If Terraform deleted the controller first, they would be left behind, and the VPC could not be deleted.
2. **`terraform destroy`.**
3. **`scripts/verify-teardown.sh`.**

Before starting, switch the pipeline off (`gh variable set DEPLOY_ENABLED --body false`) so a push cannot deploy into a cluster that is being deleted.

Recorded:

```
==> Deleting the Ingress (the controller removes the load balancer)
==> Load balancer deleted
module.vpc.aws_nat_gateway.this[0]: Destruction complete after 1m20s
module.eks.aws_eks_cluster.this[0]: Destruction complete after 3m29s
Destroy complete! Resources: 72 destroyed.
```

### The verification script

[`scripts/verify-teardown.sh`](../scripts/verify-teardown.sh) only **reads**. It checks, in eu-central-1:
EKS cluster, VPC, subnets, NAT gateways, Elastic IPs, EC2 instances, network interfaces, security groups, the load balancer and its target groups, the ECR repository, CloudWatch log groups, the KMS alias, and anything else tagged `Project=eks-devsecops`. Then the global IAM roles and policies, and finally that the **shared GitHub OIDC provider still exists**.

Two lessons from the real run made the script better:

1. **Module-generated names.** The EKS and VPC modules named some IAM roles `default-eks-node-group-…` and `vpc-flow-log-role-…`, without the project prefix. A check for `eks-devsecops*` would have missed them. Now the script checks those prefixes too, but counts a role or policy only if it carries the tag `Project=eks-devsecops`, so another team's similarly named roles never cause a false alarm. Terraform now also gives every IAM name the `eks-devsecops` prefix.
2. **The tagging index lags.** Right after the destroy, the Resource Groups Tagging API still listed 4 tagged resources: a NAT gateway (state `deleted`), a flow log and a security group (both already gone), and the KMS key. The script now checks each tagged item's **real state**.

The **KMS key** is special: AWS never deletes a key immediately. It goes to `PendingDeletion` for at least 7 days (here: deleted on 2026-10-11). A key waiting for deletion is not billed and cannot be used.

Final recorded result:

```
  gone  EKS cluster  …  gone  anything else tagged Project=eks-devsecops
  gone  IAM roles    gone  IAM policies
  kept  GitHub OIDC identity provider
Clean: nothing of this project is left.
```

And the region inventory taken before the project matched exactly afterwards: 1 VPC (the default one), 0 Elastic IPs, 0 NAT gateways, 0 clusters, 0 load balancers, 0 ECR repositories, 0 instances.

### What it cost

| Item | Approximate price in eu-central-1 |
|---|---|
| EKS control plane | $0.10 / hour |
| 2 × t3.medium | $0.10 / hour |
| NAT gateway | $0.05 / hour + data |
| ALB, public IPv4, logs, KMS | ~$0.05 / hour |

From the first `terraform apply` to the verified teardown: **62 minutes**, so an estimated **$0.35**. These are on-demand list prices; the AWS bill (Cost Explorer, usually within 24 hours) is the final word.

## Try it

```bash
gh variable set DEPLOY_ENABLED --body false
export TF_VAR_allowed_account_id=<your account id>
scripts/teardown.sh
scripts/verify-teardown.sh          # safe to run any time, read-only
gh secret delete AWS_DEPLOY_ROLE_ARN --env production
```

## Common mistakes

- `terraform destroy` before deleting the Ingress (the VPC deletion fails).
- Checking only one region, or forgetting IAM.
- Trusting the tagging API without checking each resource's real state.
- Deleting resources by name pattern in a shared account (you may hit someone else's).
- Forgetting the GitHub secret and variable after the cloud side is gone.

## Check yourself

1. Why is the Ingress deleted before `terraform destroy`?
2. Why does the verification check tags as well as name prefixes for IAM?
3. The KMS key still exists after the teardown. Is that a leftover?

### Answers

<details><summary>Answers</summary>

1. The ALB and its security groups were created by the Load Balancer Controller. Deleting the Ingress lets the controller remove them; otherwise they stay behind and block the VPC deletion.
2. Name prefixes find the candidates (including module-generated names); the tag proves they belong to this project, so other teams' roles with similar names are never reported or touched.
3. No. AWS requires a waiting period of at least 7 days before deleting a key; it is in `PendingDeletion`, cannot be used, and is not billed.

</details>

Next: [14. Hands-on labs](14-hands-on-labs.md)
