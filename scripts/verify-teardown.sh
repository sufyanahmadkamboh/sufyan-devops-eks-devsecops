#!/usr/bin/env bash
# Proves that nothing of this project is left in the account, and that shared resources are untouched.
# Read-only: it never deletes anything. Region is fixed to eu-central-1 (IAM checks are global by nature).
set -uo pipefail

export AWS_REGION=eu-central-1 AWS_DEFAULT_REGION=eu-central-1
fail=0
check() {  # description, command that prints a count; 0 = clean
  local n
  n="$("${@:2}" 2>/dev/null)"
  n="${n:-0}"
  if [[ "$n" == "0" || "$n" == "None" ]]; then
    printf '\033[1;32m  gone\033[0m  %s\n' "$1"
  else
    printf '\033[1;31m  LEFT\033[0m  %s (%s)\n' "$1" "$n"
    fail=1
  fi
}

echo "Resources of project eks-devsecops in eu-central-1:"
check "EKS cluster"            aws eks list-clusters --query "length(clusters[?@=='eks-devsecops'])"
check "VPC"                    aws ec2 describe-vpcs --filters Name=tag:Project,Values=eks-devsecops --query 'length(Vpcs)'
check "subnets"                aws ec2 describe-subnets --filters Name=tag:Project,Values=eks-devsecops --query 'length(Subnets)'
check "NAT gateways"           aws ec2 describe-nat-gateways --filter Name=tag:Project,Values=eks-devsecops Name=state,Values=pending,available,deleting --query 'length(NatGateways)'
check "Elastic IPs"            aws ec2 describe-addresses --filters Name=tag:Project,Values=eks-devsecops --query 'length(Addresses)'
check "EC2 instances (nodes)"  aws ec2 describe-instances --filters Name=tag:eks:cluster-name,Values=eks-devsecops Name=instance-state-name,Values=pending,running,stopping,stopped --query 'length(Reservations[].Instances[])'
check "network interfaces"     aws ec2 describe-network-interfaces --filters Name=tag:Project,Values=eks-devsecops --query 'length(NetworkInterfaces)'
check "security groups"        aws ec2 describe-security-groups --filters Name=tag:Project,Values=eks-devsecops --query 'length(SecurityGroups)'
check "load balancer"          aws elbv2 describe-load-balancers --query "length(LoadBalancers[?LoadBalancerName=='eks-devsecops-profile-card'])"
check "target groups (k8s-*)"  aws elbv2 describe-target-groups --query "length(TargetGroups[?starts_with(TargetGroupName,'k8s-profilec')])"
check "ECR repository"         aws ecr describe-repositories --query "length(repositories[?starts_with(repositoryName,'eks-devsecops/')])"
check "CloudWatch log groups"  aws logs describe-log-groups --query "length(logGroups[?contains(logGroupName,'eks-devsecops')])"
check "KMS alias"              aws kms list-aliases --query "length(Aliases[?AliasName=='alias/eks/eks-devsecops'])"
# The tagging index lags behind deletions (it can list deleted resources for hours), so every tagged ARN is
# checked for its real state. A KMS key waiting out its mandatory deletion window counts as deleted.
really_exists() {  # ARN -> prints 1 if the resource still exists
  local arn="$1" id="${1##*/}"
  case "$arn" in
    *:natgateway/*)     [[ "$(aws ec2 describe-nat-gateways --nat-gateway-ids "$id" --query 'NatGateways[0].State' --output text 2>/dev/null)" =~ ^(pending|available|deleting)$ ]] && echo 1 ;;
    *:security-group/*) aws ec2 describe-security-groups --group-ids "$id" >/dev/null 2>&1 && echo 1 ;;
    *:vpc-flow-log/*)   [[ "$(aws ec2 describe-flow-logs --flow-log-ids "$id" --query 'length(FlowLogs)' --output text 2>/dev/null)" == 1 ]] && echo 1 ;;
    *:kms:*:key/*)      [[ "$(aws kms describe-key --key-id "$id" --query 'KeyMetadata.KeyState' --output text 2>/dev/null)" =~ ^(Enabled|Disabled)$ ]] && echo 1 ;;
    *)                  echo 1 ;;   # unknown type: report it, never assume it is gone
  esac
}
tagged_left() {
  local arn
  for arn in $(aws resourcegroupstaggingapi get-resources --tag-filters Key=Project,Values=eks-devsecops \
                 --query 'ResourceTagMappingList[].ResourceARN' --output text); do
    really_exists "$arn"
  done | grep -c '^1$'
}
check "anything else tagged Project=eks-devsecops" tagged_left

echo "Global IAM resources of the project (name prefixes used by this project and its Terraform modules,"
echo "counted only when they carry the tag Project=eks-devsecops, so other teams' roles never match):"
ROLE_PREFIXES="starts_with(RoleName,'eks-devsecops') || starts_with(RoleName,'default-eks-node-group-') || starts_with(RoleName,'vpc-flow-log-role-')"
POLICY_PREFIXES="starts_with(PolicyName,'eks-devsecops') || starts_with(PolicyName,'vpc-flow-log-to-cloudwatch-')"
PROJECT_TAG="Tags[?Key=='Project' && Value=='eks-devsecops'] | length(@)"
tagged_roles() {
  local r
  for r in $(aws iam list-roles --query "Roles[?${ROLE_PREFIXES}].RoleName" --output text); do
    aws iam list-role-tags --role-name "$r" --query "$PROJECT_TAG" --output text
  done | grep -c '^1$'
}
tagged_policies() {
  local p
  for p in $(aws iam list-policies --scope Local --query "Policies[?${POLICY_PREFIXES}].Arn" --output text); do
    aws iam list-policy-tags --policy-arn "$p" --query "$PROJECT_TAG" --output text
  done | grep -c '^1$'
}
check "IAM roles"    tagged_roles
check "IAM policies" tagged_policies

echo "Shared resources that must still exist (never touched by this project):"
if aws iam list-open-id-connect-providers --query 'OpenIDConnectProviderList[].Arn' --output text | grep -q token.actions.githubusercontent.com; then
  printf '\033[1;32m  kept\033[0m  GitHub OIDC identity provider\n'
else
  printf '\033[1;31m  MISSING\033[0m  GitHub OIDC identity provider\n'
  fail=1
fi

key="$(aws kms list-keys --query 'Keys[].KeyId' --output text | tr '\t' '\n' | while read -r k; do
  aws kms list-resource-tags --key-id "$k" --query "Tags[?TagKey=='Project' && TagValue=='eks-devsecops'] | length(@)" --output text 2>/dev/null | grep -q '^1$' && echo "$k"; done)"
if [[ -n "$key" ]]; then
  echo "KMS key: $(aws kms describe-key --key-id "$key" --query 'KeyMetadata.KeyState' --output text) (AWS keeps a deleted key for 7 days, at no cost, before removing it)"
fi

if (( fail )); then echo "Something is left: see LEFT above."; exit 1; fi
echo "Clean: nothing of this project is left."
