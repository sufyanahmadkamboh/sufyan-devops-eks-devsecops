Deploy a React app to Amazon EKS with Terraform and a DevSecOps GitHub Actions pipeline: private VPC, hardened EKS cluster, AWS Load Balancer Controller with an ALB Ingress, Trivy scanning, cosign signing, and OIDC (no AWS keys in GitHub). Then I attack my own cluster, fix the two weaknesses it finds, and delete everything with a verified teardown. Built and recorded on a real AWS account in 62 minutes.

💻 Code: https://github.com/sufyanahmadkamboh/sufyan-devops-eks-devsecops
🌐 All my projects: https://sufyanahmadkamboh.github.io/

🧪 Build it yourself (your own AWS account, roughly $0.30 per hour while it runs, delete it the same day):
1. Fork the repository, set github_repository and github_oidc_subject_prefix in terraform/variables.tf
2. export TF_VAR_allowed_account_id=<your account id>; terraform -chdir=terraform apply
3. GitHub: secret AWS_DEPLOY_ROLE_ARN (environment production), variable DEPLOY_ENABLED=true
4. Push to main and watch it deploy
5. scripts/teardown.sh

⏱️ Chapters
{{CHAPTERS}}

🧰 Tools used, and what each one does here
• Terraform: VPC, EKS, ECR, IAM as code, with account and region guard rails
• Amazon VPC: private subnets for nodes, public subnets for the load balancer only, NAT gateway, flow logs
• Amazon EKS 1.37: KMS-encrypted secrets, audit logs, access entries, IMDSv2 with hop limit 1, network policies
• React + Vite + nginx-unprivileged: a small, non-root, read-only image with strict security headers
• Trivy: image gate, Terraform and Kubernetes misconfiguration scans (accepted risks written down and dated)
• GitHub Actions: gitleaks, npm audit, hadolint, kubeconform, pinned actions, actionlint, zizmor
• GitHub OIDC → AWS IAM: short-lived credentials, one repository, one environment, one namespace
• Amazon ECR: immutable tags, scan on push
• cosign: keyless image signatures
• AWS Load Balancer Controller + EKS Pod Identity: Ingress → internet-facing ALB, no keys in the cluster

📊 What happened (all measured)
• terraform apply: 72 resources in 12 min 30 s · destroy: 72 resources, verified clean
• push to live: 3 min 37 s
• Trivy blocked the first image: a HIGH vulnerability in pcre2, fixed by applying Alpine updates
• privileged pod, egress, stealing node credentials via IMDS: all refused
• lateral movement between namespaces: worked, then fixed with a tighter NetworkPolicy
• requests during a deploy: 3 of 280 failed → 401 of 401 after readiness gates + preStop

💬 Which attack would you try next? Tell me in the comments.

#AWS #Kubernetes #DevSecOps
