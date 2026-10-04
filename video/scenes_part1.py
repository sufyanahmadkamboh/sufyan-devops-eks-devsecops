"""Workshop video, part 1: build the platform.

Everything shown was recorded on 2026-10-04 from a fresh clone of the repository, on a real AWS account in
eu-central-1: terminal output (redacted by redact.py) and AWS Console screenshots taken through a read-only
federated session, redacted in the page and checked by OCR before use.
"""

from __future__ import annotations

from components import arrow, box, card, checklist, code, grid, label, notes, svg, terminal, tile


def S(say: str, hl: tuple[int, int] | None = None, tts: str | None = None) -> dict:
    return {"say": say, "hl": hl, "tts": tts}


def shot(s: int, src: str, alt: str, style: str = "height:700px;width:auto") -> str:
    return f'<img class="shot st" data-s="{s}" src="../../assets/workshop/{src}" alt="{alt}" style="{style}">'


SCENES: list[dict] = []


def scene(chapter, kicker, title, body, steps, layout="full"):
    SCENES.append({"chapter": chapter, "kicker": kicker, "title": title, "body": body, "steps": steps, "layout": layout})


# ---------------------------------------------------------------- 1. Hook
scene("The problem we are solving", "Workshop · part 1 of 2", "Push code. It gets tested, scanned, signed and deployed. No AWS keys in GitHub.", svg(
    box(0, 0, 40, 520, 240, "🧑‍💻", "A developer pushes code", ["that is all they do"], "blue")
    + arrow(1, 525, 160, 615, 160)
    + box(1, 620, 40, 540, 240, "🛡️", "The platform checks it", ["secrets, tests, dependencies,", "Dockerfile, infrastructure, image"], "amber", "#2b2410")
    + arrow(2, 1165, 160, 1255, 160)
    + box(2, 1260, 40, 460, 240, "☸️", "Amazon EKS", ["signed image, by digest,", "behind a load balancer"], "ok", "#0f2a22")
    + box(3, 200, 360, 1320, 200, "🔑", "And GitHub never holds an AWS password", ["temporary credentials through OIDC, valid for one job"], "violet")
    + label(4, 860, 650, "part 1: build the platform · part 2: ship it, break it, tear it down", 32, "sky", "middle", 800)
), [
    S("Here is the question this workshop answers. How do we build a secure, repeatable Kubernetes platform on AWS, where a developer just pushes code, "
      "and that code is automatically tested, security scanned, signed, and safely deployed to EKS?"),
    S("Every push goes through the same checks: leaked secrets, unit tests, vulnerable dependencies, the Dockerfile, the infrastructure code, and the container image itself."),
    S("Only then is the image deployed to Amazon EKS, by its exact digest, behind an AWS load balancer."),
    S("And all of that happens without a single AWS access key stored in GitHub."),
    S("I will build the whole thing with you on a real AWS account, from a fresh clone of the repository. In part one, we build the platform. "
      "In part two, we ship code through the pipeline, break things on purpose, troubleshoot them, and tear everything down. Let us start with why."),
])

# ---------------------------------------------------------------- 2. Real-world problems
scene(None, "Why this project exists", "What goes wrong without a platform like this", grid([
    card(0, "🔑", "Long-lived AWS keys in CI", "one leak gives an attacker your cloud for months", "bad"),
    card(1, "🐛", "Security checked at the end", "or never: vulnerable code ships first", "bad"),
    card(2, "📦", "Unknown image contents", "no SBOM, so 'are we affected?' takes days", "bad"),
    card(3, "✍️", "No proof of origin", "anyone with registry access can push an image", "bad"),
    card(4, "👑", "Containers as root", "one bug, and the attacker owns the node", "bad"),
    card(5, "🧱", "Hand-built infrastructure", "nobody can rebuild it, nobody can review it", "bad"),
], cols=3), [
    S("Let us be concrete about the problems. First, long lived AWS keys stored in the CI system. If one leaks, an attacker has your cloud account until someone notices."),
    S("Second, security as a final step. Someone scans the application after it is already in production, or nobody scans it at all."),
    S("Third, nobody knows what is inside the container image. When the next big library vulnerability is announced, answering 'are we affected?' takes days instead of a search."),
    S("Fourth, no proof of where an image came from. Anyone who can push to the registry can put an image there."),
    S("Fifth, containers that run as root, with full Linux capabilities. One application bug, and the attacker controls the node."),
    S("And sixth, infrastructure built by clicking around in the console. Nobody can review it, and nobody can rebuild it exactly."),
])

scene(None, "The choices, and why", "Each tool solves one of those problems", grid([
    card(0, "☸️", "Amazon EKS", "managed Kubernetes: AWS runs the control plane, we focus on workloads"),
    card(1, "🏗️", "Terraform", "the whole platform as reviewable, repeatable, destroyable code"),
    card(2, "🛡️", "DevSecOps", "security checks inside the pipeline, before anything ships"),
    card(3, "🔍 🧾 ✍️", "Scan · SBOM · sign", "known vulnerabilities, a parts list, proof of origin"),
    card(4, "🪪", "GitHub OIDC", "temporary credentials instead of stored keys"),
    card(5, "🔒", "Restricted workloads", "non-root, read-only, no capabilities, network policies"),
], cols=3), [
    S("So each tool in this project answers one of those problems. EKS gives us managed Kubernetes: AWS runs and patches the control plane, and we focus on our workloads.",
      tts="So each tool in this project answers one of those problems. E K S gives us managed Kubernetes: AWS runs and patches the control plane, and we focus on our workloads."),
    S("Terraform turns the whole platform into code: reviewed in a pull request, rebuilt identically, and destroyed with one command."),
    S("DevSecOps means the security checks live inside the pipeline. A problem is caught minutes after the push, not months after the release."),
    S("Image scanning catches known vulnerabilities, the SBOM lists every component, and the signature proves the image came from our pipeline.",
      tts="Image scanning catches known vulnerabilities, the S-bom lists every component, and the signature proves the image came from our pipeline."),
    S("GitHub OIDC replaces stored AWS keys with temporary credentials, valid for one job."),
    S("And the workload itself runs restricted: non-root, a read-only file system, no Linux capabilities, and network policies around it."),
])

# ---------------------------------------------------------------- 3. Architecture: delivery flow
scene("The architecture", "Architecture · the delivery flow", "From a git push to a public URL", svg(
    box(0, 0, 0, 330, 120, "🧑‍💻", "Developer", ["git push"], "blue")
    + arrow(0, 335, 60, 395, 60)
    + box(0, 400, 0, 330, 120, "🐙", "GitHub", ["repository"], "blue")
    + arrow(1, 735, 60, 795, 60)
    + box(1, 800, 0, 920, 220, "⚙️", "GitHub Actions: security checks", ["gitleaks · lint · unit tests · npm audit", "hadolint · Trivy IaC scan (Terraform + Kubernetes)", "pinned actions · actionlint · zizmor"], "amber", "#2b2410")
    + arrow(2, 1260, 225, 1260, 275)
    + box(2, 800, 280, 920, 170, "🐳", "Docker build", ["Trivy image scan (CRITICAL/HIGH block) · SBOM · cosign signature"], "amber", "#2b2410")
    + arrow(3, 795, 365, 735, 365)
    + box(3, 400, 300, 330, 130, "📦", "Amazon ECR", ["by digest"], "blue")
    + arrow(3, 565, 435, 565, 495)
    + box(4, 0, 500, 1100, 200, "☸️", "EKS: Kubernetes", ["Pod Security restricted · NetworkPolicy · limits · health probes", "2 replicas · PodDisruptionBudget"], "ok", "#0f2a22")
    + arrow(5, 1105, 600, 1165, 600)
    + box(5, 1170, 500, 550, 200, "🌍", "Load Balancer Controller", ["→ Application Load Balancer", "→ public application URL"], "ok", "#0f2a22")
), [
    S("Before we create anything, here is the complete picture. A developer pushes code to the GitHub repository."),
    S("GitHub Actions runs the security checks first: gitleaks for secrets, lint and unit tests, npm audit, hadolint for the Dockerfile, and a Trivy scan of the Terraform and Kubernetes files. "
      "It even checks the pipeline itself.",
      tts="GitHub Actions runs the security checks first: git leaks for secrets, lint and unit tests, N P M audit, hado lint for the Dockerfile, and a Trivy scan of the Terraform and Kubernetes files. "
          "It even checks the pipeline itself."),
    S("Only then does it build the Docker image, scan it with Trivy, generate an SBOM, and sign it with cosign.",
      tts="Only then does it build the Docker image, scan it with Trivy, generate an S-bom, and sign it with co-sign."),
    S("The image goes to Amazon ECR, the container registry, and it is referenced by its digest, never just a tag."),
    S("EKS runs it with security restrictions: Pod Security, network policies, resource limits, health probes, two replicas and a disruption budget.",
      tts="E K S runs it with security restrictions: pod security, network policies, resource limits, health probes, two replicas and a disruption budget."),
    S("And the AWS Load Balancer Controller turns our Kubernetes Ingress into an Application Load Balancer with a public URL."),
])

scene(None, "Architecture · the AWS side", "What lives inside eu-central-1", svg(
    box(0, 0, 0, 1720, 740, "☁️", "AWS eu-central-1 (Frankfurt)", [], "amber", "#111c2e")
    + box(1, 40, 80, 800, 360, "🌐", "VPC 10.42.0.0/16 · 2 availability zones", [
        "public subnets: load balancer, NAT gateway",
        "private subnets: EKS worker nodes (2 × t3.medium)",
        "no public IPs on nodes", "flow logs to CloudWatch"], "blue", "#16306a")
    + box(2, 880, 80, 800, 170, "☸️", "EKS control plane (managed by AWS)", ["Kubernetes 1.37 · audit logs · access entries"], "ok", "#0f2a22")
    + box(3, 880, 270, 390, 170, "🔐", "KMS", ["encrypts Kubernetes secrets"], "violet")
    + box(3, 1290, 270, 390, 170, "📦", "ECR", ["immutable images, scanned"], "blue")
    + box(4, 40, 470, 520, 230, "📈", "CloudWatch", ["control plane logs", "VPC flow logs"], "blue")
    + box(4, 600, 470, 520, 230, "🪪", "IAM (global)", ["only roles named eks-devsecops-*", "shared GitHub OIDC provider: read only"], "violet")
    + box(5, 1160, 470, 520, 230, "⚖️", "Application Load Balancer", ["created by the controller", "from the Kubernetes Ingress"], "ok", "#0f2a22")
), [
    S("And here is the AWS side. Everything lives in one region, Frankfurt."),
    S("A VPC with two availability zones. Public subnets hold only the load balancer and the NAT gateway. The two worker nodes live in private subnets, without public IP addresses, and VPC flow logs record the traffic.",
      tts="A V P C with two availability zones. Public subnets hold only the load balancer and the NAT gateway. The two worker nodes live in private subnets, without public I P addresses, and V P C flow logs record the traffic."),
    S("The EKS control plane is managed by AWS. It writes audit logs, and access is controlled with access entries.",
      tts="The E K S control plane is managed by AWS. It writes audit logs, and access is controlled with access entries."),
    S("KMS encrypts the Kubernetes secrets, and ECR stores our images.", tts="K M S encrypts the Kubernetes secrets, and E C R stores our images."),
    S("CloudWatch keeps the logs. IAM is global, so we are careful there: we only create roles whose names start with eks-devsecops, and we only read the shared GitHub identity provider, never change it.",
      tts="CloudWatch keeps the logs. I A M is global, so we are careful there: we only create roles whose names start with E K S dev sec ops, and we only read the shared GitHub identity provider, never change it."),
    S("The Application Load Balancer is the odd one out: Terraform does not create it. The load balancer controller creates it from our Kubernetes Ingress. Remember that, because it matters a lot when we tear things down."),
])

scene(None, "How the parts talk to each other", "Who calls whom, and with which identity", checklist([
    (0, "1", "Internet → ALB → pods", "HTTP to the load balancer, which forwards straight to pod IPs in the private subnets"),
    (1, "2", "Nodes → internet", "outbound only, through the NAT gateway: pulling images, AWS APIs"),
    (2, "3", "GitHub Actions → AWS", "OIDC token exchanged for a short-lived role: push to ECR, describe the cluster"),
    (3, "4", "GitHub Actions → Kubernetes", "the same role, mapped by an access entry to one namespace only"),
    (4, "5", "Controller → AWS", "EKS Pod Identity: the controller pod gets credentials, no keys stored"),
]), [
    S("How do these parts talk to each other? Internet traffic reaches the load balancer, and the load balancer forwards it straight to the pod IP addresses in the private subnets."),
    S("The nodes can reach out, through the NAT gateway, for example to pull images, but nothing on the internet can reach in."),
    S("GitHub Actions talks to AWS with a short lived role from OIDC. That role can push to our container registry and describe our cluster.",
      tts="GitHub Actions talks to AWS with a short lived role from O I D C. That role can push to our container registry and describe our cluster."),
    S("The same role reaches Kubernetes through an access entry, which limits it to a single namespace."),
    S("And the load balancer controller gets its AWS permissions through EKS Pod Identity. No access keys are stored anywhere in the cluster.",
      tts="And the load balancer controller gets its AWS permissions through E K S pod identity. No access keys are stored anywhere in the cluster."),
])

# ---------------------------------------------------------------- 4. Pipeline overview
scene("The DevSecOps pipeline", "Before we run it", "This is DevSecOps, not just CI/CD", '<div class="compact">' + grid([
    tile(0, "🔑", "Secret scan", "gitleaks", "amber"),
    tile(0, "🧪", "Lint + unit tests", "oxlint · vitest", "blue"),
    tile(0, "📦", "Dependencies", "npm audit", "amber"),
    tile(0, "🐳", "Dockerfile", "hadolint", "amber"),
    tile(1, "🏗️", "Terraform + Kubernetes", "Trivy config", "amber"),
    tile(1, "🔍", "Image scan", "Trivy image", "amber"),
    tile(1, "🧾", "SBOM", "Syft", "amber"),
    tile(1, "✍️", "Signature", "cosign", "amber"),
    tile(2, "📌", "Deploy by digest", "kubectl apply", "ok"),
    tile(2, "⏳", "Rollout", "rollout status", "ok"),
    tile(2, "🎯", "Permissions proof", "kubectl auth can-i", "ok"),
    tile(2, "🌍", "Health check", "smoke test via ALB", "ok"),
], cols=4, gap=16) + "</div>", [
    S("Here is the pipeline we are about to run. Notice how many stages are security stages, marked in amber. Secrets, dependencies, the Dockerfile, the infrastructure code."),
    S("Then the image itself: a vulnerability scan, an SBOM, and a signature. A classic CI/CD pipeline builds and deploys. A DevSecOps pipeline also refuses to deploy what it cannot trust.",
      tts="Then the image itself: a vulnerability scan, an S-bom, and a signature. A classic C I C D pipeline builds and deploys. A dev sec ops pipeline also refuses to deploy what it cannot trust."),
    S("And the deployment itself is verified: the exact digest is deployed, the rollout must finish, the pipeline proves its own permissions are limited, and a smoke test goes through the real load balancer."),
])

# ---------------------------------------------------------------- 5. Repository tour
scene("The repository", "Recorded · fresh clone", "What we are about to build", terminal([
    (0, "$ git clone https://github.com/sufyanahmadkamboh/sufyan-devops-eks-devsecops.git", "cmd"),
    (0, "Cloning into 'sufyan-devops-eks-devsecops'...", "out"),
    (1, "./.github/workflows/ci.yaml          ./.github/workflows/deploy.yaml      # the pipeline", "ok"),
    (1, "./.github/CODEOWNERS                 ./.github/dependabot.yml             # reviews, updates", "out"),
    (2, "./terraform/main.tf  vpc.tf  eks.tf  ecr-and-github.tf  load-balancer-controller.tf  outputs.tf", "ok"),
    (2, "./terraform/policies/aws-load-balancer-controller-v3.5.0.json                # controller IAM policy", "out"),
    (3, "./k8s/deployment.yaml  service.yaml  ingress.yaml  networkpolicy.yaml  pdb.yaml  serviceaccount.yaml", "ok"),
    (4, "./app/Dockerfile  ./app/nginx/default.conf  ./app/nginx/security-headers.conf", "ok"),
    (4, "./app/src/App.jsx  App.test.jsx  profile.js     ./app/package.json", "out"),
    (5, "./scripts/teardown.sh  ./scripts/verify-teardown.sh  ./scripts/ci/install-tools.sh", "ok"),
    (5, "./.trivyignore.yaml   ./.gitignore   ./docs/   ./study/   ./README.md", "out"),
], "bash (recorded, excerpt)"), [
    S("Let us start where you would start: clone the repository. Before we run anything, I want you to understand what we are actually about to build."),
    S("The pipeline lives in two workflows: ci dot yaml with the security checks, and deploy dot yaml, which runs those checks first and then builds and deploys. CODEOWNERS and Dependabot handle reviews and updates.",
      tts="The pipeline lives in two workflows: C I dot yammel with the security checks, and deploy dot yammel, which runs those checks first and then builds and deploys. Code owners and Dependabot handle reviews and updates."),
    S("The terraform folder describes the whole AWS platform: the network, the cluster, the registry, the GitHub role, and the load balancer controller, with its official IAM policy pinned to version 3.5.0."),
    S("The k8s folder holds the Kubernetes manifests: deployment, service, ingress, network policies, disruption budget and service account."),
    S("The app folder holds the application, its Dockerfile, and the nginx configuration with the security headers.", tts="The app folder holds the application, its Dockerfile, and the engine x configuration with the security headers."),
    S("And the scripts folder holds the tool installer for CI, plus two scripts we will use at the very end: the teardown, and the verification that nothing was left behind. "
      "Dot trivyignore lists the security exceptions we accepted on purpose, each with a reason and an expiry date.",
      tts="And the scripts folder holds the tool installer for C I, plus two scripts we will use at the very end: the teardown, and the verification that nothing was left behind. "
          "Dot trivy ignore lists the security exceptions we accepted on purpose, each with a reason and an expiry date."),
])

# ---------------------------------------------------------------- 6. The application
PROFILE = """export const profile = {
  name: "Sufyan Ahmad Kamboh",
  role: "DevSecOps Engineer",
  bio: "DevOps Engineer | Expertise in AWS, VoIP Solutions, ...",
  tags: ["Docker", "Kubernetes", "Git", "Jenkins", "Ansible",
         "Terraform", "AWS", "Golang"],
  links: [
    { label: "Contact", href: "mailto:sufyanahmad1@gmail.com", primary: true },
    { label: "Portfolio", href: "https://www.linkedin.com/in/sufyanahmadkamboh/" },
  ],
};"""
scene("The application", "The app · React + Vite", "A deliberately small application",
      code("app/src/profile.js (excerpt)", PROFILE, "javascript", 20) + notes([
          (0, "Why so small?", "this workshop is about the platform"),
          (1, "Original: one HTML file", "rebuilt as React + Vite"),
          (2, "Why rebuild it", "a real build, tests and npm audit"),
          (3, "Version in the footer", "baked in by the pipeline"),
      ]), [
    S("The application is a profile card. It is intentionally simple. The goal of this project is not to teach React. The goal is to show a production style DevSecOps platform around an application."),
    S("The original profile card was a single HTML file. For this project it is rebuilt as a small React app with Vite.", tts="The original profile card was a single H T M L file. For this project it is rebuilt as a small React app with veet."),
    S("Why rebuild it? Because a real build step gives the pipeline real work: a dependency tree to audit, unit tests to run, and a production build to scan."),
    S("The page footer shows the version and git commit of the running build, which the pipeline bakes into the image. So you can always see exactly what is deployed."),
], layout="code")

scene(None, "Recorded · local checks", "Lint, test, audit and build, before any cloud", terminal([
    (0, "$ npm ci                     added packages · found 0 vulnerabilities", "cmd"),
    (0, "$ npm run lint               oxlint: no problems", "cmd"),
    (1, "$ npx vitest run --reporter=verbose", "cmd"),
    (1, " ✓ profile card > shows the name and role", "ok"),
    (1, " ✓ profile card > lists every skill", "ok"),
    (1, " ✓ profile card > opens external links safely in a new tab", "ok"),
    (1, " ✓ profile card > does not open mailto links in a new tab", "ok"),
    (1, " ✓ profile card > shows which build is running", "ok"),
    (1, "      Tests  5 passed (5)", "ok"),
    (2, "$ npm audit --audit-level=high", "cmd"),
    (2, "found 0 vulnerabilities", "ok"),
    (3, "$ npm run build", "cmd"),
    (3, "dist/index.html 0.57 kB · dist/assets/index-….css 1.59 kB · dist/assets/index-….js 221.36 kB   ✓ built in 418ms", "out"),
], "bash (recorded)"), [
    S("Before anything touches the cloud, the developer loop. npm ci installs exactly what the lock file says, and the linter finds no problems.",
      tts="Before anything touches the cloud, the developer loop. N P M C I installs exactly what the lock file says, and the linter finds no problems."),
    S("Five unit tests pass. One of them checks a security detail: external links open with no referrer and no opener, so the linked site cannot control our page."),
    S("npm audit with level high finds zero vulnerabilities. The pipeline runs exactly this command, and later we will see it fail on purpose.",
      tts="N P M audit with level high finds zero vulnerabilities. The pipeline runs exactly this command, and later we will see it fail on purpose."),
    S("And the production build is tiny: one HTML file, one CSS file and one JavaScript bundle. This is all that nginx will serve.",
      tts="And the production build is tiny: one H T M L file, one C S S file and one JavaScript bundle. This is all that engine x will serve."),
])

# ---------------------------------------------------------------- 7. Local environment
scene("Preparing the environment", "Recorded · tools and identity", "Check your tools, and check who you are", terminal([
    (0, "$ git --version              git version 2.54.0", "out"),
    (0, "$ terraform version          Terraform v1.15.6", "out"),
    (0, "$ aws --version              aws-cli/2.34.64", "out"),
    (0, "$ docker --version           Docker version 29.4.3", "out"),
    (0, "$ kubectl version --client   Client Version: v1.37.1", "out"),
    (0, "$ helm version --short       v4.2.1", "out"),
    (1, "$ aws sts get-caller-identity", "cmd"),
    (1, '{ "UserId": "AIDA…<redacted>", "Account": "<account-id>", "Arn": "arn:aws:iam::<account-id>:user/<redacted>" }', "out"),
    (2, "$ echo $AWS_REGION", "cmd"),
    (2, "AWS_REGION=eu-central-1  AWS_DEFAULT_REGION=eu-central-1", "ok"),
], "bash (recorded, redacted)"), [
    S("Now behave like a careful engineer: check your tools. Git, Terraform, the AWS CLI, Docker, kubectl version 1.37 to match the cluster, and Helm. kubectl only supports one minor version of difference from the cluster, so the version matters.",
      tts="Now behave like a careful engineer: check your tools. Git, Terraform, the A W S C L I, Docker, kube control version 1 point 37 to match the cluster, and Helm. Kube control only supports one minor version of difference from the cluster, so the version matters."),
    S("Then the most important command before any cloud work: aws sts get caller identity. It tells you which account and which identity you are about to change. I have redacted mine, but you should always read yours.",
      tts="Then the most important command before any cloud work: A W S S T S get caller identity. It tells you which account and which identity you are about to change. I have redacted mine, but you should always read yours."),
    S("And the region. Every command in this workshop is pinned to eu-central-1. I built this in a shared company account, so we work inside a controlled scope: one region, our own resources only. "
      "Terraform enforces that too, as you will see in a moment.",
      tts="And the region. Every command in this workshop is pinned to E U central 1. I built this in a shared company account, so we work inside a controlled scope: one region, our own resources only. "
          "Terraform enforces that too, as you will see in a moment."),
])

# ---------------------------------------------------------------- 8. Terraform walkthrough
TF_MAIN = """variable "region" {
  default = "eu-central-1"
  validation {
    condition     = var.region == "eu-central-1"
    error_message = "This project only runs in eu-central-1 (Frankfurt)."
  }
}

provider "aws" {
  region              = var.region
  allowed_account_ids = [var.allowed_account_id]   # TF_VAR_allowed_account_id
  default_tags {
    tags = { Project = "eks-devsecops", Owner = "sufyan", ManagedBy = "terraform" }
  }
}"""
scene("Terraform, file by file", "Terraform · guard rails", "Terraform is our source of truth",
      code("terraform/variables.tf + main.tf (excerpts)", TF_MAIN, "terraform", 21) + notes([
          (0, "One region only", "validation refuses anything else"),
          (1, "One account only", "allowed_account_ids"),
          (2, "Tags on everything", "Project=eks-devsecops, Owner=sufyan"),
          (3, "State: local + gitignored", "never commit it to a public repo"),
      ]), [
    S("Before running Terraform, let us read it. Terraform is our source of truth for this infrastructure. First, guard rails. The region variable has a validation: anything other than Frankfurt is refused.", hl=(1, 7)),
    S("The provider has allowed account IDs. I pass my account ID through an environment variable, and if my credentials ever pointed at a different account, Terraform would refuse to run.", hl=(9, 11)),
    S("Every resource gets default tags: project, owner, and managed by Terraform. At the end, we will use these tags to prove that nothing was left behind.", hl=(12, 14)),
    S("And the state. Terraform state is kept locally here and ignored by git, because it contains account IDs, resource details, sometimes even secrets. "
      "Never commit Terraform state to a public repository. For a team, you would put it in an S3 bucket with locking, which we discuss in part two.",
      tts="And the state. Terraform state is kept locally here and ignored by git, because it contains account I Ds, resource details, sometimes even secrets. "
          "Never commit Terraform state to a public repository. For a team, you would put it in an S 3 bucket with locking, which we discuss in part two."),
], layout="code")

VPC = """module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.7.3"
  cidr    = "10.42.0.0/16"
  azs     = slice(data.aws_availability_zones.available.names, 0, 2)

  private_subnets = ["10.42.0.0/20", "10.42.16.0/20"]   # nodes and pods
  public_subnets  = ["10.42.48.0/24", "10.42.49.0/24"]  # load balancer only

  enable_nat_gateway = true
  single_nat_gateway = true            # lab: one; production: one per AZ

  public_subnet_tags  = { "kubernetes.io/role/elb" = 1 }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = 1 }

  manage_default_security_group = true # default SG allows nothing
  enable_flow_log               = true # VPC flow logs to CloudWatch
}"""
scene(None, "Terraform · vpc.tf", "The network: private nodes, public load balancer",
      code("terraform/vpc.tf (excerpt)", VPC, "terraform", 21) + notes([
          (0, "2 availability zones", "survive a data-center failure"),
          (1, "Private vs public", "nodes and pods stay private"),
          (2, "NAT gateway", "outbound only"),
          (3, "Subnet tags", "where the ALB may go"),
          (4, "Locked down, logged", "default SG empty, flow logs"),
      ]), [
    S("The network uses the community VPC module, pinned to version 6.7.3. One address range, 10.42 dot 0 dot 0 slash 16, over two availability zones.", hl=(1, 5),
      tts="The network uses the community V P C module, pinned to version 6 point 7 point 3. One address range, ten dot forty two dot zero dot zero slash sixteen, over two availability zones."),
    S("Two large private subnets for the nodes and pods, and two small public subnets for the load balancer only.", hl=(7, 8)),
    S("One NAT gateway gives the private nodes outbound internet access. One is cheaper for a lab. In production you would use one per zone, so a zone failure does not cut off the other zone.", hl=(10, 11)),
    S("These tags tell the load balancer controller which subnets it may use for internet facing and internal load balancers.", hl=(13, 14)),
    S("And two security habits: the default security group allows nothing, and flow logs record every connection for investigations.", hl=(16, 17)),
], layout="code")

EKS = """module "eks" {
  source             = "terraform-aws-modules/eks/aws"
  version            = "21.26.0"
  kubernetes_version = "1.37"
  subnet_ids         = module.vpc.private_subnets
  enabled_log_types  = ["api", "audit", "authenticator"]
  encryption_config  = { resources = ["secrets"] }   # KMS
  enable_irsa        = false                         # Pod Identity instead
  authentication_mode = "API"                        # access entries
  access_entries = { github_deploy = {
    principal_arn = aws_iam_role.github_deploy.arn
    policy_associations = { app = {
      policy_arn   = ".../AmazonEKSEditPolicy"
      access_scope = { type = "namespace", namespaces = ["profile-card"] } } } } }
  addons = { vpc-cni = { enableNetworkPolicy = "true" }, eks-pod-identity-agent = {} }
  eks_managed_node_groups = { default = {
    instance_types   = ["t3.medium"]   # 2 nodes, max 3
    metadata_options = { http_tokens = "required", http_put_response_hop_limit = 1 }
    block_device_mappings = { xvda = { ebs = { encrypted = true } } } } }
}"""
scene(None, "Terraform · eks.tf", "The cluster, with security built in",
      code("terraform/eks.tf (simplified)", EKS, "terraform", 18) + notes([
          (0, "EKS 1.37, private subnets", "the newest standard-support version"),
          (1, "Audit logs + KMS", "who did what; secrets encrypted"),
          (2, "Access entries", "pipeline: one namespace only"),
          (3, "Network policy + Pod Identity", "add-ons"),
          (4, "IMDSv2 hop limit 1, encrypted disks", "nodes"),
      ]), [
    S("The cluster uses the community EKS module, version 21.26. Kubernetes 1.37, the newest version in standard support, placed in the private subnets.", hl=(1, 5),
      tts="The cluster uses the community E K S module, version 21 point 26. Kubernetes 1 point 37, the newest version in standard support, placed in the private subnets."),
    S("The control plane writes API, audit and authenticator logs, and Kubernetes secrets are encrypted with a KMS key. I switched off IRSA, because we use the newer Pod Identity, which needs no extra identity provider.", hl=(6, 8),
      tts="The control plane writes A P I, audit and authenticator logs, and Kubernetes secrets are encrypted with a K M S key. I switched off I R S A, because we use the newer pod identity, which needs no extra identity provider."),
    S("Access entries map AWS identities to Kubernetes permissions. Our GitHub deploy role gets the edit policy, but only inside the profile card namespace.", hl=(9, 14)),
    S("The VPC CNI add-on gets network policy enforcement switched on, and the Pod Identity agent is installed.", hl=(15, 15),
      tts="The V P C C N I add-on gets network policy enforcement switched on, and the pod identity agent is installed."),
    S("And the node group: t3 medium instances, instance metadata version two required, with a hop limit of one, and encrypted disks.", hl=(16, 19)),
], layout="code")

OIDC = """data "aws_iam_openid_connect_provider" "github" {
  count = var.create_github_oidc_provider ? 0 : 1   # default: read the shared one
  url   = "https://token.actions.githubusercontent.com"
}

resource "aws_ecr_repository" "app" {
  name                 = "eks-devsecops/profile-card"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
  force_delete         = true                      # clean teardown
}

resource "aws_eks_pod_identity_association" "lb_controller" {
  namespace       = "kube-system"
  service_account = "aws-load-balancer-controller"
  role_arn        = aws_iam_role.lb_controller.arn
}
resource "helm_release" "lb_controller" {
  chart   = "aws-load-balancer-controller"
  version = "3.5.0"
}"""
scene(None, "Terraform · ECR, OIDC, controller", "Registry, GitHub identity, load balancer controller",
      code("terraform/ecr-and-github.tf + load-balancer-controller.tf (excerpts)", OIDC, "terraform", 19) + notes([
          (0, "Shared OIDC provider", "read only, never modified"),
          (1, "ECR", "immutable tags, scan on push"),
          (2, "Pod Identity", "controller credentials without keys"),
          (3, "Helm, pinned", "chart 3.5.0"),
      ]), [
    S("This account already has a GitHub identity provider, shared by other teams. IAM is global, so Terraform only reads it with a data source. A switch exists for fresh accounts that have none, and it is off by default.", hl=(1, 4)),
    S("The container registry has immutable tags, so a tag can never be overwritten, and every pushed image is scanned. Force delete lets the teardown remove it completely.", hl=(6, 11)),
    S("The load balancer controller gets its AWS permissions through a Pod Identity association, for one service account in kube-system. No keys.", hl=(13, 17),
      tts="The load balancer controller gets its AWS permissions through a pod identity association, for one service account in kube system. No keys."),
    S("And Terraform installs the controller itself with Helm, chart version 3.5.0. So one terraform apply gives us a cluster that is ready for an Ingress.", hl=(18, 21)),
], layout="code")

# ---------------------------------------------------------------- 9. AWS before
scene("Inspecting AWS first", "Recorded · before we create anything", "Look before you apply", terminal([
    (0, "$ inventory of eu-central-1", "cmd"),
    (0, "VPCs:             1  (default VPC only)", "out"),
    (0, "EC2 instances:    0", "out"),
    (0, "Load balancers:   0", "out"),
    (0, "EKS clusters:     0", "out"),
    (0, "NAT gateways:     0", "out"),
    (0, "ECR repositories: 0", "out"),
    (1, "GitHub OIDC provider (shared, IAM is global): 1 existing", "warn"),
], "bash (recorded)"), [
    S("Before we create anything, let us look at the account. In Frankfurt there is only the default VPC. No instances, no load balancers, no clusters, no NAT gateways, no registries. "
      "This is the baseline. At the very end we compare against it, so we can prove we left the account exactly as we found it.",
      tts="Before we create anything, let us look at the account. In Frankfurt there is only the default V P C. No instances, no load balancers, no clusters, no NAT gateways, no registries. "
          "This is the baseline. At the very end we compare against it, so we can prove we left the account exactly as we found it."),
    S("And one important existing thing: a GitHub identity provider. It belongs to the whole account, because IAM is global. Other pipelines may depend on it. We will reuse it, read only. We will not modify it, and we will not delete it.",
      tts="And one important existing thing: a GitHub identity provider. It belongs to the whole account, because I A M is global. Other pipelines may depend on it. We will reuse it, read only. We will not modify it, and we will not delete it."),
])

# ---------------------------------------------------------------- 10. init / validate / plan
scene("Terraform plan", "Recorded · a real Windows pitfall", "terraform init failed. Here is why.", terminal([
    (0, "$ terraform init", "cmd"),
    (0, "Downloading registry.terraform.io/terraform-aws-modules/eks/aws 21.26.0 for eks...", "out"),
    (0, "fatal: cannot write keep file '…/.terraform/modules/eks/.git/objects/pack/pack-1633…keep': Filename too long", "bad"),
    (1, "# Windows limits paths to 260 characters; my working folder path was very long", "dim"),
    (1, "# fix: clone into a short folder (or: git config core.longpaths true)", "dim"),
    (2, "$ terraform init      # from a short path", "cmd"),
    (2, "Downloading … vpc/aws 6.7.3 · eks/aws 21.26.0 · kms/aws 4.0.0", "out"),
    (2, "- Installing hashicorp/aws v6.67.0 · helm v3.3.0 · kubernetes v3.3.0 …", "out"),
    (2, "Terraform has been successfully initialized!", "ok"),
    (3, "$ terraform validate", "cmd"),
    (3, "Success! The configuration is valid.", "ok"),
], "bash (recorded, excerpt)"), [
    S("terraform init downloads the providers and modules. And on my first try it failed, which is worth showing you. On Windows, Terraform downloads modules with git, and git hit the 260 character path limit: filename too long.",
      tts="Terraform init downloads the providers and modules. And on my first try it failed, which is worth showing you. On Windows, Terraform downloads modules with git, and git hit the 260 character path limit: file name too long."),
    S("My working folder simply had a very long path. The fix is to work from a short folder, or to enable long paths in git."),
    S("From a short folder, init works: the VPC, EKS and KMS modules, and the AWS, Helm and Kubernetes providers, all at pinned versions.",
      tts="From a short folder, init works: the V P C, E K S and K M S modules, and the A W S, Helm and Kubernetes providers, all at pinned versions."),
    S("terraform validate checks the configuration itself. Valid.", tts="Terraform validate checks the configuration itself. Valid."),
])

scene(None, "Recorded · terraform plan", "Read the plan before you apply", terminal([
    (0, "$ terraform plan -out=tfplan", "cmd"),
    (0, "  # module.vpc.aws_vpc.this[0] will be created", "out"),
    (0, "  # module.vpc.aws_subnet.private[0..1], aws_subnet.public[0..1] will be created", "out"),
    (0, "  # module.vpc.aws_nat_gateway.this[0] will be created", "out"),
    (1, "  # module.eks.aws_eks_cluster.this[0] will be created", "out"),
    (1, "  # module.eks.module.eks_managed_node_group[\"default\"].aws_eks_node_group.this[0] will be created", "out"),
    (1, "  # module.eks.module.kms.aws_kms_key.this[0] will be created", "out"),
    (2, "  # aws_iam_role.github_deploy · aws_iam_role.lb_controller · module.eks.aws_iam_role.this[0] will be created", "out"),
    (2, "  # aws_ecr_repository.app · module.eks.aws_cloudwatch_log_group.this[0] · module.vpc.aws_flow_log.this[0]", "out"),
    (2, "  # helm_release.lb_controller · kubernetes_namespace_v1.app will be created", "out"),
    (3, "Plan: 72 to add, 0 to change, 0 to destroy.", "ok"),
], "terraform (recorded, excerpt)"), [
    S("Now the plan. I am not going to blindly run apply. First I want to see exactly what Terraform wants to create. The network: the VPC, four subnets, the NAT gateway.",
      tts="Now the plan. I am not going to blindly run apply. First I want to see exactly what Terraform wants to create. The network: the V P C, four subnets, the NAT gateway."),
    S("The cluster, the node group, and the KMS key.", tts="The cluster, the node group, and the K M S key."),
    S("IAM roles: for the GitHub deploy pipeline, for the load balancer controller, and for the cluster. The registry, the log groups and the flow log. And inside Kubernetes, the controller and our namespace.",
      tts="I A M roles: for the GitHub deploy pipeline, for the load balancer controller, and for the cluster. The registry, the log groups and the flow log. And inside Kubernetes, the controller and our namespace."),
    S("And the most important line: seventy two to add, zero to change, zero to destroy. In a shared account, zero to change and zero to destroy is your proof that you will not touch anything that belongs to someone else."),
])

scene("Building it on AWS", "Recorded · terraform apply", "72 resources in 12 minutes", terminal([
    (0, "$ terraform apply tfplan", "cmd"),
    (0, "aws_ecr_repository.app: Creation complete after 0s", "out"),
    (0, "module.vpc.aws_vpc.this[0]: Creation complete after 1s", "out"),
    (1, "module.eks.module.kms.aws_kms_key.this[0]: Creation complete after 29s", "out"),
    (1, "module.vpc.aws_nat_gateway.this[0]: Creation complete after 1m54s", "out"),
    (2, "module.eks.aws_eks_cluster.this[0]: Creation complete after 8m21s", "warn"),
    (2, "module.eks.module.eks_managed_node_group[\"default\"]...: Creation complete after 1m47s", "out"),
    (3, "kubernetes_namespace_v1.app: Creation complete after 2s", "out"),
    (3, "helm_release.lb_controller: Creation complete after 22s", "out"),
    (4, "Apply complete! Resources: 72 added, 0 changed, 0 destroyed.        # 12 min 5 s", "ok"),
], "terraform (recorded, excerpt)"), [
    S("Now we apply exactly that saved plan. The registry and the VPC take a second each.", tts="Now we apply exactly that saved plan. The registry and the V P C take a second each."),
    S("The KMS key takes half a minute, and the NAT gateway almost two minutes.", tts="The K M S key takes half a minute, and the NAT gateway almost two minutes."),
    S("The EKS control plane is the slow part: eight minutes and twenty one seconds. Then the two worker nodes join in under two minutes.",
      tts="The E K S control plane is the slow part: eight minutes and twenty one seconds. Then the two worker nodes join in under two minutes."),
    S("Then Terraform reaches inside the new cluster: it creates our namespace and installs the load balancer controller with Helm."),
    S("Seventy two resources, in twelve minutes. Now let us go into AWS and verify that Terraform created what we expected."),
])

# ---------------------------------------------------------------- 11. Console verification
scene("Verifying in the AWS Console", "AWS Console · VPC (recorded)", "The VPC and its resource map", shot(0, "c01-vpc.png", "VPC details and resource map"), [
    S("This is the AWS console, through a read only session. Our VPC, eks devsecops, with the address range 10.42 dot 0 dot 0 slash 16. I have redacted the account number.",
      tts="This is the AWS console, through a read only session. Our V P C, E K S dev sec ops, with the address range ten dot forty two dot zero dot zero slash sixteen. I have redacted the account number."),
    S("The resource map shows the design we read in Terraform: in each of the two zones, one public and one private subnet, and the route tables connecting them."),
])

scene(None, "AWS Console · subnets and NAT (recorded)", "Why private nodes need a NAT gateway",
      shot(0, "c02-subnets.png", "Subnets", "height:620px;width:auto"), [
    S("The four subnets: public 48 and 49, private 0 and 16, all available.", tts="The four subnets: public forty eight and forty nine, private zero and sixteen, all available."),
    S("Notice the nodes are in private subnets. Let me explain why. A node without a public IP cannot be reached from the internet at all, so a whole class of attacks simply does not apply. "
      "But the nodes still need to reach out, to pull images and to talk to AWS. That is the job of the NAT gateway: outbound only."),
])

scene(None, "AWS Console · EKS (recorded)", "The cluster: active, version 1.37", shot(0, "c04-eks-overview.png", "EKS cluster overview"), [
    S("The EKS cluster: active, Kubernetes 1.37, standard support until December 2027, and zero health issues.",
      tts="The E K S cluster: active, Kubernetes 1 point 37, standard support until December 2027, and zero health issues."),
    S("In the details you can see the API server endpoint and the cluster IAM role. Every A R N here contains the account number, which you see redacted.",
      tts="In the details you can see the A P I server endpoint and the cluster I A M role. Every A R N here contains the account number, which you see redacted."),
])

scene(None, "AWS Console · EKS access (recorded)", "Who can do what in the cluster", shot(0, "c06-eks-access.png", "EKS access entries"), [
    S("The access tab. Authentication mode: EKS API. That means access entries, not the old config map.", tts="The access tab. Authentication mode: E K S A P I. That means access entries, not the old config map."),
    S("Four entries: the EKS service role, the node role, my admin user from Terraform, and our GitHub deploy role with only the edit policy. "
      "On the command line we can see the scope: the deploy role's edit policy applies to one namespace, profile card. Nothing else in the cluster.",
      tts="Four entries: the E K S service role, the node role, my admin user from Terraform, and our GitHub deploy role with only the edit policy. "
          "On the command line we can see the scope: the deploy role's edit policy applies to one namespace, profile card. Nothing else in the cluster."),
])

scene(None, "AWS Console · node group (recorded)", "Nodes: private, IMDSv2, encrypted",
      shot(0, "c09-nodegroup.png", "Node group", "height:520px;width:auto")
      + '<div class="st" data-s="1" style="margin-top:14px;width:1500px">'
      + terminal([(1, "$ aws ec2 describe-launch-template-versions … MetadataOptions, RootVolume", "cmd"),
                  (1, "HttpTokens: required    HttpPutResponseHopLimit: 1    Encrypted: true    VolumeType: gp3    VolumeSize: 20", "ok")], "bash (recorded)")
      + "</div>", [
    S("The node group: two t3 medium nodes, Amazon Linux 2023, minimum two, maximum three, in our two private subnets. "
      "And look at the blue banner: my console identity has no access to Kubernetes objects. That is correct. A read only AWS identity without an access entry sees nothing inside the cluster.",
      tts="The node group: two t3 medium nodes, Amazon Linux 2023, minimum two, maximum three, in our two private subnets. "
          "And look at the blue banner: my console identity has no access to Kubernetes objects. That is correct. A read only A W S identity without an access entry sees nothing inside the cluster."),
    S("The launch template confirms the security settings: instance metadata tokens required, a hop limit of one, and an encrypted 20 gigabyte gp3 disk.",
      tts="The launch template confirms the security settings: instance metadata tokens required, a hop limit of one, and an encrypted twenty gigabyte G P 3 disk."),
])

scene(None, "AWS Console · EC2 (recorded)", "Two instances, no public IP", shot(0, "c13-ec2.png", "EC2 instances"), [
    S("In EC2 you can see the two running nodes, one in eu-central-1a and one in 1b. The public IPv4 column is empty. No node is reachable from the internet.",
      tts="In E C 2 you can see the two running nodes, one in E U central 1 A and one in 1 B. The public I P version 4 column is empty. No node is reachable from the internet."),
])

scene(None, "AWS Console · KMS, ECR, CloudWatch (recorded)", "Encryption, registry, logs", grid([
    card(0, "🔐", "KMS key: Enabled, customer managed", "alias eks/eks-devsecops · automatic rotation: true", "violet"),
    card(1, "📦", "ECR: eks-devsecops/profile-card", "tag immutability: IMMUTABLE · scan on push: true · AES-256", "blue"),
    card(2, "📈", "CloudWatch log groups", "/aws/eks/eks-devsecops/cluster · /aws/vpc-flow-log/… · retention 7 days", "blue"),
], cols=3, gap=20) + f'<div style="display:flex;gap:24px;margin-top:24px">{shot(0, "c10-kms.png", "KMS key", "height:420px;width:auto")}'
      f'{shot(1, "c11-ecr.png", "ECR", "height:420px;width:auto")}</div>', [
    S("The KMS key: customer managed, enabled, with automatic rotation. Why a customer managed key? Because you control its policy and you can audit every use of it. If a Kubernetes secret is ever read from etcd storage directly, it is encrypted.",
      tts="The K M S key: customer managed, enabled, with automatic rotation. Why a customer managed key? Because you control its policy and you can audit every use of it. If a Kubernetes secret is ever read from the cluster's storage directly, it is encrypted."),
    S("The container registry: tag immutability on, scan on push on. Nobody can silently replace an image behind an existing tag.",
      tts="The container registry: tag immutability on, scan on push on. Nobody can silently replace an image behind an existing tag."),
    S("And CloudWatch holds two log groups: the cluster's control plane logs, and the VPC flow logs, both kept for seven days. In an incident, these are the first places you look.",
      tts="And CloudWatch holds two log groups: the cluster's control plane logs, and the V P C flow logs, both kept for seven days. In an incident, these are the first places you look."),
])

# ---------------------------------------------------------------- 12. EKS security summary
scene("EKS security, explained", "Senior-level summary", "Six decisions that make this cluster safer", grid([
    card(0, "🔒", "Private nodes", "no public IP: a whole class of attacks does not apply"),
    card(1, "🪪", "IMDSv2, hop limit 1", "a compromised pod cannot reach the node's AWS credentials"),
    card(2, "💽", "Encrypted disks", "a lost or copied volume reveals nothing"),
    card(3, "🔐", "KMS for secrets", "envelope encryption with a key you control and audit"),
    card(4, "🎫", "Access entries", "every identity mapped explicitly; the pipeline gets one namespace"),
    card(5, "🧩", "Pod Identity", "AWS permissions for pods without any stored keys"),
], cols=3), [
    S("Let me summarise the cluster security at a senior level. Private nodes: no public IP, so nothing on the internet can even try to connect."),
    S("IMDS version two with a hop limit of one: every node has AWS credentials in its instance metadata. The hop limit means a container cannot reach them, so a compromised pod cannot become a compromised AWS account.",
      tts="I M D S version two with a hop limit of one: every node has A W S credentials in its instance metadata. The hop limit means a container cannot reach them, so a compromised pod cannot become a compromised A W S account."),
    S("Encrypted disks: if a volume snapshot is ever copied, it reveals nothing."),
    S("KMS envelope encryption of Kubernetes secrets, with a key you control and can audit.", tts="K M S envelope encryption of Kubernetes secrets, with a key you control and can audit."),
    S("Access entries: every identity that can use the cluster is listed explicitly, and the pipeline only gets one namespace."),
    S("And Pod Identity: when a pod needs AWS permissions, like the load balancer controller, it gets them from EKS. We never put AWS access keys inside the Kubernetes cluster.",
      tts="And pod identity: when a pod needs A W S permissions, like the load balancer controller, it gets them from E K S. We never put A W S access keys inside the Kubernetes cluster."),
])

# ---------------------------------------------------------------- 13. Load balancer controller
scene("The AWS Load Balancer Controller", "Recorded · installed by Terraform with Helm", "Ingress in, Application Load Balancer out", terminal([
    (0, "$ helm list -A", "cmd"),
    (0, "aws-load-balancer-controller   kube-system   1   deployed   aws-load-balancer-controller-3.5.0   v3.5.0", "ok"),
    (1, "$ kubectl -n kube-system get deploy,pods -l app.kubernetes.io/name=aws-load-balancer-controller", "cmd"),
    (1, "deployment.apps/aws-load-balancer-controller   2/2   2   2", "ok"),
    (1, "pod/aws-load-balancer-controller-…-d7ttk   1/1   Running        pod/…-ms5bv   1/1   Running", "out"),
    (2, "$ aws eks list-pod-identity-associations --cluster-name eks-devsecops", "cmd"),
    (2, "|  kube-system  |  aws-load-balancer-controller  |", "ok"),
    (3, "$ kubectl get nodes -o wide", "cmd"),
    (3, "ip-10-42-22-252…  Ready  v1.37.0-eks-3b4a6ca  10.42.22.252  EXTERNAL-IP <none>", "ok"),
    (3, "ip-10-42-7-30…    Ready  v1.37.0-eks-3b4a6ca  10.42.7.30    EXTERNAL-IP <none>", "ok"),
], "bash (recorded)"), [
    S("Now the load balancer controller. What does it do? It watches Kubernetes Ingress objects, and for each one it creates and manages a real AWS Application Load Balancer, with listeners, target groups and security groups. "
      "Terraform installed it with Helm: chart and app version 3.5.0, deployed."),
    S("It runs as two replicas in kube-system, both running.", tts="It runs as two replicas in kube system, both running."),
    S("And how does it get AWS permissions to create load balancers? A Pod Identity association: its service account is linked to an IAM role. EKS hands the pod temporary credentials. There is no access key anywhere.",
      tts="And how does it get AWS permissions to create load balancers? A pod identity association: its service account is linked to an I A M role. E K S hands the pod temporary credentials. There is no access key anywhere."),
    S("And the nodes: two, ready, Kubernetes 1.37, and no external IP. The platform is ready for our application.",
      tts="And the nodes: two, ready, Kubernetes 1 point 37, and no external I P. The platform is ready for our application."),
])

# ---------------------------------------------------------------- 14. Kubernetes manifests
DEPLOY = """spec:
  replicas: 2
  strategy: {rollingUpdate: {maxUnavailable: 0, maxSurge: 1}}
  template:
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10101
        seccompProfile: {type: RuntimeDefault}
      containers:
        - name: web
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: {drop: [ALL]}
          resources:
            requests: {cpu: 50m, memory: 32Mi}
            limits:   {cpu: 200m, memory: 64Mi}
          readinessProbe: {httpGet: {path: /healthz, port: http}}
          livenessProbe:  {httpGet: {path: /healthz, port: http}}
          lifecycle: {preStop: {sleep: {seconds: 15}}}"""
scene("The Kubernetes manifests", "k8s/deployment.yaml", "The Deployment, line by line",
      code("k8s/deployment.yaml (excerpt)", DEPLOY, "yaml", 19) + notes([
          (0, "2 replicas, zero downtime", "old pods stay until new ones are ready"),
          (1, "No token, non-root, seccomp", "the pod's identity"),
          (2, "Read-only, no capabilities", "the container"),
          (3, "Requests + limits", "fair share, no runaway"),
          (4, "Probes + preStop", "traffic only to healthy pods"),
      ]), [
    S("Now the application manifests. Two replicas, and a rolling update with max unavailable zero: an old pod is only removed after a new one is ready.", hl=(1, 3)),
    S("No service account token, because the app never calls the Kubernetes API. It runs as user 10101, never root, with the default seccomp profile blocking dangerous system calls.", hl=(6, 10)),
    S("The container cannot escalate privileges, its root file system is read only, and every Linux capability is dropped.", hl=(13, 16)),
    S("Resource requests reserve what it needs, and limits stop it from starving its neighbours.", hl=(17, 19)),
    S("Readiness and liveness probes on the healthz endpoint, so traffic only reaches pods that are ready. And a fifteen second pause before stopping, so the load balancer can drain a pod before it disappears.", hl=(20, 22)),
], layout="code")

NETPOL = """# networkpolicy.yaml: default deny, then one exception
kind: NetworkPolicy
metadata: {name: default-deny}
spec: {podSelector: {}, policyTypes: [Ingress, Egress]}
---
kind: NetworkPolicy
metadata: {name: allow-http-from-load-balancer}
spec:
  ingress:
    - from: [{ipBlock: {cidr: 10.42.48.0/23}}]   # ALB subnets only
      ports: [{protocol: TCP, port: 8080}]
---
# pdb.yaml
kind: PodDisruptionBudget
spec: {minAvailable: 1}
---
# ingress.yaml (annotations)
alb.ingress.kubernetes.io/scheme: internet-facing
alb.ingress.kubernetes.io/target-type: ip
alb.ingress.kubernetes.io/healthcheck-path: /healthz"""
scene(None, "NetworkPolicy · PDB · Ingress", "Who may talk to the pods",
      code("k8s/networkpolicy.yaml, pdb.yaml, ingress.yaml (excerpts)", NETPOL, "yaml", 19) + notes([
          (0, "Default deny", "nothing in, nothing out"),
          (1, "One exception", "port 8080 from the ALB subnets"),
          (2, "Disruption budget", "node maintenance never takes it down"),
          (3, "Ingress", "internet-facing ALB, straight to pods"),
          (4, "Namespace", "Pod Security restricted (Terraform)"),
      ]), [
    S("Network policies. First a default deny: no traffic in and no traffic out for every pod in the namespace.", hl=(1, 4)),
    S("Then exactly one exception: TCP port 8080, and only from the load balancer subnets. Not from the whole VPC, because on EKS, pod addresses come from the VPC range, and that would let every other pod in the cluster in. I learned that the hard way in my previous build.",
      tts="Then exactly one exception: T C P port 8080, and only from the load balancer subnets. Not from the whole V P C, because on E K S, pod addresses come from the V P C range, and that would let every other pod in the cluster in. I learned that the hard way in my previous build.", hl=(6, 11)),
    S("A pod disruption budget keeps at least one pod running during node maintenance.", hl=(13, 15)),
    S("The Ingress asks for an internet facing Application Load Balancer that sends traffic straight to pod IPs, and checks their health on healthz.", hl=(17, 20)),
    S("And the namespace itself, created by Terraform, enforces the Kubernetes Pod Security standard called restricted. Pods that do not follow these rules are refused at the door."),
], layout="code")

scene("Works vs. runs securely", "Recorded · inside the running pod", "\"It works\" is not the same as \"it runs securely\"", terminal([
    (0, "$ kubectl -n profile-card exec <pod> -- id", "cmd"),
    (0, "uid=10101 gid=10101 groups=10101", "ok"),
    (1, "$ kubectl -n profile-card exec <pod> -- touch /usr/share/nginx/html/hacked", "cmd"),
    (1, "touch: /usr/share/nginx/html/hacked: Read-only file system", "ok"),
    (1, "write to /tmp (emptyDir): ok", "out"),
    (2, "$ kubectl -n profile-card exec <pod> -- grep Cap /proc/1/status", "cmd"),
    (2, "CapPrm: 0000000000000000    CapEff: 0000000000000000", "ok"),
    (3, "$ kubectl -n profile-card exec <pod> -- wget http://example.com", "cmd"),
    (3, "wget: bad address 'example.com'          # default-deny egress: not even DNS", "ok"),
    (4, "$ kubectl -n profile-card run attacker --image=busybox --privileged", "cmd"),
    (4, "Error from server (Forbidden): violates PodSecurity \"restricted:latest\": privileged, allowPrivilegeEscalation …", "ok"),
], "bash (recorded)"), [
    S("Here is the difference between the application works, and the application is running securely. Inside a running pod, the process runs as user 10101. Not root.", tts="Here is the difference between the application works, and the application is running securely. Inside a running pod, the process runs as user ten one zero one. Not root."),
    S("If an attacker gets in, they cannot change the website files: read only file system. Only a small temporary folder is writable."),
    S("The process has zero Linux capabilities. Both the permitted and the effective sets are empty."),
    S("It cannot call out to the internet, not even resolve a name, so an attacker cannot download tools or send data out."),
    S("And nobody can start a privileged container in this namespace. Pod Security refuses it. A container that only works when it runs as privileged root is a problem waiting to happen in production."),
])

# ---------------------------------------------------------------- 15. Build, scan, SBOM, signing
scene("Build, scan, SBOM, sign", "Recorded · local build", "Build the image and scan it", terminal([
    (0, "$ docker build -t profile-card:workshop --build-arg VERSION=1.0.0 --build-arg COMMIT=$(git rev-parse HEAD) app", "cmd"),
    (0, "#16 [build 8/8] RUN npm run build                      DONE 1.2s", "out"),
    (0, "#18 [stage-1 2/5] RUN apk upgrade --no-cache", "out"),
    (0, "#20 [stage-1 5/5] COPY --from=build /app/dist /usr/share/nginx/html", "out"),
    (1, "$ trivy image --severity CRITICAL,HIGH --ignore-unfixed --exit-code 1 profile-card:workshop", "cmd"),
    (1, "profile-card:workshop (alpine 3.24.2)   alpine   Vulnerabilities: 0", "ok"),
    (1, "# exit 0 · the gate passes", "dim"),
], "bash (recorded)"), [
    S("Now the container. The Dockerfile has two stages: Node builds the static files, and the final image only contains nginx and those files. Notice the apk upgrade step. "
      "In my first build, Trivy blocked the official base image because of a high severity bug in a library called pcre2 that already had a fix. Upgrading the Alpine packages fixed it.",
      tts="Now the container. The Dockerfile has two stages: Node builds the static files, and the final image only contains engine x and those files. Notice the A P K upgrade step. "
          "In my first build, Trivy blocked the official base image because of a high severity bug in a library called P C R E 2 that already had a fix. Upgrading the Alpine packages fixed it."),
    S("Trivy scans the operating system packages and the application dependencies inside the image, against public vulnerability databases. Critical or high with a fix available means exit code one, and the pipeline stops. "
      "Here: zero. But remember, scanning only finds known problems. That is why it is one layer among many, not the whole defence."),
])

scene(None, "Recorded · SBOM with Syft", "An SBOM tells us what is inside", terminal([
    (0, "$ syft scan docker:profile-card:workshop -o table", "cmd"),
    (0, "NAME                       VERSION           TYPE", "out"),
    (0, "curl / libcurl             8.22.0-r0         apk", "out"),
    (0, "musl                       1.2.6-r2          apk", "out"),
    (0, "nginx                      1.30.5-r1         apk", "out"),
    (0, "pcre2                      10.49-r0          apk        # the fixed version", "ok"),
    (0, "zlib                       1.3.2-r0          apk", "out"),
    (1, "… 70 packages in total", "out"),
    (1, "$ syft scan … -o cyclonedx-json=sbom.cdx.json      # CycloneDX 1.7", "cmd"),
], "bash (recorded, excerpt)"), [
    S("An SBOM tells us what components exist inside our image. Syft lists every package: curl, musl, nginx, zlib, and pcre2 version 10.49, the fixed version from that story.",
      tts="An S-bom tells us what components exist inside our image. Sift lists every package: curl, muscle, engine x, zlib, and P C R E 2 version 10 point 49, the fixed version from that story."),
    S("Seventy packages in total, written as a CycloneDX document. The day a new vulnerability is announced, you search your SBOMs and know in seconds whether you are affected.",
      tts="Seventy packages in total, written as a Cyclone D X document. The day a new vulnerability is announced, you search your S-boms and know in seconds whether you are affected."),
])

scene(None, "Signing with cosign", "Why we sign images", grid([
    card(0, "✍️", "What signing means", "a cryptographic statement: this exact digest was built by this pipeline", "amber"),
    card(1, "🪪", "Keyless signing", "the GitHub job's identity gets a short-lived certificate from Sigstore; no signing key to steal", "amber"),
    card(1, "📒", "Public transparency log", "every signature is recorded in Rekor, so it can be audited", "amber"),
    card(2, "🏁", "Where it happens", "inside the deploy job, right after the push to ECR, then verified", "blue"),
    card(3, "🔭", "The next step", "enforce it: a cluster that only runs signed images (my previous project)", "ok"),
], cols=2), [
    S("And the last piece before the registry: signing. Signing means a cryptographic statement: this exact image digest was built by this pipeline. Image provenance, in one word."),
    S("We use cosign in keyless mode. The GitHub job proves its identity, gets a certificate valid for a few minutes, and signs. There is no long lived signing key that could be stolen, and every signature is written to a public transparency log.",
      tts="We use co-sign in keyless mode. The GitHub job proves its identity, gets a certificate valid for a few minutes, and signs. There is no long lived signing key that could be stolen, and every signature is written to a public transparency log."),
    S("That is why signing happens inside the pipeline, not on my laptop: the identity being signed is the pipeline itself. You will see it run in part two."),
    S("And the honest next step: in this project the cluster does not yet refuse unsigned images. My previous project shows exactly that, with Kyverno. That is where signing turns from evidence into enforcement.",
      tts="And the honest next step: in this project the cluster does not yet refuse unsigned images. My previous project shows exactly that, with Kai-verno. That is where signing turns from evidence into enforcement."),
])

scene("End of part 1", "Part 1 complete", "The platform is ready", grid([
    card(0, "🌐", "VPC", "2 zones, private nodes, NAT, flow logs", "ok"),
    card(0, "☸️", "EKS 1.37", "KMS, audit logs, access entries, IMDSv2", "ok"),
    card(0, "⚖️", "Load Balancer Controller", "Pod Identity, no keys", "ok"),
    card(0, "🔒", "Restricted workload", "non-root, read-only, no capabilities", "ok"),
    card(1, "▶️", "Part 2", "OIDC, the real pipeline, a failing security check, troubleshooting, teardown", "amber"),
], cols=2), [
    S("That is part one. We have a VPC across two zones with private nodes, an EKS cluster with encryption, audit logs and access entries, the load balancer controller without any keys, and a workload that runs restricted. "
      "And we verified all of it, on the command line and in the AWS console.",
      tts="That is part one. We have a V P C across two zones with private nodes, an E K S cluster with encryption, audit logs and access entries, the load balancer controller without any keys, and a workload that runs restricted. "
          "And we verified all of it, on the command line and in the AWS console."),
    S("In part two, we connect GitHub through OIDC, push code through the real pipeline, watch a security check fail on purpose, troubleshoot a broken rollout, and then destroy everything and prove it. See you there.",
      tts="In part two, we connect GitHub through O I D C, push code through the real pipeline, watch a security check fail on purpose, troubleshoot a broken rollout, and then destroy everything and prove it. See you there."),
])
