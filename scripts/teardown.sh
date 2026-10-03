#!/usr/bin/env bash
# Removes everything this project created, in the order that leaves nothing behind:
#   1. delete the Ingress, so the Load Balancer Controller deletes the ALB, its target groups and security groups
#      (Terraform did not create those, so `terraform destroy` alone would leave them and fail on the VPC)
#   2. terraform destroy
#   3. scripts/verify-teardown.sh
# Requires: AWS credentials for the same account, TF_VAR_allowed_account_id set. Region is fixed to eu-central-1.
set -euo pipefail
cd "$(dirname "$0")/.."

export AWS_REGION=eu-central-1 AWS_DEFAULT_REGION=eu-central-1
CLUSTER=eks-devsecops
NAMESPACE=profile-card
ALB=eks-devsecops-profile-card

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

if aws eks describe-cluster --name "$CLUSTER" >/dev/null 2>&1; then
  aws eks update-kubeconfig --name "$CLUSTER" >/dev/null
  log "Deleting the Ingress (the controller removes the load balancer)"
  kubectl -n "$NAMESPACE" delete ingress --all --ignore-not-found --wait=true
  for _ in $(seq 1 60); do
    if ! aws elbv2 describe-load-balancers --names "$ALB" >/dev/null 2>&1; then break; fi
    sleep 5
  done
  if aws elbv2 describe-load-balancers --names "$ALB" >/dev/null 2>&1; then
    echo "the load balancer $ALB still exists; not continuing" >&2
    exit 1
  fi
  log "Load balancer deleted"
  # Give the controller a moment to remove its security groups before the VPC goes.
  sleep 30
fi

log "terraform destroy"
terraform -chdir=terraform destroy -input=false -auto-approve

scripts/verify-teardown.sh
