# Runbook

## Deploy
Merge to `main`. `deploy.yaml` builds, scans, signs and deploys the exact digest, then smoke-tests the ALB. Manual
re-deploy: Actions → deploy → Run workflow (main).

## Roll back
`git revert` the bad commit and push: the pipeline deploys the previous code as a new, scanned image. For an
immediate rollback, `kubectl -n profile-card rollout undo deployment/profile-card` (the next push re-applies git).

## Scale
`replicas` in `k8s/deployment.yaml` (keep ≥ 2 for the PDB and both zones). Nodes: `min_size`/`max_size`/`desired_size`
in `terraform/eks.tf`.

## Upgrade Kubernetes
Raise `kubernetes_version` one minor version at a time; `terraform apply` upgrades the control plane, then the node
group. Check add-on versions and the kubectl skew afterwards.

## Access
- Admin: the IAM principal that ran Terraform (access entry `cluster_creator`). Add more admins as access entries.
- Pipeline: role `eks-devsecops-github-deploy`, namespace-scoped `AmazonEKSEditPolicy`. Verified by every deployment.
- No static AWS keys exist for the pipeline. Rotate the operator's own keys regularly.

## Security exceptions
`.trivyignore.yaml` lists accepted risks with an expiry date. When one expires, CI fails: re-review it, fix it, or
renew it with a reason.

## Teardown (do this the same day in a lab)
```bash
gh variable set DEPLOY_ENABLED --body false   # stop deployments first
scripts/teardown.sh                            # Ingress → ALB gone → terraform destroy → verification
gh secret delete AWS_DEPLOY_ROLE_ARN --env production
```
`scripts/verify-teardown.sh` can be run on its own at any time; it only reads.
