# 14. Hands-on labs

Nine labs. **Labs 1–4 are free** and run on your computer with Docker. **Labs 5–9 run in your own AWS account and cost money** (roughly $0.30 per hour while the platform exists).

> ⚠️ **Before lab 5:** use your **own** AWS account, never an employer's account without permission. Plan the AWS labs for one sitting, and **always finish with lab 9 (teardown) the same day.**

All commands run from the repository root, in bash (Git Bash on Windows). Compare what you see with [`docs/test-results.md`](../docs/test-results.md).

## Lab 1: Build and harden the image locally (free)

```bash
docker build -t profile-card:local --build-arg VERSION=0.1.0 --build-arg COMMIT=abcdef1 app
docker run -d --name pc --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges -p 18080:8080 profile-card:local
curl -sI localhost:18080/ ; curl -s localhost:18080/healthz ; docker exec pc id
docker rm -f pc
```

1. Which user does nginx run as? Which security headers do you see?
2. Remove `--tmpfs /tmp` and start it again. What happens, and why does the Kubernetes Deployment mount an `emptyDir` at `/tmp`?
3. `cd app && npm ci && npm test`: which 5 behaviours do the tests check?

## Lab 2: Be the vulnerability gate (free)

```bash
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.75.0 \
  image --severity CRITICAL,HIGH --ignore-unfixed profile-card:local
```

1. Comment out the `RUN apk upgrade --no-cache` line (and the `USER 0` above it) in `app/Dockerfile`, rebuild, scan again. Is anything found today? If yes, which package and which fixed version?
2. Scan once without `--ignore-unfixed`. How many more findings appear, and why does the pipeline not block on them?
3. Undo your change: `git checkout -- app/Dockerfile`.

## Lab 3: Break the Dockerfile, let the checks catch it (free)

```bash
docker run --rm -i hadolint/hadolint:v2.15.1 < app/Dockerfile        # clean
printf '\nUSER root\n' >> app/Dockerfile
docker run --rm -i hadolint/hadolint:v2.15.1 < app/Dockerfile        # which rule fires?
git checkout -- app/Dockerfile
```

1. Which hadolint rule fails, and what does it say?
2. In `k8s/deployment.yaml`, which setting would still make the pod run as UID 10101, even with `USER root` in the image?

## Lab 4: Read the security exceptions and the manifests (free)

```bash
docker run --rm -v "$PWD:/src" -w /src aquasec/trivy:0.75.0 \
  config --severity HIGH,CRITICAL --skip-dirs terraform/.terraform terraform              # without the ignore file
docker run --rm -v "$PWD:/src" -w /src aquasec/trivy:0.75.0 \
  config --severity HIGH,CRITICAL --ignorefile .trivyignore.yaml --skip-dirs terraform/.terraform terraform
```

(Run `terraform -chdir=terraform init -backend=false` first so the modules are downloaded.)

1. Which three findings appear without the ignore file? For each, write down the production fix from `.trivyignore.yaml`.
2. Change one `expired_at` to yesterday's date and scan again. What happens? Why is that useful?
3. Render the manifests like CI does (see `.github/workflows/ci.yaml`, job `infrastructure`) and run `kubeconform -strict` on them.

## Lab 5: Prepare your fork and read your OIDC subject (free, needs GitHub)

1. Fork the repository. In `terraform/variables.tf`, set `github_repository` to your fork.
2. Read your subject prefix and set `github_oidc_subject_prefix`:
   ```bash
   gh api repos/<you>/<your-fork>/actions/oidc/customization/sub
   ```
   Does your prefix contain numeric IDs (`owner@id/name@id`)? What attack does that prevent?
3. Create the GitHub environment `production` that only allows the `main` branch (Settings → Environments → Deployment branches).
4. If your AWS account has **no** GitHub OIDC provider yet (there is at most one per account, `token.actions.githubusercontent.com`), set `create_github_oidc_provider = true` so Terraform creates it. Leave it `false` (the default) in an account that already has one: the provider is shared by every repository there, and this project then only reads it.

## Lab 6: Plan, review, apply (💶 costs money from here)

```bash
export AWS_REGION=eu-central-1
export TF_VAR_allowed_account_id=<your 12-digit account id>
aws ec2 describe-vpcs --query 'length(Vpcs)'      # write down your inventory first
terraform -chdir=terraform init
terraform -chdir=terraform plan -out=tfplan
terraform -chdir=terraform apply tfplan
```

1. What does the last line of the plan say? What would make you stop before applying?
2. Try a wrong account ID in `TF_VAR_allowed_account_id` and run `plan`. What happens?
3. After the apply: `aws eks update-kubeconfig --name eks-devsecops` and `kubectl get nodes -o wide`. Is there an external IP?

## Lab 7: Deploy through the pipeline and check least privilege (💶)

```bash
terraform -chdir=terraform output -raw github_deploy_role_arn | gh secret set AWS_DEPLOY_ROLE_ARN --env production
gh variable set DEPLOY_ENABLED --body true
gh workflow run deploy.yaml --ref main
```

1. Open the run. How long did each job take? Which URL does it show?
2. Find the "Least privilege check" step. Which `can-i` answers are `no`?
3. Make a small visible change in `app/src/profile.js`, push to `main`, and watch the footer version change on the live site.

## Lab 8: Attack your cluster (💶)

```bash
kubectl -n profile-card run attacker --image=busybox:1.37 --privileged --restart=Never -- sleep 60
P=$(kubectl -n profile-card get pods -o jsonpath='{.items[0].metadata.name}')
kubectl -n profile-card exec "$P" -- wget -T 5 -q -O /dev/null http://example.com
kubectl run imds --image=curlimages/curl:8.17.0 --restart=Never --rm -i --command -- \
  curl -sS -m 5 -X PUT http://169.254.169.254/latest/api/token -H "X-aws-ec2-metadata-token-ttl-seconds: 60"
IP=$(kubectl -n profile-card get pods -o jsonpath='{.items[0].status.podIP}')
kubectl -n default run lateral --image=curlimages/curl:8.17.0 --restart=Never --rm -i -- curl -m 5 "http://$IP:8080/"
```

1. Which mechanism stops each of the four attempts?
2. Temporarily change the NetworkPolicy's `ipBlock` to `10.42.0.0/16` (`kubectl -n profile-card edit networkpolicy allow-http-from-load-balancer`) and repeat the lateral test. What changes? Put it back (`kubectl apply -k` or re-run the pipeline).
3. While a deployment runs (Lab 7, step 3), run the `curl` loop from chapter 12 and count non-200 answers.

## Lab 9: Teardown and proof (do not skip)

```bash
gh variable set DEPLOY_ENABLED --body false
scripts/teardown.sh
scripts/verify-teardown.sh
gh secret delete AWS_DEPLOY_ROLE_ARN --env production
aws ec2 describe-vpcs --query 'length(Vpcs)'      # same as your inventory from lab 6?
```

1. What did the script delete first, and why?
2. Does the tagging API still list anything right after the destroy? What does the script report for it?
3. What state is the KMS key in, and when will AWS remove it?
4. Next day: open Cost Explorer and compare the real cost with the estimate (about $0.30 per hour).
