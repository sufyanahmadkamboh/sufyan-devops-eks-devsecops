EKS DevSecOps workshop, part 2 of 2: GitHub OIDC with no stored AWS keys, every stage of the DevSecOps pipeline, a real push going live on Amazon EKS behind an ALB, a vulnerable dependency stopped by the pipeline, a broken rollout troubleshot layer by layer, and a verified teardown that leaves the account exactly as we found it.

◀️ Part 1 (architecture, Terraform, VPC, EKS, console tour, build and scan): {{PART1_LINK}}
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
• git push to live: 4 min 36 s (security checks in parallel, about 30 s)
• lodash 4.17.20 pushed on purpose: npm audit failed the run, build and deploy skipped, production untouched
• fix (lodash 4.18.1): green again in 3 min 23 s
• a readiness probe typo did NOT fail: single-page apps answer 200 on every path
• a probe on the wrong port: rollout stuck, users unaffected thanks to readiness gates, fixed with git revert
• teardown: 72 resources destroyed, verified by name, tag and real state; shared OIDC provider untouched

💬 What would you add first to make this production ready? Tell me in the comments.

#AWS #Kubernetes #DevSecOps
