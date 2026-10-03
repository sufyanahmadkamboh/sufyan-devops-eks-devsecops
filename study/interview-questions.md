# Interview questions

25 questions this project prepares you for. Try to answer before opening the answer.

1. **Why put EKS worker nodes in private subnets, and how do they still pull images?**
   <details><summary>Answer</summary>Nodes without public IPs cannot be reached from the internet, which removes a whole attack surface. Outbound traffic (ECR, EKS API, OS updates) goes through a NAT gateway in a public subnet; only the load balancer is public.</details>

2. **One NAT gateway or one per availability zone?**
   <details><summary>Answer</summary>One is cheaper (this lab), but it is a single point of failure: if its zone fails, the other zone loses outbound access. Production uses one per AZ, each private subnet routing to the NAT in its own zone.</details>

3. **What guard rails make Terraform safe in a shared AWS account?**
   <details><summary>Answer</summary>`allowed_account_ids` (refuses any other account), a validated region variable, default tags on every resource, reviewing the plan ("0 to change, 0 to destroy"), reading shared resources with data sources instead of managing them, and unique name prefixes.</details>

4. **Why must Terraform state never be committed, and where should a team keep it?**
   <details><summary>Answer</summary>It contains resource IDs, the account number and sometimes secrets, and two copies diverge. Teams use a remote backend such as S3 with locking so only one apply runs at a time.</details>

5. **What are EKS access entries and why are they better than the aws-auth ConfigMap?**
   <details><summary>Answer</summary>They map IAM principals to Kubernetes permissions through the EKS API, as code, with AWS-managed access policies that can be scoped to namespaces. The ConfigMap was edited by hand inside the cluster and a mistake could lock everyone out.</details>

6. **How does IMDSv2 with a hop limit of 1 protect a cluster?**
   <details><summary>Answer</summary>The instance metadata service hands out the node's AWS credentials. IMDSv2 requires a session token from a PUT request; with a hop limit of 1 the token response cannot reach a pod (one extra hop), so a compromised pod cannot steal the node's credentials. In this project the token request from a pod timed out and IMDSv1 returned 401.</details>

7. **Why encrypt Kubernetes secrets with a KMS key when EBS volumes are already encrypted?**
   <details><summary>Answer</summary>Envelope encryption protects secrets in etcd and backups at the application level with a key you control and can audit or revoke, independent of disk encryption.</details>

8. **What is Pod Identity and why use it instead of IRSA?**
   <details><summary>Answer</summary>Pod Identity links a service account to an IAM role through an EKS association and an agent add-on. Unlike IRSA it needs no IAM OIDC provider per cluster and no role annotation, so fewer global IAM objects are created.</details>

9. **How does GitHub Actions get into AWS without stored keys?**
   <details><summary>Answer</summary>The job requests an OIDC token from GitHub, `configure-aws-credentials` exchanges it with STS (`AssumeRoleWithWebIdentity`) for temporary credentials of a role whose trust policy checks the audience (`sts.amazonaws.com`) and the subject (this repository's `production` environment).</details>

10. **The OIDC role assumption fails with "Not authorized to perform sts:AssumeRoleWithWebIdentity". How do you debug it?**
    <details><summary>Answer</summary>Compare the token's claims with the trust policy: audience, and especially the subject. New GitHub repositories use an immutable subject with numeric IDs (`repo:owner@id/name@id:environment:production`); read it with `gh api repos/OWNER/REPO/actions/oidc/customization/sub`. Also check that the job runs in the expected environment and that the identity provider exists.</details>

11. **Why scope the trust policy to a GitHub environment instead of a branch?**
    <details><summary>Answer</summary>An environment can have protection rules (only `main`, optional reviewers) and secrets of its own. Only jobs that pass those rules get the `environment:production` subject.</details>

12. **How do you prove a pipeline has least privilege in Kubernetes?**
    <details><summary>Answer</summary>Scope its access entry to one namespace and test it on every run with `kubectl auth can-i`: yes for its own namespace, no for kube-system, secrets, cluster role bindings and namespace deletion. The job fails if an answer changes.</details>

13. **Why split the deploy workflow into a build-and-scan job and a deploy job?**
    <details><summary>Answer</summary>Scanning tools never run next to cloud credentials, a vulnerable image never reaches the registry, and the deploy job ships exactly the scanned image (passed as an artifact).</details>

14. **Why deploy by digest instead of tag?**
    <details><summary>Answer</summary>A tag can be moved to different content; a digest is the content hash. The pipeline writes the digest into the kustomization, so pods run exactly what was scanned and signed. ECR tags are also immutable.</details>

15. **What does `--ignore-unfixed` do in a Trivy gate and why use it?**
    <details><summary>Answer</summary>It reports only vulnerabilities with a fixed version available, so the gate blocks on problems the team can act on. A gate that blocks on unfixable issues gets disabled.</details>

16. **The scanner blocks the official base image you pinned yesterday. What do you do?**
    <details><summary>Answer</summary>Read the finding: here pcre2 CVE-2026-103111 (HIGH, fixed in 10.49). If the distribution has the fix, apply it in the image (`apk upgrade` as root, then back to the unprivileged user) or move to a newer base digest; rescan to confirm 0 findings. Never just ignore it.</details>

17. **How do you handle a scanner finding you decide to accept?**
    <details><summary>Answer</summary>Write it down where the scanner reads it (`.trivyignore.yaml`) with the reason, the production fix and an expiry date, so it is reviewed again. Here: the public EKS endpoint for GitHub-hosted runners and node egress.</details>

18. **Why pin GitHub Actions to commit SHAs?**
    <details><summary>Answer</summary>Version tags can be moved to malicious commits (it happened to tj-actions/changed-files in 2025). A full commit SHA always means the same code. A script in CI rejects unpinned actions.</details>

19. **How does an Ingress become an AWS load balancer?**
    <details><summary>Answer</summary>The AWS Load Balancer Controller watches Ingresses with `ingressClassName: alb`, finds subnets by their tags, and creates an ALB, listeners, target groups and security groups. With target type ip, targets are the pod IPs.</details>

20. **Why does `terraform destroy` fail on the VPC if you forget the Ingress?**
    <details><summary>Answer</summary>The ALB and its security groups were created by the controller, not Terraform. If the controller is destroyed first, they remain and still use the VPC's subnets. Delete the Ingress first and wait for the ALB to disappear.</details>

21. **On EKS, a NetworkPolicy allows the VPC CIDR so the ALB can reach the pods. What is wrong?**
    <details><summary>Answer</summary>With the VPC CNI, pod IPs come from the VPC, so the rule also lets every pod in the cluster reach the app (lateral movement; measured: HTTP 200 from another namespace). Allow only the subnets where the ALB's interfaces live (here 10.42.48.0/23).</details>

22. **Which securityContext settings make a container hard to abuse?**
    <details><summary>Answer</summary>`runAsNonRoot` with a high UID, `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true` (with a small writable `/tmp`), `capabilities: drop [ALL]`, `seccompProfile: RuntimeDefault`, no service account token, and resource limits; enforced by Pod Security `restricted` on the namespace.</details>

23. **Why can a rolling update behind an ALB still drop requests, and how do you fix it?**
    <details><summary>Answer</summary>Pods stop before the ALB stops sending them traffic, and new pods can get traffic before the ALB has health-checked them. Fix: pod readiness gates (pods are ready only when the ALB target is healthy), a preStop sleep longer than the deregistration delay (15 s vs 10 s), and enough termination grace. Measured: 3 of 280 failed before, 401 of 401 after.</details>

24. **What is version skew in a single-page app rollout?**
    <details><summary>Answer</summary>Old and new pods serve at the same time (about 28 s here), so a browser can load an old `index.html` and then ask a new pod for an old hashed asset that no longer exists. Keep old assets available (S3/CDN) or keep users on one version.</details>

25. **How do you prove a lab is fully deleted in a shared account?**
    <details><summary>Answer</summary>Delete in the right order, then verify read-only: every resource type by name and by project tag in the region, IAM roles and policies (including module-generated names, confirmed by tag), the real state of everything the tagging API still lists (it lags; a KMS key in its 7-day deletion window counts as deleted), and that shared resources such as the GitHub OIDC provider still exist. Finally compare with the inventory taken before the project.</details>
