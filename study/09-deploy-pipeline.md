# 9. The deploy pipeline

## What is it?

**CD** (continuous deployment): every change that reaches `main` and passes all checks is deployed automatically. Here that is [`.github/workflows/deploy.yaml`](../.github/workflows/deploy.yaml). It runs on every push to `main` that touches `app/`, `k8s/` or the workflow, and can be started by hand.

## Why it is built this way

Two jobs, because the riskiest moment is when tools and credentials meet:

| Job | Has AWS credentials? | Does |
|---|---|---|
| **1. Build and scan** | **no** | build the image (with version and commit), Trivy gate, SBOM, save the image as an artifact |
| **2. Deploy to EKS** | yes, temporary (OIDC), in the `production` environment | push, ECR scan, sign, deploy, check permissions, smoke test |

- The scanners never run next to AWS credentials.
- A vulnerable image never even reaches the registry.
- Job 2 deploys exactly the image job 1 scanned (it is passed as an artifact, `image.tar.gz`).

## How it works: job 2 step by step

1. **OIDC → AWS** (chapter 8). The account ID is masked in the public logs (`mask-aws-account-id: true` and `::add-mask::`).
2. **Push to ECR by digest.** The image gets an immutable tag like `1.0.10-cddef1d`; the step outputs the **digest** (`sha256:…`) that the registry computed. Everything after this uses the digest.
3. **ECR scan on push (second opinion).** ECR scans the image; the job stops on any CRITICAL finding.
4. **cosign keyless signature.** `cosign sign` signs the digest with a short-lived certificate for this workflow (Sigstore), then `cosign verify` checks it with the expected identity `…/.github/workflows/deploy.yaml@refs/heads/main`. The signature is stored next to the image in ECR (the untagged entries in the image list).
5. **Deploy the exact digest.** `k8s/kustomization.yaml` contains placeholders; the job replaces them and applies:
   ```yaml
   images:
     - name: profile-card
       newName: IMAGE_REPOSITORY      # → <registry>/eks-devsecops/profile-card
       digest: IMAGE_DIGEST           # → sha256:…
   ```
   ```bash
   sed -i -e "s|IMAGE_REPOSITORY|${REPO}|" -e "s|IMAGE_DIGEST|${DIGEST}|" k8s/kustomization.yaml
   kubectl apply -k k8s
   kubectl -n profile-card rollout status deployment/profile-card --timeout=300s
   ```
   Pods run `…/profile-card@sha256:…`, never a tag.
6. **Least privilege check** with `kubectl auth can-i` (chapter 8).
7. **Smoke test through the load balancer.** The job reads the Ingress hostname and waits until `/healthz` answers and the page contains "Profile". GitHub shows the URL on the run page.

Recorded run triggered by a push: **3 minutes 37 seconds** from push to live (build and scan 33 s, deploy 2 min 54 s).

### Real bugs found in the pipeline

Pipelines are code, and they need testing too. Two real problems appeared in step 3:

1. **`aws ecr wait image-scan-complete` failed with `ScanNotFoundException`.** Right after a push, ECR has not registered the scan yet, and the CLI waiter gives up instead of waiting. Fix: a loop that polls `describe-image-scan-findings` until the status is `COMPLETE` (or `FAILED` / `UNSUPPORTED_IMAGE`).
2. **A clean image failed the check.** With zero findings, ECR returns no `findingSeverityCounts` at all, so the CLI printed nothing and the `jq` check treated "nothing" as an error. Fix: treat an empty answer as `{}`, and read `(. // {}).CRITICAL // 0`.

```bash
counts="$(aws ecr describe-image-scan-findings … --query 'imageScanFindings.findingSeverityCounts' --output json)"
counts="${counts:-null}"
[[ "$(jq -r '(. // {}).CRITICAL // 0' <<<"${counts}")" == 0 ]]
```

### Switching deployments on and off

Job 2 only runs when the repository variable `DEPLOY_ENABLED` is `true`. It is switched on while the lab cluster exists and off before the teardown, so a push can never try to deploy to a deleted cluster.

## Common mistakes

- Scanning after pushing, or deploying a tag that was scanned yesterday.
- `kubectl set image …:latest`: you no longer know what runs.
- No rollout wait: the pipeline is green while the new pods crash.
- No smoke test through the real entry point (the load balancer).
- Trusting AWS CLI waiters blindly: read what they do on errors.

## Check yourself

1. Why is the image passed from job 1 to job 2 as an artifact instead of being rebuilt?
2. What does the cluster run: a tag or a digest? Where does the digest come from?
3. What was wrong with the first version of the ECR scan check?

### Answers

<details><summary>Answers</summary>

1. So that job 2 deploys exactly the bytes job 1 scanned; a rebuild could produce a different image (new base image packages, new dependencies).
2. A digest. The registry computes it during the push; the job reads it with `docker inspect` (`RepoDigests`) and writes it into the kustomization.
3. Two things: the waiter failed when the scan was not registered yet (`ScanNotFoundException`), and a clean image (no findings, so no counts) was treated as a failure.

</details>

Next: [10. Load Balancer Controller and Ingress](10-load-balancer-and-ingress.md)
