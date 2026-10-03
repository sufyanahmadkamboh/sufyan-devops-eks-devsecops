module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "21.26.0"

  name               = local.name
  kubernetes_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # GitHub-hosted runners deploy over the public endpoint, authenticated by IAM (no static credentials).
  # Production alternative: private endpoint only, with self-hosted runners inside the VPC.
  endpoint_public_access  = true
  endpoint_private_access = true

  # Control plane audit logs, and Kubernetes secrets encrypted with a dedicated KMS key.
  enabled_log_types                      = ["api", "audit", "authenticator"]
  cloudwatch_log_group_retention_in_days = 7
  encryption_config                      = { resources = ["secrets"] }
  kms_key_deletion_window_in_days        = 7

  # Access entries instead of the aws-auth ConfigMap. The creator (the IAM user running Terraform) is admin.
  authentication_mode                      = "API"
  enable_cluster_creator_admin_permissions = true

  access_entries = {
    # The pipeline may only edit objects inside the app namespace: not other namespaces, not cluster settings.
    github_deploy = {
      principal_arn = aws_iam_role.github_deploy.arn
      policy_associations = {
        app_namespace = {
          policy_arn   = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy"
          access_scope = { type = "namespace", namespaces = [var.app_namespace] }
        }
      }
    }
  }

  addons = {
    coredns    = {}
    kube-proxy = {}
    vpc-cni = {
      before_compute = true
      # Turns on enforcement of Kubernetes NetworkPolicies.
      configuration_values = jsonencode({ enableNetworkPolicy = "true" })
    }
    eks-pod-identity-agent = { before_compute = true }
  }

  eks_managed_node_groups = {
    default = {
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = [var.node_instance_type]
      min_size       = 2
      max_size       = 3
      desired_size   = 2

      # IMDSv2 only, and a hop limit of 1: pods cannot reach the node's instance metadata credentials.
      metadata_options = {
        http_endpoint               = "enabled"
        http_tokens                 = "required"
        http_put_response_hop_limit = 1
      }

      block_device_mappings = {
        xvda = {
          device_name = "/dev/xvda"
          ebs = {
            volume_size           = 20
            volume_type           = "gp3"
            encrypted             = true
            delete_on_termination = true
          }
        }
      }
    }
  }
}

# The platform owns the namespace and its Pod Security level; the pipeline only deploys into it.
resource "kubernetes_namespace_v1" "app" {
  metadata {
    name = var.app_namespace
    labels = {
      "pod-security.kubernetes.io/enforce"         = "restricted"
      "pod-security.kubernetes.io/enforce-version" = "latest"
      "pod-security.kubernetes.io/warn"            = "restricted"
      "pod-security.kubernetes.io/audit"           = "restricted"
    }
  }

  depends_on = [module.eks]
}
