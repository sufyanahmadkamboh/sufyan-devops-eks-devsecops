# 1. AWS basics for this project

## What is it?

**Amazon Web Services (AWS)** rents out computers, networks and managed services by the hour. A few ideas are enough for this project:

| Idea | Meaning |
|---|---|
| **Account** | your container for all AWS resources and the bill; identified by a 12-digit number |
| **Region** | a geographic area with its own data centers, for example `eu-central-1` (Frankfurt) |
| **Availability zone (AZ)** | one or more separate data centers inside a region; a region has at least three |
| **IAM** | Identity and Access Management: *who* (users, roles) may do *what* (policies) on *which* resources |
| **IAM role** | an identity without a password that someone or something can **assume** to get temporary credentials |
| **Tag** | a key/value label on a resource, for example `Project=eks-devsecops` |

## Why this project cares

- **One region only.** The project was built in an account that other people use. Working in exactly one region (Frankfurt) keeps the project away from everything else, and makes cleanup easy to verify.
- **Two availability zones.** If one data center fails, the app keeps running in the other one.
- **IAM is global.** Unlike most resources, IAM roles and policies are not tied to a region. EKS cannot work without IAM roles, so the project creates a few **uniquely named** ones (all starting with `eks-devsecops`) and deletes them at the end.
- **Tags on everything.** Every resource gets `Project=eks-devsecops`, `Owner=sufyan`, `ManagedBy=terraform`. At the end, a script searches for these tags to prove nothing was left behind.

## How it works

### Regions and AZs

```
eu-central-1 (Frankfurt)
├── eu-central-1a  ─ private subnet 10.42.0.0/20,  public subnet 10.42.48.0/24
└── eu-central-1b  ─ private subnet 10.42.16.0/20, public subnet 10.42.49.0/24
```

Terraform picks the first two available zones of the region (`slice(data.aws_availability_zones.available.names, 0, 2)` in [`terraform/vpc.tf`](../terraform/vpc.tf)).

### IAM: principals, policies, roles

- A **principal** is someone or something that makes requests: an IAM user, a role, an AWS service.
- A **policy** is a JSON document: *allow these actions on these resources, under these conditions*.
- A **trust policy** is attached to a role and says *who may assume it*. In chapter 8 the trust policy says: "only GitHub Actions jobs of this repository, in its `production` environment".

### Cost

You pay for most things **per hour** while they exist. This lab's main costs in Frankfurt, at on-demand prices:

| Item | About |
|---|---|
| EKS control plane | $0.10 / hour |
| 2 × t3.medium worker nodes | $0.10 / hour |
| NAT gateway | $0.05 / hour + data |
| Load balancer, public IPv4 addresses, logs, KMS key | ~$0.05 / hour |

That is **roughly $0.30 per hour**. The recorded build ran 62 minutes: an estimated $0.35. A forgotten lab costs about $7 per day, so deleting it matters (chapter 13).

## Where it is configured

[`terraform/main.tf`](../terraform/main.tf) applies the tags to every resource the AWS provider creates:

```hcl
locals {
  name = "eks-devsecops"
  tags = {
    Project    = "eks-devsecops"
    Owner      = "sufyan"
    ManagedBy  = "terraform"
    Repository = "github.com/${var.github_repository}"
  }
}

provider "aws" {
  region              = var.region
  allowed_account_ids = [var.allowed_account_id]
  default_tags {
    tags = local.tags
  }
}
```

[`terraform/variables.tf`](../terraform/variables.tf) refuses any region but Frankfurt:

```hcl
variable "region" {
  default = "eu-central-1"
  validation {
    condition     = var.region == "eu-central-1"
    error_message = "This project only runs in eu-central-1 (Frankfurt)."
  }
}
```

## Try it

With the AWS CLI configured for **your own** account:

```bash
aws sts get-caller-identity --query Arn           # who am I?
aws ec2 describe-availability-zones --region eu-central-1 --query 'AvailabilityZones[].ZoneName'
aws ec2 describe-vpcs --region eu-central-1 --query 'length(Vpcs)'   # take an inventory before you start
```

Write the inventory down: after the teardown you compare against it.

## Common mistakes

- Running commands with the wrong profile or account. Terraform's `allowed_account_ids` guard prevents that.
- Forgetting that IAM is global: deleting "everything in the region" does not delete IAM roles.
- Leaving a lab running overnight.
- Sharing screenshots that show the account ID in ARNs or registry hostnames.

## Check yourself

1. What is the difference between a region and an availability zone?
2. Why does the project use two availability zones?
3. Which part of this project is *not* regional, and how is it kept separate from other people's resources?

### Answers

<details><summary>Answers</summary>

1. A region is a geographic area (Frankfurt); an availability zone is an isolated data center (or group of them) inside a region.
2. So that the loss of one data center does not take the app down: one replica runs in each zone.
3. IAM (roles and policies). The project gives every IAM name the prefix `eks-devsecops` and tags them, and the teardown verification checks both.

</details>

Next: [2. VPC networking](02-vpc-networking.md)
