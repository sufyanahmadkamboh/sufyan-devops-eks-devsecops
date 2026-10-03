# 3. Terraform

## What is it?

**Terraform** builds infrastructure from text files. You describe *what* should exist (a VPC, a cluster, a role); Terraform works out *how* to create, change or delete it.

| Idea | Meaning |
|---|---|
| **Provider** | a plugin that talks to one API: `hashicorp/aws`, `hashicorp/helm`, `hashicorp/kubernetes` |
| **Resource** | one thing Terraform manages, e.g. `aws_ecr_repository.app` |
| **Data source** | something Terraform only **reads**, e.g. the existing GitHub OIDC provider |
| **Module** | a reusable package of resources, e.g. `terraform-aws-modules/eks/aws` |
| **State** | Terraform's record of what it created (`terraform.tfstate`) |
| **plan** | a preview: what will be added, changed and destroyed |
| **apply** | do it |
| **destroy** | delete everything in the state |

## Why this project uses it

- **Reviewable:** infrastructure changes are pull requests, not clicks.
- **Repeatable:** every student gets the same platform.
- **Destroyable:** one command deletes all 72 resources; you cannot forget one in a console.

**Alternatives:** AWS CloudFormation or CDK (AWS only), Pulumi (general-purpose languages), `eksctl` (EKS only, quick but less control), OpenTofu (an open-source fork of Terraform).

## How it works

1. `terraform init` downloads providers and modules (pinned versions, recorded in `.terraform.lock.hcl`).
2. `terraform plan -out=tfplan` compares your files with the state and the real world, and saves the plan.
3. **Read the plan.** The recorded plan ended with **`Plan: 73 to add, 0 to change, 0 to destroy.`** In a shared account, "0 to change, 0 to destroy" is your proof that you will not touch anyone else's resources.
4. `terraform apply tfplan` executes exactly that plan. Recorded: **72 resources in 12 minutes 30 seconds** (one module feature was switched off after the first plan, see chapter 4).
5. `terraform destroy` deletes them again (chapter 13).

### State

The state file contains resource IDs and the account number, so it is **never committed** (`.gitignore` lists `*.tfstate`). For one operator and a short-lived lab, local state is fine. A team keeps state in **S3 with locking**, so two people cannot apply at the same time.

## Where it is configured

| File | Contents |
|---|---|
| [`versions.tf`](../terraform/versions.tf) | Terraform ≥ 1.10; providers aws ~> 6.67, helm ~> 3.3, kubernetes ~> 3.3 |
| [`variables.tf`](../terraform/variables.tf) | region (validated), allowed account, repository, OIDC subject prefix, versions |
| [`main.tf`](../terraform/main.tf) | tags, provider configuration, token for Kubernetes/Helm |
| [`vpc.tf`](../terraform/vpc.tf) | the network (chapter 2) |
| [`eks.tf`](../terraform/eks.tf) | the cluster and the app namespace (chapter 4) |
| [`load-balancer-controller.tf`](../terraform/load-balancer-controller.tf) | IAM, Pod Identity and the Helm release (chapter 10) |
| [`ecr-and-github.tf`](../terraform/ecr-and-github.tf) | the registry and the pipeline's role (chapters 8, 9) |
| [`outputs.tf`](../terraform/outputs.tf) | values to read after apply; the ones containing the account ID are `sensitive` |

### Guard rails for a shared account

```hcl
provider "aws" {
  region              = var.region                 # only eu-central-1 passes validation
  allowed_account_ids = [var.allowed_account_id]   # any other account: Terraform refuses to run
  default_tags { tags = local.tags }
}
```

`allowed_account_id` has no default: you set it with `export TF_VAR_allowed_account_id=<12 digits>`, so it never lands in git.

### Talking to Kubernetes from Terraform

The `kubernetes` and `helm` providers authenticate to the new cluster with a short-lived token from `aws eks get-token`, using the same AWS credentials. That is how Terraform creates the app namespace and installs the load balancer controller in the same run.

## Try it

```bash
cd terraform
terraform init -backend=false && terraform validate     # no AWS account needed
terraform fmt -check -recursive
export TF_VAR_allowed_account_id=<your account id>
terraform plan -out=tfplan                                # read the last line before applying
```

## Common mistakes

- Running `apply` without reading the plan.
- Committing `terraform.tfstate` or `*.tfvars` with real values.
- Unpinned module versions: a new module release changes your infrastructure without a code change.
- Resources created outside Terraform (here: the load balancer, created by a controller) block `destroy` later.

## Check yourself

1. What does "0 to change, 0 to destroy" in a plan tell you?
2. Why is the account ID passed as an environment variable and not written in a file?
3. Why would two people running `apply` with local state be dangerous?

### Answers

<details><summary>Answers</summary>

1. That Terraform will only create new resources and will not modify or delete anything that already exists in its state.
2. To keep it out of git (and out of screenshots), and so that the same code can be used by anyone with their own account.
3. Each has their own state file: they do not see each other's changes and can create duplicates or delete each other's resources. Remote state with locking prevents this.

</details>

Next: [4. Amazon EKS](04-amazon-eks.md)
