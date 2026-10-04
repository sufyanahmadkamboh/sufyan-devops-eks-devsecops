EKS DevSecOps workshop, part 1 of 2: build a production-style Amazon EKS platform with Terraform, live on a real AWS account. The problem, the architecture, the repository, the React app, then the VPC, the EKS cluster and the AWS Load Balancer Controller, verified in the terminal and in the AWS Console. We finish with the image build, the Trivy scan, the SBOM and signing.

▶️ Part 2 (OIDC, the real pipeline, a failing security check, troubleshooting, teardown): {{PART2_LINK}}
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

📊 What happened (all recorded)
• terraform plan: 72 to add, 0 to change, 0 to destroy
• terraform apply: 72 resources in 12 min 5 s (the EKS control plane alone: 8 min 21 s)
• Windows gotcha: terraform init failed with "Filename too long", fixed with a shorter folder
• Trivy image scan: 0 fixable CRITICAL/HIGH findings · SBOM: 70 packages (CycloneDX)
• EKS: API access entries, KMS-encrypted secrets, audit logs, IMDSv2 with hop limit 1, private nodes

#AWS #Kubernetes #DevSecOps
