# 8. OIDC and least privilege

## What is it?

- **OIDC** (OpenID Connect) is a standard for proving identity with signed **tokens**. GitHub Actions can give each job a token that says, in a signed way: "I am a job of repository X, running workflow Y, on branch/environment Z".
- AWS can **trust** GitHub as an **identity provider**: a job sends its token to AWS STS (`AssumeRoleWithWebIdentity`) and receives **temporary credentials** for an IAM role, valid for one hour at most.
- **Least privilege** means every identity gets only the permissions it needs, nothing more.

## Why this project uses it

The classic way is to create an IAM user, generate an access key and store it as a GitHub secret. Those keys never expire on their own, get copied around, and leaked cloud keys are one of the most common causes of cloud breaches. With OIDC **there is no AWS key to steal**: the credentials are created per job and expire.

## How it works

1. The deploy job has `permissions: id-token: write`, so it may request a token.
2. `aws-actions/configure-aws-credentials` (pinned to a commit SHA) sends the token to AWS STS with the role ARN.
3. AWS checks the token's signature against the **identity provider** `token.actions.githubusercontent.com`, then checks the role's **trust policy** conditions.
4. If everything matches, STS returns credentials valid for this job only.

### The trust policy

[`terraform/ecr-and-github.tf`](../terraform/ecr-and-github.tf):

```hcl
# The provider is shared by the whole account: read it (default), or create it in a fresh account.
data "aws_iam_openid_connect_provider" "github" {
  count = var.create_github_oidc_provider ? 0 : 1
  url   = "https://token.actions.githubusercontent.com"   # existing and shared: read, never changed
}

data "aws_iam_policy_document" "github_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [local.github_oidc_provider_arn]   # the read or the created provider
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["${var.github_oidc_subject_prefix}:environment:production"]
    }
  }
}
```

- **`aud` (audience)** must be `sts.amazonaws.com`: the token was meant for AWS.
- **`sub` (subject)** must be this repository, running in its **`production` environment**. That GitHub environment only accepts deployments from the `main` branch. A pull request, a fork or another branch gets a different subject and is refused.
- The account already had a GitHub identity provider used by other teams, so Terraform only **reads** it with a data source. It is never modified or deleted.

### The real failure: GitHub's immutable subject

The first deployment failed:

```
Could not assume role with OIDC: Not authorized to perform sts:AssumeRoleWithWebIdentity
```

The trust policy expected `repo:sufyanahmadkamboh/sufyan-devops-eks-devsecops:environment:production`. But new GitHub repositories use an **immutable subject** that includes the numeric IDs of the owner and the repository:

```
repo:sufyanahmadkamboh@25397028/sufyan-devops-eks-devsecops@1403679100:environment:production
```

You can read it with `gh api repos/OWNER/REPO/actions/oidc/customization/sub`. This is a security improvement: if someone deletes the repository and creates a new one with the same name, it gets a different ID and **cannot** assume the role. The fix was one variable, `github_oidc_subject_prefix`.

### What the role may do in AWS

Simplified from `data "aws_iam_policy_document" "github_deploy"`:

```text
statement { actions = ["ecr:GetAuthorizationToken"]  resources = ["*"] }   # no resource-level support
statement {                                                                   # push to ONE repository
  actions   = ["ecr:BatchCheckLayerAvailability", "ecr:PutImage", "ecr:InitiateLayerUpload",
               "ecr:UploadLayerPart", "ecr:CompleteLayerUpload", "ecr:BatchGetImage",
               "ecr:DescribeImages", "ecr:DescribeImageScanFindings", "ecr:GetDownloadUrlForLayer"]
  resources = [aws_ecr_repository.app.arn]
}
statement { actions = ["eks:DescribeCluster"]  resources = [module.eks.cluster_arn] }
```

### What the role may do in Kubernetes

An EKS **access entry** ([`terraform/eks.tf`](../terraform/eks.tf)) maps the role to `AmazonEKSEditPolicy` with `access_scope = { type = "namespace", namespaces = ["profile-card"] }`: it may create and change Deployments, Services, Ingresses and so on, **only in `profile-card`**. It cannot even create that namespace; Terraform (the platform) owns it.

### Proving it on every deploy

The deploy job checks its own permissions with `kubectl auth can-i` and fails if any answer is unexpected. Recorded output:

```
can-i create deployments -n profile-card -> yes (expected yes)
can-i create deployments -n kube-system -> no (expected no)
can-i get secrets -n kube-system -> no (expected no)
can-i create clusterrolebindings -> no (expected no)
can-i delete namespaces -> no (expected no)
```

## Try it

```bash
gh api repos/<you>/<your-fork>/actions/oidc/customization/sub     # your subject prefix
terraform -chdir=terraform output -raw github_deploy_role_arn | gh secret set AWS_DEPLOY_ROLE_ARN --env production
aws iam get-role --role-name eks-devsecops-github-deploy --query 'Role.AssumeRolePolicyDocument'
```

## Common mistakes

- A trust policy with `StringLike` and `repo:owner/*`: every repository of the owner (and every branch) can assume the role.
- Forgetting the `aud` condition.
- Using the old `repo:owner/name` subject for a new repository (the failure above).
- Giving the deploy role `AdministratorAccess` and the cluster-admin policy "for now".
- Deleting or "fixing" a shared identity provider in a company account.

## Check yourself

1. What is stored in GitHub so the pipeline can reach AWS?
2. Why does the subject include `environment:production`?
3. Name two things the deploy role cannot do in the cluster, and how that is proven.

### Answers

<details><summary>Answers</summary>

1. Only the role's ARN (as a secret, to keep the account ID out of public logs). No access key, no password.
2. Only jobs that run in the protected `production` environment, which accepts only the `main` branch, get that subject. Pull requests and other branches cannot assume the role.
3. For example: create deployments in `kube-system`, read secrets in `kube-system`, create cluster role bindings, delete namespaces. Every deploy runs `kubectl auth can-i` for these and fails if any answer is "yes".

</details>

Next: [9. The deploy pipeline](09-deploy-pipeline.md)
