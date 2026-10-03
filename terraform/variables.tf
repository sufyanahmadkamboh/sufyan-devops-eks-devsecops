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
