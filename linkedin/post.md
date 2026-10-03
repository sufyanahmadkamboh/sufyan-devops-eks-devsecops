I put a React app on AWS EKS, attacked it 5 ways, fixed what broke, and deleted everything. 62 minutes on AWS. 👇

Getting a container running on Kubernetes takes an afternoon. Running it SAFELY is the actual job:
👉 no AWS keys sitting in the CI system
👉 no known vulnerabilities shipped
👉 no servers exposed to the internet
👉 no forgotten test cluster billing every hour

So I built the whole thing the way a security-minded team would, and recorded every step 🎬

🏗️ Terraform builds it: a private network, an EKS cluster, an image registry, permissions. 72 AWS resources in 12.5 minutes.
🔍 Every push is checked: leaked secrets, vulnerable packages, the Dockerfile, the image, the Terraform, the Kubernetes files.
🪪 The pipeline has NO stored AWS password. It gets a "day pass" (GitHub OIDC) that works for one job, one repository, one namespace.
🚀 git push → live on the internet in 3 minutes 37 seconds, through an AWS load balancer.

Then I attacked my own cluster:
⛔ privileged container → refused
⛔ app pod calling out to the internet → blocked
⛔ stealing the server's AWS credentials from a pod → blocked
⚠️ reaching the app from another namespace → WORKED (HTTP 200). Fixed, now blocked.
⚠️ requests during a deployment → 3 of 280 failed. Fixed: 401 of 401 OK.

The security scanner even blocked my very first image: a HIGH vulnerability in the official base image, with a fix already available.

🧹 And then: terraform destroy, 72 resources gone, plus a script that proves nothing is left. Estimated cost of the whole lab: about $0.35.

🎓 I made a 23-minute video for my students that explains every tool and its configuration, using the real terminal output, plus a free study guide with hands-on labs.

💻 Code + video: https://github.com/sufyanahmadkamboh/sufyan-devops-eks-devsecops
🌐 Slides + all my projects: https://sufyanahmadkamboh.github.io/#story=eks-devsecops&slide=1

Honest question: is a test cluster of yours still running right now? 👇

#AWS #Kubernetes #EKS #DevSecOps #Terraform #GitHubActions #DevOps #CloudSecurity #PlatformEngineering #LearningDevOps
