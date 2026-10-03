output "region" {
  value = var.region
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "app_namespace" {
  value = var.app_namespace
}

# These contain the account ID: marked sensitive so they are not printed (read with `terraform output -raw`).
output "ecr_repository_url" {
  value     = aws_ecr_repository.app.repository_url
  sensitive = true
}

output "github_deploy_role_arn" {
  value     = aws_iam_role.github_deploy.arn
  sensitive = true
}
