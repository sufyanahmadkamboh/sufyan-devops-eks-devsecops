locals {
  name = "eks-devsecops"

  # Every resource carries these tags: teardown is verified by searching for Project=eks-devsecops.
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

# Short-lived token for the Kubernetes and Helm providers, from the same AWS credentials.
locals {
  kube_exec = {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name, "--region", var.region]
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  exec {
    api_version = local.kube_exec.api_version
    command     = local.kube_exec.command
    args        = local.kube_exec.args
  }
}

provider "helm" {
  kubernetes = {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    exec                   = local.kube_exec
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}
