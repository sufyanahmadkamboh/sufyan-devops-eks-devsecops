variable "region" {
  description = "AWS region. This project is built for one region only."
  type        = string
  default     = "eu-central-1"

  validation {
    condition     = var.region == "eu-central-1"
    error_message = "This project only runs in eu-central-1 (Frankfurt)."
  }
}

variable "allowed_account_id" {
  description = "The only AWS account Terraform may touch (a guard against a wrong profile). Set TF_VAR_allowed_account_id."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^[0-9]{12}$", var.allowed_account_id))
    error_message = "allowed_account_id must be a 12-digit AWS account ID."
  }
}

variable "github_repository" {
  description = "owner/name of the GitHub repository whose production environment may deploy."
  type        = string
  default     = "sufyanahmadkamboh/sufyan-devops-eks-devsecops"
}

variable "github_oidc_subject_prefix" {
  description = <<-EOT
    Prefix of the GitHub OIDC "sub" claim. New repositories use immutable IDs (owner@id/repo@id), so a deleted and
    re-created repository with the same name cannot assume the role. Read it with:
    gh api repos/OWNER/REPO/actions/oidc/customization/sub
  EOT
  type        = string
  default     = "repo:sufyanahmadkamboh@25397028/sufyan-devops-eks-devsecops@1403679100"
}

variable "create_github_oidc_provider" {
  description = <<-EOT
    Create the GitHub OIDC identity provider. Only for an account that has none yet: the provider is shared by every
    repository in the account, so where one exists (as in the account this was built in) it is only read, never changed.
  EOT
  type        = bool
  default     = false
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version."
  type        = string
  default     = "1.37"
}

variable "node_instance_type" {
  description = "Instance type of the managed node group."
  type        = string
  default     = "t3.medium"
}

variable "app_namespace" {
  description = "Namespace the pipeline deploys into (and the only one it may change)."
  type        = string
  default     = "profile-card"
}
