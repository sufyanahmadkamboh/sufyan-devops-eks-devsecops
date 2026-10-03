# Troubleshooting

Every problem below happened while building this project.

**Trivy gate fails on the base image (e.g. pcre2 CVE-2026-103111, HIGH, "fixed")**
The pinned base image predates an Alpine security fix. The runtime stage runs `apk upgrade --no-cache` (as UID 0,
then back to the unprivileged user). `--ignore-unfixed` keeps the gate on problems you can actually fix.

**`configure-aws-credentials`: Not authorized to perform sts:AssumeRoleWithWebIdentity**
New GitHub repositories use an immutable OIDC subject: `repo:<owner>@<owner-id>/<repo>@<repo-id>:environment:production`.
Read it with `gh api repos/OWNER/REPO/actions/oidc/customization/sub` and set `github_oidc_subject_prefix`. Also check
that the job runs in the `production` environment.

**`aws ecr wait image-scan-complete`: ScanNotFoundException**
Right after a push the scan is not registered yet, and the waiter gives up. The pipeline polls
`describe-image-scan-findings` until the status is COMPLETE.

**ECR scan step fails on a clean image**
With zero findings ECR returns no `findingSeverityCounts`, so the CLI prints nothing. Treat empty as zero.

**Trivy KSV-0125: image from an untrusted registry (in CI)**
The CI render used `registry.example`. Use a registry Trivy trusts (an ECR hostname, as in the real deployment).

**Trivy finds problems in `.terraform/modules`**
Those are the modules' own examples. Scan with `--skip-dirs terraform/.terraform`.

**A pod in another namespace can reach the app**
On EKS (VPC CNI), pod IPs are VPC IPs, so a NetworkPolicy rule "allow the VPC CIDR" allows every pod. Allow only the
public subnets where the ALB's network interfaces live. Kubelet health probes keep working.

**Requests fail (502/timeouts) during rollouts**
Pods stop before the ALB deregisters them. Use pod readiness gates (namespace label
`elbv2.k8s.aws/pod-readiness-gate-inject=enabled`), a `preStop` sleep, and a shorter ALB deregistration delay.

**`kubectl`: Unable to connect to localhost:8080 (Windows, Git Bash)**
With `MSYS_NO_PATHCONV=1`, a `/c/...` KUBECONFIG path is not converted for `kubectl.exe`. Use `C:/...`.

**kubectl version skew**
kubectl supports one minor version around the server. Use kubectl 1.36–1.38 for EKS 1.37.

**Teardown verification lists deleted resources**
The Resource Groups Tagging API keeps deleted resources for a while. `verify-teardown.sh` checks each ARN's real state;
a KMS key in its mandatory 7-day deletion window counts as deleted.

**`terraform destroy` fails on the VPC (dependency violation)**
The ALB and its security groups were created by the controller, not Terraform. Delete the Ingress first
(`scripts/teardown.sh` does this and waits for the ALB to disappear).
