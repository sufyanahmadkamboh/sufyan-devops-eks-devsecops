"""The video: scenes, visuals and narration for the EKS DevSecOps project.

Every number and every terminal line comes from the real build on 2026-10-03/04 (recorded command output,
redacted by redact.py before it reaches a frame). `hl` highlights code lines; `tts` overrides the spoken text.
"""

from __future__ import annotations

from components import arrow, box, card, checklist, code, grid, label, notes, svg, terminal, tile


def S(say: str, hl: tuple[int, int] | None = None, tts: str | None = None) -> dict:
    return {"say": say, "hl": hl, "tts": tts}


def shot(s: int, src: str, alt: str, style: str = "") -> str:
    return f'<img class="shot st" data-s="{s}" src="../assets/{src}" alt="{alt}" style="{style}">'


REPO = "github.com/sufyanahmadkamboh/sufyan-devops-eks-devsecops"
SCENES: list[dict] = []


def scene(chapter, kicker, title, body, steps, layout="full"):
    SCENES.append({"chapter": chapter, "kicker": kicker, "title": title, "body": body, "steps": steps, "layout": layout})


# ---------------------------------------------------------------- Hook
scene("The challenge", "AWS · Kubernetes · DevSecOps", "From zero to the internet, securely, then delete it all", svg(
    box(0, 0, 30, 400, 230, "💻", "A React app", ["your laptop", "\"works on my machine\""], "blue")
    + arrow(1, 405, 145, 505, 145)
    + box(1, 510, 30, 520, 230, "🏗️", "Terraform → AWS EKS", ["VPC, private nodes, load balancer", "72 resources in 12.5 minutes"], "amber", "#2b2410")
    + arrow(2, 1035, 145, 1135, 145)
    + box(2, 1140, 30, 580, 230, "🌍", "Live on the internet", ["every git push: build, scan,", "sign, deploy, smoke test"], "ok", "#0f2a22")
    + box(3, 0, 330, 840, 190, "🕵️", "Then I attack it", ["privileged pods, stolen node credentials,", "lateral movement, downtime during deploys"], "bad", "#2a1520")
    + box(4, 880, 330, 840, 190, "🧹", "And delete everything", ["72 resources destroyed, verified clean", "62 minutes on AWS in total"], "violet")
    + label(4, 860, 640, "real AWS account · real pipeline · real bugs found and fixed", 34, "ok", "middle", 900)
), [
    S("In this video, we take a React app from a laptop to the internet, on Amazon EKS, the way a security-minded DevOps team would do it at work."),
    S("Terraform builds the whole platform on AWS: a private network, a Kubernetes cluster and a load balancer. Seventy two resources, in twelve and a half minutes."),
    S("Then every git push builds the app, scans it for vulnerabilities, signs it and deploys it, with no AWS password stored anywhere."),
    S("Then I attack my own cluster. Privileged containers, stealing the node's cloud credentials, moving sideways between apps, and dropping requests during a deployment. "
      "Two of those attacks found real weaknesses, and I fix them on camera."),
    S("And at the end, I delete everything and prove that nothing is left. The whole thing ran on AWS for sixty two minutes. Let us build it."),
])

# ---------------------------------------------------------------- Map
scene(None, "What you will learn", "The plan for the next 25 minutes", grid([
    card(0, "🗺️", "Architecture", "how all the parts connect"),
    card(1, "🏗️", "Terraform", "VPC, EKS, ECR, IAM as code"),
    card(1, "🌐", "VPC", "public and private subnets, NAT"),
    card(1, "☸️", "Amazon EKS", "a hardened cluster"),
    card(2, "⚛️", "React + Docker", "a small, non-root image"),
    card(2, "🔍", "Trivy", "scan code, config and images"),
    card(2, "⚙️", "GitHub Actions", "CI checks and CD"),
    card(2, "🔐", "OIDC", "AWS access without keys"),
    card(3, "⚖️", "Load Balancer Controller", "Ingress → ALB"),
    card(3, "🛡️", "Kubernetes security", "pod security, network policy"),
    card(3, "🕵️", "Attacks + fixes", "what broke and why", "bad"),
    card(4, "🧹", "Teardown", "delete and verify", "ok"),
], cols=4, gap=16), [
    S("Here is the plan. First the architecture, so you see the big picture."),
    S("Then the infrastructure with Terraform: the VPC network, the EKS cluster, the container registry, and the permissions."),
    S("Then the application: React, a secure Docker image, Trivy scanning, the GitHub Actions pipeline, and how it gets into AWS without any stored keys."),
    S("Then exposing it to the internet with the AWS Load Balancer Controller, the Kubernetes security settings, and my attacks with the fixes."),
    S("And finally, how to delete everything safely and prove it. All the code is linked in the description, so you can follow along."),
])

# ---------------------------------------------------------------- Why
scene("Why this matters", "The problem", "Running containers is easy. Running them safely is the job.", grid([
    card(0, "🔑", "Leaked cloud keys", "long-lived AWS keys in CI settings are a top cause of cloud breaches", "bad"),
    card(1, "🐛", "Known vulnerabilities", "base images ship with CVEs that already have a fix", "bad"),
    card(2, "🌐", "Exposed nodes", "worker nodes with public IPs, open security groups", "bad"),
    card(3, "👑", "Over-privileged pods", "containers running as root, able to reach node credentials", "bad"),
    card(4, "💸", "Forgotten resources", "a test cluster left running costs money every hour", "amber"),
    card(5, "✅", "This project", "fixes each one, and proves it with a test you can rerun", "ok"),
], cols=3), [
    S("Why does this matter? Getting a container running on Kubernetes takes an afternoon. Getting it running safely is the actual job. Here is what usually goes wrong. "
      "First: long lived AWS keys stored in the CI system, one of the most common causes of cloud breaches.",
      tts="Why does this matter? Getting a container running on Kubernetes takes an afternoon. Getting it running safely is the actual job. Here is what usually goes wrong. "
          "First: long lived A W S keys stored in the C I system, one of the most common causes of cloud breaches."),
    S("Second: known vulnerabilities. Base images often ship with security bugs that already have a fix, and nobody notices."),
    S("Third: worker nodes with public IP addresses, sitting directly on the internet."),
    S("Fourth: containers running as root, or able to steal the node's cloud credentials."),
    S("And fifth: the test cluster that someone forgot to delete, quietly costing money every hour."),
    S("This project fixes every one of these, and for each fix there is a test or a command you can rerun yourself."),
])

# ---------------------------------------------------------------- Architecture
scene("Architecture", "Architecture", "The whole platform on one page", svg(
    box(0, 0, 0, 360, 170, "🧑‍💻", "git push to main", ["GitHub repository"], "blue")
    + arrow(1, 365, 85, 425, 85)
    + box(1, 430, 0, 520, 170, "⚙️", "GitHub Actions", ["CI: secrets, tests, scans", "CD: build → scan → sign → deploy"], "blue", "#16306a")
    + arrow(2, 955, 85, 1015, 85, label="OIDC")
    + box(2, 1020, 0, 700, 170, "🔐", "AWS IAM role (short-lived)", ["push to one ECR repository", "deploy into one Kubernetes namespace"], "violet")
    + box(3, 0, 230, 1720, 500, "☁️", "AWS eu-central-1 · VPC 10.42.0.0/16 · 2 availability zones", [], "amber", "#111c2e")
    + box(3, 40, 320, 520, 180, "🌍", "Public subnets", ["Application Load Balancer", "NAT gateway"], "ok", "#0f2a22")
    + box(4, 620, 320, 1060, 370, "🔒", "Private subnets: EKS worker nodes (no public IPs)", ["profile-card pods × 2 (one per zone)", "AWS Load Balancer Controller", "CoreDNS, VPC CNI (network policies), Pod Identity agent"], "blue", "#16306a")
    + arrow(4, 565, 410, 615, 410, "ok")
    + box(5, 40, 540, 520, 150, "📦", "Amazon ECR", ["immutable tags, scan on push"], "blue")
    + label(5, 1150, 655, "EKS control plane: KMS-encrypted secrets · audit logs · access entries", 22, "#ffe9b0", "middle")
), [
    S("Here is the whole platform on one page. It starts with a git push to the main branch."),
    S("GitHub Actions runs the checks, and on main it builds, scans, signs and deploys the app."),
    S("To reach AWS, the pipeline uses OIDC to get a short lived role. That role can push to exactly one container repository, and deploy into exactly one Kubernetes namespace. Nothing else."),
    S("Everything lives in one AWS region, Frankfurt, in a dedicated VPC that spans two availability zones. The public subnets hold only the load balancer and the NAT gateway."),
    S("The EKS worker nodes live in private subnets, with no public IP addresses. They run our two app pods, one in each zone, plus the load balancer controller and the cluster add-ons."),
    S("Images are stored in Amazon ECR, and the EKS control plane encrypts secrets with a dedicated KMS key and writes audit logs."),
])

# ---------------------------------------------------------------- Terraform
TF_MAIN = """locals {
  name = "eks-devsecops"
  tags = {                       # every resource carries these tags
    Project   = "eks-devsecops"
    Owner     = "sufyan"
    ManagedBy = "terraform"
  }
}

provider "aws" {
  region              = var.region               # validated: eu-central-1 only
  allowed_account_ids = [var.allowed_account_id] # wrong account? refuse to run

  default_tags {
    tags = local.tags
  }
}"""
scene("Tool 1: Terraform", "Tool 1 · Terraform", "Infrastructure as code, with guard rails",
      code("terraform/main.tf (excerpt)", TF_MAIN, "terraform", 22) + notes([
          (0, "Why Terraform", "reviewable, repeatable, destroyable"),
          (1, "Tags everywhere", "teardown is verified by tag"),
          (2, "Two guard rails", "one region, one account"),
          (3, "Pinned versions", "AWS provider 6.67, VPC module 6.7.3, EKS module 21.26.0"),
      ]), [
    S("Tool number one is Terraform. Instead of clicking through the AWS console, we describe the infrastructure as code. "
      "That makes it reviewable in a pull request, repeatable for every student, and, just as important, destroyable with one command."),
    S("Every resource gets the same tags: project, owner, and managed by Terraform. At the end, we use these tags to prove that nothing was left behind.", hl=(3, 7)),
    S("Then two guard rails, because I built this in a company account. The region variable only accepts Frankfurt, and allowed account IDs makes Terraform refuse to run against any other AWS account.", hl=(11, 12)),
    S("All versions are pinned: the AWS provider, and the community VPC and EKS modules. The modules are well tested and widely used, so we write less code and make fewer mistakes."),
], layout="code")

# ---------------------------------------------------------------- VPC
VPC = """module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.7.3"
  cidr    = "10.42.0.0/16"
  azs     = slice(data.aws_availability_zones.available.names, 0, 2)

  private_subnets = ["10.42.0.0/20", "10.42.16.0/20"]   # nodes and pods
  public_subnets  = ["10.42.48.0/24", "10.42.49.0/24"]  # load balancer only

  enable_nat_gateway = true
  single_nat_gateway = true   # lab: one; production: one per zone

  public_subnet_tags  = { "kubernetes.io/role/elb" = 1 }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = 1 }

  manage_default_security_group = true   # default SG allows nothing
  enable_flow_log               = true   # who talked to whom
}"""
scene("Tool 2: the VPC", "Tool 2 · VPC network", "Private nodes, public load balancer",
      code("terraform/vpc.tf (excerpt)", VPC, "terraform", 21) + notes([
          (0, "Two zones", "survives a data-center failure"),
          (1, "Private vs public", "nodes never get public IPs"),
          (2, "NAT gateway", "outbound only: images, updates"),
          (3, "Subnet tags", "the controller finds its subnets"),
          (4, "Locked down + logged", "default SG empty, flow logs on"),
      ]), [
    S("Tool two is the network: a VPC with the address range 10.42 dot 0 dot 0 slash 16, spread over two availability zones, so the app survives the loss of a whole data center.",
      tts="Tool two is the network: a V P C with the address range ten dot forty two dot zero dot zero slash sixteen, spread over two availability zones, so the app survives the loss of a whole data center.", hl=(1, 5)),
    S("Private subnets hold the worker nodes and the pods. Public subnets hold only the load balancer. Nodes never get a public IP address.", hl=(7, 8)),
    S("A NAT gateway lets the private nodes reach out, for example to pull images, while nothing on the internet can reach in. One NAT keeps the lab cheap. In production you would use one per zone.", hl=(10, 11)),
    S("These two subnet tags let the AWS Load Balancer Controller discover where to place internet-facing and internal load balancers.", hl=(13, 14)),
    S("And two security habits: the default security group allows nothing, and VPC flow logs record every connection, which you will want during an investigation.", hl=(16, 17)),
], layout="code")

# ---------------------------------------------------------------- EKS
EKS = """module "eks" {
  source             = "terraform-aws-modules/eks/aws"
  version            = "21.26.0"
  kubernetes_version = "1.37"
  subnet_ids         = module.vpc.private_subnets

  enabled_log_types = ["api", "audit", "authenticator"]
  encryption_config = { resources = ["secrets"] }      # KMS
  authentication_mode = "API"                          # access entries

  addons = {
    vpc-cni = { configuration_values = jsonencode({ enableNetworkPolicy = "true" }) }
    eks-pod-identity-agent = {}
  }
  eks_managed_node_groups = { default = {
    instance_types   = ["t3.medium"]
    min_size = 2, max_size = 3, desired_size = 2
    metadata_options = { http_tokens = "required", http_put_response_hop_limit = 1 }
    block_device_mappings = { xvda = { ebs = { encrypted = true } } }
  } }
}"""
scene("Tool 3: Amazon EKS", "Tool 3 · Amazon EKS", "A hardened Kubernetes cluster",
      code("terraform/eks.tf (simplified)", EKS, "terraform", 19) + notes([
          (0, "Kubernetes 1.37", "latest in standard support"),
          (1, "Audit logs + KMS", "who did what; secrets encrypted"),
          (2, "Access entries", "IAM → Kubernetes, no aws-auth"),
          (3, "Network policy on", "via the VPC CNI add-on"),
          (4, "IMDSv2, hop limit 1", "pods can't steal node credentials"),
      ]), [
    S("Tool three is Amazon EKS, managed Kubernetes. We use version 1.37, the newest one in standard support, and place the cluster in the private subnets.",
      tts="Tool three is Amazon E K S, managed Kubernetes. We use version 1 point 37, the newest one in standard support, and place the cluster in the private subnets.", hl=(1, 5)),
    S("The control plane writes audit logs, so every API call is recorded, and Kubernetes secrets are encrypted with a dedicated KMS key.", hl=(7, 8)),
    S("Authentication mode API means we use EKS access entries to map AWS identities to Kubernetes permissions. No more editing the old aws-auth config map by hand.", hl=(9, 9),
      tts="Authentication mode A P I means we use E K S access entries to map AWS identities to Kubernetes permissions. No more editing the old A W S auth config map by hand."),
    S("The VPC CNI add-on gets network policy enforcement switched on, and the Pod Identity agent lets pods get AWS permissions without any keys.", hl=(11, 14)),
    S("Two t3 medium nodes, encrypted disks, and an important one: instance metadata version two only, with a hop limit of one. Remember this. Later, I try to steal the node's credentials from a pod, and this setting is why it fails.", hl=(15, 20),
      tts="Two t3 medium nodes, encrypted disks, and an important one: instance metadata version two only, with a hop limit of one. Remember this. Later, I try to steal the node's credentials from a pod, and this setting is why it fails."),
], layout="code")

# ---------------------------------------------------------------- Plan & apply
scene("Building it on AWS", "Recorded: terraform plan + apply", "73 to add, 0 to change, 0 to destroy", terminal([
    (0, "$ terraform plan -out=tfplan", "cmd"),
    (0, "  # module.vpc.aws_vpc.this[0] will be created", "out"),
    (0, "  # module.eks.aws_eks_cluster.this[0] will be created", "out"),
    (0, "  # helm_release.lb_controller will be created", "out"),
    (0, "Plan: 73 to add, 0 to change, 0 to destroy.", "ok"),
    (1, "$ terraform apply tfplan", "cmd"),
    (1, "module.vpc.aws_nat_gateway.this[0]: Creation complete after 1m33s", "out"),
    (1, "module.eks.aws_eks_cluster.this[0]: Creation complete after 8m44s", "out"),
    (1, "module.eks.module.eks_managed_node_group[\"default\"]...: Creation complete after 1m59s", "out"),
    (1, "helm_release.lb_controller: Creation complete after 21s", "out"),
    (2, "Apply complete! Resources: 72 added, 0 changed, 0 destroyed.     # 12 min 30 s", "ok"),
], "terraform (recorded, excerpt)"), [
    S("Now let us build it. First, terraform plan. Read the last line before anything else: seventy three to add, zero to change, zero to destroy. "
      "In a shared company account, that zero to change and zero to destroy is your proof that you will not touch anyone else's resources."),
    S("Then terraform apply. The NAT gateway took one and a half minutes. The EKS control plane is the slow part: eight minutes and forty four seconds. The nodes took two minutes, and the load balancer controller twenty one seconds."),
    S("Seventy two resources in twelve and a half minutes. Seventy two, not seventy three, because I switched off one module feature we do not need, an extra identity provider for the older IRSA mechanism. Fewer global IAM objects in a shared account is always better.",
      tts="Seventy two resources in twelve and a half minutes. Seventy two, not seventy three, because I switched off one module feature we do not need, an extra identity provider for the older I R S A mechanism. Fewer global I A M objects in a shared account is always better."),
])

scene(None, "Recorded: the cluster", "Private nodes, two zones, everything running", terminal([
    (0, "$ kubectl get nodes -o wide", "cmd"),
    (0, "NAME                                    STATUS  VERSION              INTERNAL-IP    EXTERNAL-IP", "out"),
    (0, "ip-10-42-14-224.eu-central-1.compute…  Ready   v1.37.0-eks-3b4a6ca  10.42.14.224   <none>", "ok"),
    (0, "ip-10-42-30-26.eu-central-1.compute…   Ready   v1.37.0-eks-3b4a6ca  10.42.30.26    <none>", "ok"),
    (1, "$ aws eks describe-cluster --name eks-devsecops --query '{…}'", "cmd"),
    (1, "authenticationMode: API", "out"),
    (1, "controlPlaneLogs: [api, audit, authenticator]", "out"),
    (1, "secretsEncryptedWithKMS: true", "out"),
    (1, "privateEndpoint: true      publicEndpoint: true   # see the accepted risks", "warn"),
    (2, "$ kubectl get pods -n kube-system", "cmd"),
    (2, "aws-load-balancer-controller-…   2/2 Running    aws-node-…   Running (with network policy agent)", "out"),
    (2, "coredns-…  Running    eks-pod-identity-agent-…  Running    kube-proxy-…  Running", "out"),
], "bash (recorded)"), [
    S("kubectl get nodes: two nodes, Ready, Kubernetes 1.37. Look at the last column: external IP, none. The nodes are not reachable from the internet. "
      "And their internal IPs, 10.42.14 and 10.42.30, are in two different subnets, so two different availability zones.",
      tts="kube control get nodes: two nodes, ready, Kubernetes 1 point 37. Look at the last column: external I P, none. The nodes are not reachable from the internet. "
          "And their internal I Ps, ten forty two fourteen and ten forty two thirty, are in two different subnets, so two different availability zones."),
    S("The cluster settings confirm it: access entries, audit logs, secrets encrypted with KMS. The API endpoint is public, and that is a deliberate trade-off I will explain in the pipeline part.",
      tts="The cluster settings confirm it: access entries, audit logs, secrets encrypted with K M S. The A P I endpoint is public, and that is a deliberate trade-off I will explain in the pipeline part."),
    S("And the system pods are running, including two replicas of the load balancer controller, which Terraform installed with Helm."),
])

# ---------------------------------------------------------------- App + Docker
DOCKERFILE = """FROM node:24-alpine@sha256:ebfe2f90…05ec1c1 AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY index.html vite.config.js ./
COPY public ./public
COPY src ./src
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.30-alpine@sha256:ed04ec1f…dd20b1e
USER 0
RUN apk upgrade --no-cache          # security fixes newer than the base image
USER 101
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080"""
scene("Tool 4: React + Docker", "Tool 4 · React + Docker", "A static React app in a non-root image",
      code("app/Dockerfile (excerpt)", DOCKERFILE, "docker", 20) + notes([
          (0, "React + Vite", "5 unit tests, lint, npm audit"),
          (1, "Multi-stage build", "Node.js never reaches production"),
          (2, "Pinned by digest", "the base image cannot change silently"),
          (3, "nginx-unprivileged", "port 8080, non-root, read-only"),
          (4, "Strict headers", "CSP, frame and sniffing protection"),
      ]), [
    S("Tool four is the application. It is my profile card, rebuilt as a small React app with Vite. It has five unit tests, a linter, and an npm audit for vulnerable dependencies.",
      tts="Tool four is the application. It is my profile card, rebuilt as a small React app with veet. It has five unit tests, a linter, and an N P M audit for vulnerable dependencies."),
    S("The Dockerfile has two stages. Stage one uses Node to build the static files. Stage two only copies the result, so Node.js and all the build tools never reach production.", hl=(1, 8)),
    S("Both base images are pinned by digest, so nobody can swap them for different content behind the same tag.", hl=(1, 1)),
    S("The runtime is nginx unprivileged: it runs as a normal user on port 8080, and in Kubernetes its file system is read-only.", hl=(10, 17),
      tts="The runtime is engine x unprivileged: it runs as a normal user on port 8080, and in Kubernetes its file system is read-only."),
    S("nginx also adds strict security headers to every response, like a content security policy that only allows our own scripts and styles. You will see them later, coming back from the real load balancer.",
      tts="Engine x also adds strict security headers to every response, like a content security policy that only allows our own scripts and styles. You will see them later, coming back from the real load balancer."),
], layout="code")

# ---------------------------------------------------------------- Trivy found a real CVE
scene("Tool 5: Trivy", "Tool 5 · Trivy · recorded", "The scanner blocked my first image", terminal([
    (0, "$ trivy image --severity CRITICAL,HIGH --ignore-unfixed --exit-code 1 profile-card:local", "cmd"),
    (0, "profile-card:local (alpine 3.24.2)", "out"),
    (0, "Total: 1 (HIGH: 1, CRITICAL: 0)", "bad"),
    (0, "│ pcre2 │ CVE-2026-103111 │ HIGH │ fixed │ 10.48-r0 │ 10.49-r0 │ Out-of-bounds write via crafted regular expression", "bad"),
    (0, "gate exit code: 1        # the pipeline would stop here: nothing is pushed", "bad"),
    (1, "# fix in the Dockerfile:  USER 0  /  RUN apk upgrade --no-cache  /  USER 101", "dim"),
    (2, "$ trivy image --severity CRITICAL,HIGH --ignore-unfixed --exit-code 1 profile-card:local", "cmd"),
    (2, "profile-card:local (alpine 3.24.2)   Vulnerabilities: 0", "ok"),
    (2, "gate exit code: 0", "ok"),
], "bash (recorded)"), [
    S("Tool five is Trivy, a free security scanner. And it caught a real problem in my very first image. The official nginx base image, pinned to the latest version, "
      "contained a library called pcre2 with a high severity vulnerability. A fixed version already existed. The gate returned exit code one, so in the pipeline nothing would have been pushed.",
      tts="Tool five is Trivy, a free security scanner. And it caught a real problem in my very first image. The official engine x base image, pinned to the latest version, "
          "contained a library called P C R E 2 with a high severity vulnerability. A fixed version already existed. The gate returned exit code one, so in the pipeline nothing would have been pushed."),
    S("The fix is three lines: switch to root for one command, apply the Alpine security updates, and switch back to the unprivileged user."),
    S("Scan again: zero vulnerabilities, exit code zero. Notice the flag ignore unfixed: we block on problems we can actually fix, so the gate stays strict without becoming noise."),
])

# ---------------------------------------------------------------- CI
scene("Tool 6: GitHub Actions CI", "Tool 6 · GitHub Actions · ci.yaml", "Five security jobs on every pull request", checklist([
    (0, "🔑", "Secret scan", "gitleaks scans the full git history for keys and passwords"),
    (1, "⚛️", "App", "lint, 5 unit tests, npm audit (fails on high), build"),
    (2, "🐳", "Container", "hadolint for the Dockerfile, build, Trivy image gate"),
    (3, "🏗️", "Infrastructure", "terraform fmt + validate, Trivy misconfiguration scan, kubeconform"),
    (4, "⚙️", "Pipeline security", "every action pinned to a commit SHA, actionlint, zizmor"),
]), [
    S("Tool six is GitHub Actions. The CI workflow runs five jobs on every pull request and every push. None of them can touch AWS."),
    S("First, gitleaks scans the entire git history for leaked keys and passwords. Second, the app job runs the linter, the unit tests, the dependency audit and the build.",
      tts="First, git leaks scans the entire git history for leaked keys and passwords. Second, the app job runs the linter, the unit tests, the dependency audit and the build."),
    S("Third, the container job lints the Dockerfile with hadolint, builds the image and runs the Trivy gate you just saw.",
      tts="Third, the container job lints the Dockerfile with hado lint, builds the image and runs the Trivy gate you just saw."),
    S("Fourth, the infrastructure job formats and validates the Terraform, scans Terraform and the Kubernetes manifests for misconfigurations, and checks the manifests against the Kubernetes schemas with kubeconform.",
      tts="Fourth, the infrastructure job formats and validates the Terraform, scans Terraform and the Kubernetes manifests for misconfigurations, and checks the manifests against the Kubernetes schemas with kube conform."),
    S("And fifth, the pipeline checks itself: every third party action must be pinned to a full commit SHA, and actionlint and zizmor look for workflow security mistakes.",
      tts="And fifth, the pipeline checks itself: every third party action must be pinned to a full commit shah, and action lint and zizz-more look for workflow security mistakes."),
])

TRIVYIGNORE = """# Accepted risks: each one is a deliberate trade-off, reviewed, explained and dated.
misconfigurations:
  - id: AWS-0040      # public EKS endpoint
    statement: >-
      GitHub-hosted runners deploy over it, authenticated by IAM (OIDC role
      + access entry scoped to one namespace). Production: private endpoint
      only, with self-hosted runners in the VPC.
    expired_at: 2027-04-01
  - id: AWS-0041      # public endpoint open to 0.0.0.0/0
    statement: GitHub-hosted runners have no fixed IPs (see AWS-0040).
    expired_at: 2027-04-01
  - id: AWS-0104      # nodes may connect out to anywhere
    statement: >-
      Nodes need ECR, EKS, STS and package mirrors via NAT. Pod egress is
      restricted separately by a default-deny NetworkPolicy.
    expired_at: 2027-04-01"""
scene(None, "Tool 5 · Trivy misconfiguration scan", "Security exceptions must be written down",
      code(".trivyignore.yaml (excerpt)", TRIVYIGNORE, "yaml", 20) + notes([
          (0, "3 real findings", "in my own Terraform"),
          (1, "Explained", "why, and the production fix"),
          (2, "Expiring", "re-review by a date"),
          (3, "One more catch", "untrusted registry in a test file"),
      ]), [
    S("When Trivy scanned my Terraform, it reported three critical findings. And they were real: the EKS API endpoint is public, open to any IP address, and the nodes can connect out to anywhere."),
    S("I kept all three, on purpose. GitHub's hosted runners have no fixed IP addresses, so they need the public endpoint, protected by IAM. "
      "The production fix is a private endpoint with self-hosted runners inside the VPC. The important part: each exception is written down, with the reason and the real fix.", hl=(3, 8)),
    S("And each exception expires. On that date the pipeline fails again, and somebody has to look at it. A security exception without an owner and an end date quietly becomes permanent.", hl=(8, 8)),
    S("The scanner also caught me once more. In the CI test I rendered the manifests with a placeholder registry, registry dot example, and Trivy refused it as an untrusted registry. "
      "In the real deployment the image comes from Amazon ECR, so I changed the test to use an ECR-style address."),
], layout="code")

# ---------------------------------------------------------------- OIDC
TRUST = """data "aws_iam_policy_document" "github_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {   # only this repository's production environment
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:sufyanahmadkamboh@25397028/sufyan-devops-eks-devsecops@1403679100:environment:production"]
    }
  }
}"""
scene("Tool 7: OIDC, no stored keys", "Tool 7 · GitHub OIDC → AWS IAM", "The pipeline has no AWS password",
      code("terraform/ecr-and-github.tf (excerpt)", TRUST, "terraform", 18) + notes([
          (0, "Short-lived tokens", "valid for one job, then useless"),
          (1, "Shared provider: read only", "never modified, never deleted"),
          (2, "Strict subject", "one repo, one environment"),
          (3, "Real failure #1", "GitHub's new immutable subject"),
      ]), [
    S("Tool seven is the most important security idea in the pipeline: OIDC. The pipeline stores no AWS access key at all. "
      "Each job asks GitHub for a signed identity token, and AWS exchanges it for temporary credentials that expire after the job.",
      tts="Tool seven is the most important security idea in the pipeline: O I D C. The pipeline stores no A W S access key at all. "
          "Each job asks GitHub for a signed identity token, and AWS exchanges it for temporary credentials that expire after the job."),
    S("This account already had a GitHub identity provider, used by other teams. So Terraform only reads it with a data source. It never changes it, and it never deletes it.", hl=(4, 7)),
    S("The trust policy is strict: the token must be meant for AWS, and its subject must be this exact repository, running in its protected production environment, which only accepts the main branch.", hl=(8, 17)),
    S("And here is real failure number one. My first deploy failed with: not authorized to assume role with web identity. "
      "The reason: new GitHub repositories now use an immutable subject that includes the numeric owner and repository IDs. "
      "That is a security improvement: if someone deletes this repository and creates a new one with the same name, it cannot assume my role. One Terraform change, and the next run worked.", hl=(16, 16)),
], layout="code")

# ---------------------------------------------------------------- CD pipeline
scene("Tool 8: the deploy pipeline", "Tool 8 · deploy.yaml", "Two jobs: scan without credentials, then deploy", svg(
    box(0, 0, 20, 820, 330, "🔍", "Job 1 · Build and scan (no cloud access)", ["build the image with version and commit", "Trivy gate: no fixable CRITICAL or HIGH", "SBOM (CycloneDX)", "hand the scanned image to job 2"], "blue", "#16306a")
    + arrow(1, 825, 185, 895, 185, label="if OK")
    + box(1, 900, 20, 820, 680, "🚀", "Job 2 · Deploy to EKS (production environment)", [
        "OIDC → temporary AWS credentials",
        "push to ECR, by digest",
        "ECR scan on push (second opinion)",
        "cosign: keyless signature + verify",
        "kubectl apply the exact digest",
        "least privilege check",
        "smoke test through the load balancer"], "ok", "#0f2a22")
    + box(2, 0, 400, 820, 300, "🧩", "Why two jobs?", ["the scanning tools never run next to AWS credentials", "a vulnerable image never reaches the registry", "the deploy only ships what job 1 scanned"], "amber", "#2b2410")
), [
    S("Tool eight is the deploy workflow. It runs on every push to main, and it is split into two jobs. Job one builds the image and scans it, with no cloud access at all."),
    S("Only if job one passed does job two start, inside the protected production environment. It gets temporary AWS credentials through OIDC, pushes the image to ECR by digest, "
      "waits for ECR's own scan as a second opinion, signs the image with cosign, deploys that exact digest, checks its own permissions, and finally tests the live site through the load balancer.",
      tts="Only if job one passed does job two start, inside the protected production environment. It gets temporary AWS credentials through O I D C, pushes the image to E C R by digest, "
          "waits for E C R's own scan as a second opinion, signs the image with co-sign, deploys that exact digest, checks its own permissions, and finally tests the live site through the load balancer."),
    S("Why two jobs? The scanning tools never run next to AWS credentials, a vulnerable image never even reaches the registry, and the deploy can only ship exactly what job one scanned."),
])

scene(None, "Recorded: GitHub Actions run", "Push to live in 3 minutes 37 seconds",
      shot(0, "gh-run.png", "GitHub Actions run", "max-height:700px"), [
    S("Here is a real run, triggered by a push. Build and scan: thirty three seconds. Deploy to EKS: two minutes and fifty four seconds. Three minutes and thirty seven seconds from git push to live, "
      "and GitHub attaches the live URL to the deployment."),
    S("Getting here took two more real fixes, and both are lessons. ECR's scan result is not available for a few seconds after a push, and the standard AWS CLI waiter gives up instead of waiting. "
      "And when an image has zero findings, ECR returns nothing at all, which my first check treated as a failure. Pipelines are code. They need testing, too.",
      tts="Getting here took two more real fixes, and both are lessons. E C R's scan result is not available for a few seconds after a push, and the standard A W S C L I waiter gives up instead of waiting. "
          "And when an image has zero findings, E C R returns nothing at all, which my first check treated as a failure. Pipelines are code. They need testing, too."),
])

scene(None, "Recorded: inside the deploy job", "Signed, deployed, and limited to one namespace", terminal([
    (0, "ECR scan status: COMPLETE", "ok"),
    (0, "ECR findings by severity: {}", "ok"),
    (0, "signed and verified", "ok"),
    (1, "serviceaccount/profile-card created         service/profile-card created", "out"),
    (1, "deployment.apps/profile-card created        poddisruptionbudget.policy/profile-card created", "out"),
    (1, "ingress.networking.k8s.io/profile-card created", "out"),
    (1, "networkpolicy.networking.k8s.io/default-deny created", "out"),
    (1, "deployment \"profile-card\" successfully rolled out", "ok"),
    (2, "can-i create deployments -n profile-card -> yes (expected yes)", "ok"),
    (2, "can-i create deployments -n kube-system -> no (expected no)", "ok"),
    (2, "can-i get secrets -n kube-system -> no (expected no)", "ok"),
    (2, "can-i create clusterrolebindings -> no (expected no)", "ok"),
    (2, "can-i delete namespaces -> no (expected no)", "ok"),
], "GitHub Actions log (recorded, excerpt)"), [
    S("Inside the deploy job: the ECR scan completed with zero findings, and the cosign signature was created and verified.",
      tts="Inside the deploy job: the E C R scan completed with zero findings, and the co-sign signature was created and verified."),
    S("kubectl applies the service account, service, deployment, disruption budget, ingress and network policies, and waits until the rollout is complete.",
      tts="Kube control applies the service account, service, deployment, disruption budget, ingress and network policies, and waits until the rollout is complete."),
    S("And then the pipeline proves its own limits. kubectl auth can-i: yes, it may create deployments in its own namespace. "
      "But it may not touch kube-system, not read secrets, not grant itself cluster permissions, and not delete namespaces. If any answer changes, the job fails.",
      tts="And then the pipeline proves its own limits. Kube control auth can I: yes, it may create deployments in its own namespace. "
          "But it may not touch kube system, not read secrets, not grant itself cluster permissions, and not delete namespaces. If any answer changes, the job fails."),
])

# ---------------------------------------------------------------- Ingress / LB controller
INGRESS = """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: profile-card
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip      # straight to pod IPs
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}]'
    alb.ingress.kubernetes.io/healthcheck-path: /healthz
    alb.ingress.kubernetes.io/load-balancer-attributes: >-
      routing.http.drop_invalid_header_fields.enabled=true
spec:
  ingressClassName: alb
  rules:
    - http:
        paths:
          - {path: /, pathType: Prefix,
             backend: {service: {name: profile-card, port: {name: http}}}}"""
scene("Tool 9: Ingress + load balancer", "Tool 9 · AWS Load Balancer Controller", "One Ingress becomes a real AWS load balancer",
      code("k8s/ingress.yaml", INGRESS, "yaml", 20) + notes([
          (0, "Controller via Helm", "AWS access by Pod Identity"),
          (1, "internet-facing ALB", "in the public subnets"),
          (2, "target-type ip", "traffic straight to the pods"),
          (3, "No domain → HTTP", "TLS needs a certificate for a name"),
      ]), [
    S("Tool nine exposes the app to the internet. The AWS Load Balancer Controller, installed by Terraform with Helm, watches for Ingress objects and creates real AWS load balancers. "
      "It gets its AWS permissions through EKS Pod Identity, so there are no keys in the cluster either."),
    S("Our Ingress asks for an internet facing Application Load Balancer, which the controller places in the public subnets.", hl=(6, 6)),
    S("Target type IP sends traffic straight to the pod IP addresses, health checks use the healthz endpoint, and invalid HTTP headers are dropped at the edge.", hl=(7, 11)),
    S("One honest limitation: I have no domain name for this lab, and a TLS certificate needs a name. So the site runs on plain HTTP. "
      "With a domain you add a certificate from AWS Certificate Manager and two annotations, and the load balancer does HTTPS."),
], layout="code")

scene(None, "Recorded: live on the internet", "It works, with every security header", terminal([
    (0, "$ kubectl -n profile-card get ingress,deploy,pods -o wide", "cmd"),
    (0, "ingress/profile-card  alb  eks-devsecops-profile-card-604868946.eu-central-1.elb.amazonaws.com  80", "ok"),
    (0, "deployment/profile-card   2/2   …/eks-devsecops/profile-card@sha256:3213072…", "out"),
    (0, "pod/profile-card-…-29jvv  Running  10.42.8.223   ip-10-42-14-224…   (zone a)", "out"),
    (0, "pod/profile-card-…-qc4xf  Running  10.42.18.155  ip-10-42-30-26…    (zone b)", "out"),
    (1, "$ curl -sS -D - -o /dev/null http://eks-devsecops-profile-card-604868946.eu-central-1.elb.amazonaws.com/", "cmd"),
    (1, "HTTP/1.1 200 OK", "ok"),
    (1, "Content-Security-Policy: default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self'; …", "out"),
    (1, "X-Content-Type-Options: nosniff     X-Frame-Options: DENY     Referrer-Policy: no-referrer", "out"),
    (1, "Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()", "out"),
], "bash (recorded)"), [
    S("And here it is, live. The Ingress got a public load balancer address. The deployment runs an exact image digest, never a tag, and the two pods run on different nodes, in different zones."),
    S("curl through the load balancer: HTTP 200, with the content security policy and the other security headers, coming all the way from nginx in the private subnet.",
      tts="Curl through the load balancer: H T T P 200, with the content security policy and the other security headers, coming all the way from engine x in the private subnet."),
])

scene(None, "Recorded: the browser", "The profile card, served from Amazon EKS",
      shot(0, "app-live.png", "The app in a browser", "height:690px;width:auto"), [
    S("In the browser: the profile card, served from Amazon EKS. The footer shows the version and the git commit, which the pipeline bakes into every build, so you always know exactly what is running."),
])

# ---------------------------------------------------------------- k8s security
DEPLOY = """spec:
  template:
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10101          # above 10000: no clash with node users
        seccompProfile: {type: RuntimeDefault}
      containers:
        - name: web
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: [ALL]}
          resources:
            limits: {cpu: 200m, memory: 64Mi}
          readinessProbe: {httpGet: {path: /healthz, port: http}}
          volumeMounts: [{name: tmp, mountPath: /tmp}]   # the only writable path"""
scene("Tool 10: Kubernetes security", "Tool 10 · Kubernetes security", "Least privilege inside the cluster too",
      code("k8s/deployment.yaml (excerpt)", DEPLOY, "yaml", 20) + notes([
          (0, "No API token", "the app never calls Kubernetes"),
          (1, "Non-root, seccomp", "Trivy: 99 of 99 checks passed"),
          (2, "Read-only, no capabilities", "only /tmp is writable"),
          (3, "Limits + probes", "fair share, self-healing"),
          (4, "Namespace: restricted", "Pod Security enforced by Terraform"),
      ]), [
    S("Tool ten is Kubernetes itself. The pod does not get a service account token, because the app never talks to the Kubernetes API.", hl=(4, 4)),
    S("It runs as a non-root user with a high user ID, and with the default seccomp profile, which blocks dangerous system calls.", hl=(5, 8)),
    S("The container cannot escalate privileges, its file system is read-only, and all Linux capabilities are dropped. The only writable place is a small temporary folder.", hl=(11, 18)),
    S("CPU and memory limits keep it from starving its neighbours, and the readiness probe means traffic only reaches a pod that is actually ready.", hl=(15, 17)),
    S("And the namespace itself, created by Terraform, enforces the Kubernetes Pod Security standard called restricted. Let us see what that does to an attacker."),
], layout="code")

# ---------------------------------------------------------------- Attacks
scene("Attacking my own cluster", "Recorded attacks", "Three attacks, three refusals", terminal([
    (0, "$ kubectl -n profile-card run attacker --image=busybox --privileged -- sleep 60", "cmd"),
    (0, "Error from server (Forbidden): pods \"attacker\" is forbidden: violates PodSecurity \"restricted:latest\":", "bad"),
    (0, "  privileged, allowPrivilegeEscalation != false, unrestricted capabilities, runAsNonRoot != true, seccompProfile", "bad"),
    (1, "$ kubectl -n profile-card exec profile-card-… -- wget -T 5 http://example.com", "cmd"),
    (1, "wget: bad address 'example.com'          # default-deny: not even DNS gets out", "bad"),
    (2, "$ kubectl run imds-test --image=curlimages/curl -- curl -X PUT http://169.254.169.254/latest/api/token", "cmd"),
    (2, "-> no token: blocked (hop limit 1)", "bad"),
    (2, "IMDSv1 request without a token: 401", "bad"),
], "bash (recorded)"), [
    S("Time to attack. First, I try to start a privileged container in the app namespace, which would give it almost full control of the node. "
      "Refused by Pod Security, with a list of five violations."),
    S("Second, I pretend an attacker got into the app pod and tries to download a tool. It cannot even resolve a domain name: the default deny network policy blocks all outgoing traffic, including DNS."),
    S("Third, the classic cloud attack: from a pod, ask the instance metadata service for the node's AWS credentials. The token request times out, because of the hop limit of one we set in Terraform. "
      "And the old version one interface, without a token, answers 401. The node's credentials are out of reach."),
])

scene(None, "Attack #4 · recorded", "The attack that worked: lateral movement", terminal([
    (0, "# NetworkPolicy v1: allow port 8080 from the VPC (10.42.0.0/16)", "dim"),
    (0, "$ kubectl -n default run lateral-test --image=curlimages/curl -- curl http://<profile-card pod IP>:8080/", "cmd"),
    (0, "from another namespace: HTTP 200", "bad"),
    (1, "# on EKS, pod IPs ARE VPC IPs: \"the VPC\" includes every pod in the cluster", "warn"),
    (2, "# NetworkPolicy v2: allow port 8080 only from the load balancer subnets (10.42.48.0/23)", "dim"),
    (2, "t+30s ready=2/2 alb=200        t+90s ready=2/2 alb=200", "ok"),
    (3, "$ kubectl -n default run lateral-test2 --image=curlimages/curl -- curl http://<profile-card pod IP>:8080/", "cmd"),
    (3, "curl: (28) Connection timed out after 5002 milliseconds", "ok"),
    (3, "from another namespace: blocked", "ok"),
], "bash (recorded)"), [
    S("The fourth attack worked. My first network policy allowed port 8080 from the whole VPC, because the load balancer lives in the VPC. "
      "From a pod in a different namespace, I could reach the app directly: HTTP 200."),
    S("The reason is an EKS detail that catches many people. With the VPC CNI, pod IP addresses come from the VPC range. So allow the VPC also means allow every pod in the cluster."),
    S("The fix: only allow the two public subnets, where the load balancer's network interfaces live. I tested it live first: the pods stayed ready and the load balancer kept answering."),
    S("And the lateral attack now times out. The fix went into git, and the pipeline deployed it."),
])

scene(None, "Attack #5 · recorded", "Dropping requests during a deploy", grid([
    tile(0, "📉", "Before: plain rolling update", "3 of 280 failed", "bad", "1 × HTTP 502, 2 timeouts, 155 s"),
    tile(1, "🚦", "Pod readiness gates", "ALB says ready", "blue", "namespace label, set by Terraform"),
    tile(1, "⏳", "preStop sleep 15 s", "keep serving", "blue", "while the ALB deregisters the pod"),
    tile(1, "🔌", "Deregistration delay 10 s", "shorter than 15 s", "blue", "Ingress annotation"),
    tile(2, "📈", "After: same test", "401 of 401 OK", "ok", "0 errors, 211 s"),
    tile(3, "🔀", "Watch out", "version skew", "amber", "old and new pods serve side by side for ~28 s"),
], cols=3, gap=20), [
    S("The fifth attack was not an attacker, it was my own deployment. I requested the site twice a second while the pipeline rolled out a new version. "
      "Three requests out of two hundred and eighty failed: one bad gateway error, and two timeouts. Small, but in production that is real users getting errors."),
    S("The cause: a pod was stopped before the load balancer had stopped sending it traffic. The fix has three parts. Pod readiness gates, so a new pod only counts as ready when the load balancer says it is healthy. "
      "A pre-stop pause of fifteen seconds, so a terminating pod keeps serving. And a load balancer deregistration delay of ten seconds, shorter than that pause."),
    S("Same test, after the fix: four hundred and one requests, four hundred and one successful. Zero downtime, measured."),
    S("One more thing the test revealed: for about twenty eight seconds, the old and the new version served side by side. For a single page app that can mean an old page asks a new pod for an old file. "
      "Teams solve that by keeping old assets for a while, or by serving them from a CDN."),
])

# ---------------------------------------------------------------- Teardown
scene("Teardown: delete everything", "Recorded: scripts/teardown.sh", "Delete everything, then prove it", terminal([
    (0, "$ scripts/teardown.sh", "cmd"),
    (0, "==> Deleting the Ingress (the controller removes the load balancer)", "out"),
    (0, "==> Load balancer deleted", "ok"),
    (1, "==> terraform destroy", "out"),
    (1, "module.vpc.aws_nat_gateway.this[0]: Destruction complete after 1m20s", "out"),
    (1, "module.eks.aws_eks_cluster.this[0]: Destruction complete after 3m29s", "out"),
    (1, "Destroy complete! Resources: 72 destroyed.", "ok"),
    (2, "$ scripts/verify-teardown.sh", "cmd"),
    (2, "  gone  EKS cluster   gone  VPC   gone  subnets   gone  NAT gateways   gone  Elastic IPs", "ok"),
    (2, "  gone  EC2 instances   gone  load balancer   gone  ECR repository   gone  CloudWatch log groups", "ok"),
    (2, "  gone  anything else tagged Project=eks-devsecops   gone  IAM roles   gone  IAM policies", "ok"),
    (2, "  kept  GitHub OIDC identity provider", "ok"),
    (2, "Clean: nothing of this project is left.", "ok"),
], "bash (recorded, excerpt)"), [
    S("And now, the part that most tutorials skip: deleting everything. The order matters. The load balancer was created by the controller, not by Terraform, "
      "so if you run terraform destroy first, the load balancer and its security groups are left behind, and deleting the VPC fails. So the script deletes the Ingress first, and waits until the load balancer is gone."),
    S("Then terraform destroy: seventy two resources destroyed. The cluster took three and a half minutes, the NAT gateway one minute twenty."),
    S("And then a separate script proves it: every resource type, by name and by tag, is checked. Everything is gone, and the shared GitHub identity provider is still there, untouched. "
      "Two more lessons from this script. The AWS tagging index still lists deleted resources for a while, so the script checks each one's real state. "
      "And the encryption key waits seven days before AWS really deletes it, which costs nothing."),
])

scene(None, "The bill", "62 minutes on AWS", grid([
    tile(0, "☸️", "EKS control plane", "~$0.10/h", "blue", "eu-central-1"),
    tile(0, "🖥️", "2 × t3.medium", "~$0.10/h", "blue", "private nodes"),
    tile(0, "🌐", "NAT gateway", "~$0.05/h", "blue", "+ data"),
    tile(0, "⚖️", "Load balancer, IPs, logs, KMS", "~$0.05/h", "blue", ""),
    tile(1, "⏱️", "Time on AWS", "62 min", "amber", "first apply → verified teardown"),
    tile(1, "💶", "Estimated total", "≈ $0.35", "ok", "on-demand prices; the bill confirms"),
], cols=3, gap=20), [
    S("What did this cost? At on-demand prices in Frankfurt, this setup costs roughly thirty cents per hour: the EKS control plane, two small nodes, the NAT gateway, and the load balancer."),
    S("From the first terraform apply to the verified teardown, it ran for sixty two minutes. That is an estimated thirty five cents. Delete your lab when you are done, and Kubernetes on AWS is a very cheap thing to learn."),
])

# ---------------------------------------------------------------- Production next steps
scene("From lab to production", "Next steps", "What I would add for real production", grid([
    card(0, "🔒", "HTTPS", "domain + ACM certificate + HTTP→HTTPS redirect", "blue"),
    card(0, "🛡️", "AWS WAF", "on the load balancer: common attacks, rate limits", "blue"),
    card(1, "🏠", "Private API endpoint", "self-hosted runners inside the VPC", "blue"),
    card(1, "🌐", "NAT per zone", "no single point of failure", "blue"),
    card(2, "🗄️", "Remote state", "S3 with locking, not a laptop", "blue"),
    card(2, "✍️", "Verify signatures at admission", "Kyverno: only signed images run (my previous project)", "blue"),
    card(3, "📈", "Autoscaling + observability", "HPA, Karpenter, Prometheus, Grafana, alerts", "blue"),
], cols=2, gap=18), [
    S("What would I add for real production? HTTPS with your domain and a certificate, and AWS WAF on the load balancer to block common attacks and abusive traffic."),
    S("A private API endpoint with self-hosted runners inside the VPC, which removes two of the accepted risks, and one NAT gateway per zone."),
    S("Terraform state in S3 with locking, so a team can work on it safely, and signature verification at admission, so the cluster only runs images that this pipeline signed. My previous project shows exactly that, with Kyverno."),
    S("And autoscaling with the horizontal pod autoscaler and Karpenter, plus monitoring and alerts."),
])

# ---------------------------------------------------------------- Hands-on
scene("Hands-on: build it yourself", "Hands-on", "Build it in your own AWS account", checklist([
    (0, "1", "Prepare", "AWS account, Terraform 1.10+, AWS CLI, kubectl, a fork of the repository"),
    (1, "2", "Adjust", "variables: github_repository and github_oidc_subject_prefix (read it with gh api …/oidc/customization/sub)"),
    (2, "3", "Build", "export TF_VAR_allowed_account_id=…; terraform -chdir=terraform apply (about 13 minutes)"),
    (3, "4", "Connect the pipeline", "terraform output → GitHub secret AWS_DEPLOY_ROLE_ARN (environment production), variable DEPLOY_ENABLED=true"),
    (4, "5", "Push and watch", "a commit to main builds, scans, signs and deploys; the run shows the URL"),
    (5, "6", "Delete it the same day", "scripts/teardown.sh, then read the verification output"),
]), [
    S("Want to build it yourself? You need an AWS account, Terraform, the AWS CLI and kubectl, and your own fork of the repository.",
      tts="Want to build it yourself? You need an A W S account, Terraform, the A W S C L I and kube control, and your own fork of the repository."),
    S("Change two variables to your fork: the repository name, and the OIDC subject prefix. The command to read your prefix is in the README.",
      tts="Change two variables to your fork: the repository name, and the O I D C subject prefix. The command to read your prefix is in the read me."),
    S("Set your account ID as the allowed account, and run terraform apply. It takes about thirteen minutes."),
    S("Put the deploy role from the Terraform output into a GitHub secret in the production environment, and switch on the deploy variable."),
    S("Push a commit to main and watch the pipeline deploy it. The run shows you the live URL."),
    S("And please, delete it the same day: run the teardown script, and read the verification output. Then your bill stays at cents."),
])

# ---------------------------------------------------------------- Outro
scene("Summary", "Thanks for watching", "From laptop to EKS, securely, and back to zero", grid([
    card(0, "🏗️", "72 resources as code", "VPC, EKS, ECR, IAM: 12.5 min up, 15 min down", "ok"),
    card(0, "🔐", "No stored cloud keys", "OIDC, Pod Identity, least privilege, proven by can-i", "ok"),
    card(0, "🔍", "Scanned at every step", "code, config, image, registry; a real CVE blocked", "ok"),
    card(1, "🕵️", "5 attacks, 5 lessons", "3 refused, 2 found real weaknesses, both fixed", "amber"),
    card(2, "💻", "Code + docs", REPO, "blue"),
    card(2, "💬", "Your turn", "which attack would you try next? Tell me in the comments", "blue"),
], cols=3, gap=18), [
    S("That is the project. Seventy two AWS resources as code, a pipeline with no stored cloud keys, scanning at every step, and five attacks: three refused, and two that found real weaknesses, which we fixed."),
    S("Most of what you learned here comes from the failures: the scanner finding a real vulnerability, the new GitHub subject format, the lateral movement, and the dropped requests. That is what real DevOps work looks like."),
    S("The code and the documentation are linked in the description. Which attack would you try next? Tell me in the comments, and subscribe for the next real project. Thanks for watching."),
])
