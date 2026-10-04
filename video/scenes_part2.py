"""Workshop video, part 2: ship it, break it, troubleshoot it, tear it down.

Recorded on 2026-10-04 on a real AWS account (eu-central-1), from the same session as part 1: GitHub Actions runs
37167564754 (first deploy), the failing npm audit run, the fix, the readiness-probe incident, the verified teardown.
Terminal output is redacted by redact.py; console and GitHub screenshots passed an in-page redaction and an OCR check.
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
scene("Where we are", "Workshop · part 2 of 2", "Ship it. Break it. Fix it. Delete it.", grid([
    card(0, "✅", "Part 1", "VPC, EKS, load balancer controller, restricted workload: built and verified", "ok"),
    card(1, "🪪", "OIDC", "GitHub gets temporary AWS credentials", "blue"),
    card(1, "🚀", "The real pipeline", "a push goes live in under 5 minutes", "blue"),
    card(2, "❌", "A failing security check", "a vulnerable dependency, stopped before production", "bad"),
    card(2, "🔧", "A broken rollout", "troubleshooting, layer by layer", "bad"),
    card(3, "🧹", "Teardown + proof", "delete everything, then verify it", "amber"),
], cols=2), [
    S("Welcome to part two. In part one we built and verified the platform: the network, the cluster, the load balancer controller, and a restricted workload."),
    S("Now we connect GitHub to AWS without any stored keys, and push real code through the pipeline. It goes live in under five minutes."),
    S("Then we break things on purpose. A vulnerable dependency that the pipeline must stop, and a broken deployment that we troubleshoot, layer by layer, like you would at work."),
    S("And at the end, we delete everything, and prove that nothing is left behind. Let us go."),
])

# ---------------------------------------------------------------- 2. OIDC
scene("GitHub OIDC: no stored keys", "Why not just store an access key?", "Two secrets you will never see in this repository", svg(
    box(0, 0, 20, 820, 260, "🚫", "Not in GitHub", ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "long-lived, copyable, valid until someone rotates them"], "bad", "#2a1520")
    + box(1, 900, 20, 820, 260, "✅", "Instead: OIDC", ["GitHub signs a token for each job", "AWS checks it and returns temporary credentials", "valid for one job, then useless"], "ok", "#0f2a22")
    + box(2, 0, 340, 330, 130, "⚙️", "GitHub Actions", ["sends a signed OIDC token"], "blue")
    + arrow(2, 335, 405, 395, 405)
    + box(2, 400, 340, 330, 130, "🔎", "AWS STS", ["checks it, returns a role"], "violet")
    + arrow(3, 735, 405, 795, 405)
    + box(3, 800, 340, 400, 130, "🪪", "Deploy role", ["eks-devsecops-github-deploy"], "amber", "#2b2410")
    + arrow(4, 1205, 405, 1265, 405)
    + box(4, 1270, 340, 450, 130, "☸️", "ECR + EKS", ["one repository, one namespace"], "ok", "#0f2a22")
    + label(4, 860, 560, "\"The workflow receives temporary credentials. No long-lived AWS secret sits inside GitHub.\"", 28, "sky", "middle", 800)
), [
    S("This is an important DevSecOps section. The usual way to let a pipeline into AWS is to store two secrets in GitHub: an access key ID and a secret access key. "
      "They are long lived, they can be copied, and they stay valid until someone remembers to rotate them. We do not store either of them.",
      tts="This is an important dev sec ops section. The usual way to let a pipeline into AWS is to store two secrets in GitHub: an access key I D and a secret access key. "
          "They are long lived, they can be copied, and they stay valid until someone remembers to rotate them. We do not store either of them."),
    S("Instead, OIDC. For every job, GitHub signs a short token that says which repository, which branch and which environment is running. AWS checks that token and returns temporary credentials, valid for that job only.",
      tts="Instead, O I D C. For every job, GitHub signs a short token that says which repository, which branch and which environment is running. AWS checks that token and returns temporary credentials, valid for that job only."),
    S("The flow: the GitHub Actions job sends its token to AWS STS.", tts="The flow: the GitHub Actions job sends its token to A W S S T S."),
    S("If the token matches the role's trust policy, the job gets temporary credentials for the eks devsecops github deploy role.", tts="If the token matches the role's trust policy, the job gets temporary credentials for the E K S dev sec ops github deploy role."),
    S("And that role can do very little: push to one container repository, and deploy into one Kubernetes namespace. The workflow receives temporary credentials. We do not have long lived AWS secrets sitting inside GitHub."),
])

TRUST = """{
  "Effect": "Allow",
  "Principal": {
    "Federated": "arn:aws:iam::<account-id>:oidc-provider/token.actions.githubusercontent.com"
  },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub":
  "repo:sufyanahmadkamboh@25397028/sufyan-devops-eks-devsecops@1403679100:environment:production"
    }
  }
}
// permissions (inline policy "deploy"):
//   ecr:GetAuthorizationToken      on *
//   ecr push/pull actions           on repository/eks-devsecops/profile-card
//   eks:DescribeCluster             on cluster/eks-devsecops"""
scene(None, "Recorded · aws iam get-role (redacted)", "The trust policy and the permissions",
      code("aws iam get-role --role-name eks-devsecops-github-deploy", TRUST, "javascript", 16) + notes([
          (0, "Shared provider", "the account's GitHub OIDC provider, read only"),
          (1, "Audience", "the token must be meant for AWS STS"),
          (2, "Subject", "this repo, this environment only"),
          (3, "Immutable IDs", "a re-created repo cannot get in"),
          (4, "Tiny permissions", "one registry, one cluster"),
      ]), [
    S("Here is the real trust policy, recorded from IAM with the account number redacted. The principal is the account's shared GitHub identity provider, which we only read.", hl=(1, 5),
      tts="Here is the real trust policy, recorded from I A M with the account number redacted. The principal is the account's shared GitHub identity provider, which we only read."),
    S("Condition one: the token's audience must be AWS STS.", hl=(9, 9), tts="Condition one: the token's audience must be A W S S T S."),
    S("Condition two, the important one: the subject must be this repository, running in its production environment. "
      "The production environment in GitHub only accepts deployments from the main branch. So a pull request, a fork, or another branch can never assume this role.", hl=(10, 11)),
    S("Notice the numbers in the subject: GitHub's new immutable format includes the owner and repository IDs. If someone deleted this repository and created a new one with the same name, its tokens would not match. "
      "My first deploy in the original build actually failed on this, until I updated the trust policy.", hl=(11, 11),
      tts="Notice the numbers in the subject: GitHub's new immutable format includes the owner and repository I Ds. If someone deleted this repository and created a new one with the same name, its tokens would not match. "
          "My first deploy in the original build actually failed on this, until I updated the trust policy."),
    S("And the permissions are tiny: log in to the registry, push to one repository, and describe one cluster. Inside Kubernetes, the access entry limits it to one namespace.", hl=(15, 18)),
], layout="code")

# ---------------------------------------------------------------- 3. Pipeline walkthrough
scene("The pipeline, stage by stage", "deploy.yaml · 12 stages", "Every stage, and why it exists", checklist([
    (0, "1", "Secret scan · gitleaks", "full git history: a leaked key anywhere stops the release"),
    (0, "2", "Code quality · oxlint + vitest", "lint and 5 unit tests"),
    (1, "3", "Dependencies · npm audit", "fails on high or critical vulnerabilities"),
    (1, "4", "Dockerfile + workflows · hadolint, actionlint, zizmor", "Dockerfile best practices; pinned, safe GitHub Actions"),
    (2, "5", "Infrastructure · Trivy config + kubeconform", "Terraform and Kubernetes misconfigurations, schema check"),
    (3, "6–9", "Build · Trivy image · SBOM · cosign", "no fixable CRITICAL/HIGH; parts list; signature"),
    (4, "10–12", "ECR by digest · deploy · rollout + checks", "exact digest, rollout must finish, can-i, smoke test"),
]), [
    S("Let us walk through the pipeline, stage by stage. Stage one, secret scanning with gitleaks, across the full git history. Secrets must be found before anything is deployed, because a leaked key in git is public the moment you push. "
      "Stage two, code quality: the linter and the unit tests.",
      tts="Let us walk through the pipeline, stage by stage. Stage one, secret scanning with git leaks, across the full git history. Secrets must be found before anything is deployed, because a leaked key in git is public the moment you push. "
          "Stage two, code quality: the linter and the unit tests."),
    S("Stage three, dependency security: npm audit fails on any high or critical vulnerability in our packages. Stage four, hadolint, which checks the Dockerfile against best practices, like pinning versions and not running as root. In the same stage, actionlint and zizmor check our own workflows, and every action is pinned to a commit.",
      tts="Stage three, dependency security: N P M audit fails on any high or critical vulnerability in our packages. Stage four, hado lint, which checks the Dockerfile against best practices, like pinning versions and not running as root. In the same stage, action lint and zizmor check our own workflows, and every action is pinned to a commit."),
    S("Stage five, infrastructure security: Trivy scans the Terraform and the rendered Kubernetes manifests for misconfigurations, and kubeconform checks them against the Kubernetes schema. "
      "This is an important DevSecOps idea: we scan the infrastructure before we deploy it.",
      tts="Stage five, infrastructure security: Trivy scans the Terraform and the rendered Kubernetes manifests for misconfigurations, and kube conform checks them against the Kubernetes schema. "
          "This is an important dev sec ops idea: we scan the infrastructure before we deploy it."),
    S("Stages six to nine: build the image, scan it, where critical and high block the release, generate the SBOM, and sign the image with cosign.",
      tts="Stages six to nine: build the image, scan it, where critical and high block the release, generate the S-bom, and sign the image with co-sign."),
    S("Stages ten to twelve: push to ECR and deploy the exact digest, wait for the rollout, prove the pipeline's own permissions are limited, and smoke test the live site through the load balancer.",
      tts="Stages ten to twelve: push to E C R and deploy the exact digest, wait for the rollout, prove the pipeline's own permissions are limited, and smoke test the live site through the load balancer."),
])

DEPLOY_YAML = """jobs:
  checks:                                  # stages 1-5, the whole CI suite
    uses: ./.github/workflows/ci.yaml
  build-scan:
    needs: checks                          # nothing builds unless all checks pass
    permissions: {contents: read}          # no cloud access at all
    steps: [build, "trivy --exit-code 1 --severity CRITICAL,HIGH", "syft SBOM"]
  deploy:
    needs: build-scan
    environment: production                # main branch only
    permissions: {contents: read, id-token: write}
    steps:
      - aws-actions/configure-aws-credentials   # OIDC -> temporary credentials
      - push to ECR by digest                   # + wait for ECR's own scan
      - cosign sign + verify                    # keyless, logged in Rekor
      - kubectl apply -k k8s                    # image@sha256:...
      - kubectl rollout status --timeout=300s
      - kubectl auth can-i ... (expect yes / no)
      - curl through the ALB (smoke test)"""
scene(None, ".github/workflows/deploy.yaml (simplified)", "Three jobs, and who may do what",
      code("deploy.yaml (simplified)", DEPLOY_YAML, "yaml", 20) + notes([
          (0, "checks", "the full CI suite first"),
          (1, "build-scan", "no credentials at all"),
          (2, "deploy", "production environment, OIDC"),
          (3, "A gap I fixed today", "deploy used to skip the CI suite"),
      ]), [
    S("Here is how that maps to the workflow. Job one, checks, runs the whole CI suite from the other workflow file.", hl=(1, 3)),
    S("Job two builds and scans the image, but only if every check passed. And it has no cloud permissions at all: the scanning tools never run next to AWS credentials.", hl=(4, 7)),
    S("Job three deploys. It runs in the protected production environment, it is the only job allowed to request an OIDC token, and it pushes, signs, applies, waits, checks its permissions and smoke tests.", hl=(8, 19),
      tts="Job three deploys. It runs in the protected production environment, it is the only job allowed to request an O I D C token, and it pushes, signs, applies, waits, checks its permissions and smoke tests."),
    S("An honest note: while preparing this workshop I found a gap. The deploy workflow used to skip the CI checks, so a vulnerable dependency could have reached production as long as the image scan passed. "
      "Job one fixes that. You will see it work in a few minutes.", hl=(1, 5)),
], layout="code")

scene(None, "Immutable tags and digests", "Why we deploy by digest", grid([
    card(0, "🏷️", "A tag", "profile-card:1.0.5 is a label; normally it can be moved to other content", "amber"),
    card(1, "🔒", "Immutable tags in ECR", "once pushed, a tag can never be overwritten", "ok"),
    card(2, "#️⃣", "A digest", "@sha256:506b0442… is the hash of the content itself", "ok"),
    card(3, "📌", "Deploy by digest", "the cluster runs exactly the bytes that were scanned and signed", "ok"),
], cols=2), [
    S("One more concept before we push. A tag, like profile card 1.0.5, is just a label. In most registries, anyone who can push can move that label to different content."),
    S("Our ECR repository has immutable tags, so a tag can never be overwritten.", tts="Our E C R repository has immutable tags, so a tag can never be overwritten."),
    S("A digest is different: it is the SHA 256 hash of the image content. Change one byte, and the digest changes.", tts="A digest is different: it is the shah 256 hash of the image content. Change one byte, and the digest changes."),
    S("So the pipeline deploys the digest. The cluster runs exactly the bytes that were scanned and signed, and nothing can be swapped in between."),
])

# ---------------------------------------------------------------- 4. Push and run
scene("Pushing code, the real pipeline", "Recorded · the developer workflow", "A small change, and a git push", terminal([
    (0, "$ git diff", "cmd"),
    (0, '-  tags: ["Docker", "Kubernetes", "Git", "Jenkins", "Ansible", "Terraform", "AWS", "Golang"],', "bad"),
    (0, '+  tags: ["Docker", "Kubernetes", "Amazon EKS", "Git", "Jenkins", "Ansible", "Terraform", "AWS", "Golang"],', "ok"),
    (1, "$ git commit -am \"feat(app): add Amazon EKS to the skills list\"", "cmd"),
    (1, "[main 2665ca0] feat(app): add Amazon EKS to the skills list", "out"),
    (1, "$ git push", "cmd"),
    (1, "   2456bf4..2665ca0  main -> main", "ok"),
], "bash (recorded)"), [
    S("Now the developer workflow. I connected the pipeline first: the deploy role from Terraform's output went into a GitHub secret on the production environment, never printed, and the deploy switch was turned on. "
      "Then a small, controlled change: add Amazon EKS to the skills on the profile card.",
      tts="Now the developer workflow. I connected the pipeline first: the deploy role from Terraform's output went into a GitHub secret on the production environment, never printed, and the deploy switch was turned on. "
          "Then a small, controlled change: add Amazon E K S to the skills on the profile card."),
    S("git add, git commit, git push. That is all the developer does. Everything else is the platform's job.", tts="Git add, git commit, git push. That is all the developer does. Everything else is the platform's job."),
])

scene(None, "Recorded · GitHub Actions", "The pipeline starts by itself", shot(0, "gh-run-progress.png", "Pipeline in progress"), [
    S("Seconds later, the deploy workflow starts on its own. Here it is mid-run: the five security check jobs ran in parallel and passed in about half a minute, and build and scan is running now. Deploy waits for it."),
])

scene(None, "Recorded · run 37167564754", "From push to live: 4 minutes 36 seconds", '<div class="compact">' + grid([
    tile(0, "🔑", "Secret scan", "5 s", "ok", "gitleaks, full history"),
    tile(0, "⚛️", "App checks", "11 s", "ok", "lint · tests · npm audit · build"),
    tile(0, "🐳", "Container", "26 s", "ok", "hadolint · Trivy image"),
    tile(0, "🏗️", "IaC", "32 s", "ok", "Terraform · Trivy · kubeconform"),
    tile(0, "🧷", "Pipeline security", "8 s", "ok", "pinned actions · actionlint · zizmor"),
    tile(1, "🔍", "Build and scan", "51 s", "ok", "build · Trivy gate · SBOM"),
    tile(2, "🚀", "Deploy to EKS", "3 min 1 s", "ok", "OIDC · ECR · cosign · rollout"),
], cols=4, gap=18) + "</div>" + f'<div style="margin-top:20px">{shot(3, "gh-run-done.png", "Pipeline done", "height:300px;width:auto")}</div>', [
    S("The finished run. The checks: secret scan five seconds, app checks eleven, the container job twenty six, the infrastructure job thirty two, and the pipeline security job, which checks our own workflows, eight. They run in parallel, so the whole security suite takes about half a minute."),
    S("Build and scan, fifty one seconds."),
    S("And deploy to EKS, three minutes, most of it waiting for the new pods to become healthy behind the load balancer.", tts="And deploy to E K S, three minutes, most of it waiting for the new pods to become healthy behind the load balancer."),
    S("Four minutes and thirty six seconds from git push to live. Let us look inside the deploy job."),
])

scene(None, "Recorded · inside the deploy job (redacted)", "OIDC, ECR, cosign, rollout, least privilege", terminal([
    (0, "Assuming role with OIDC", "out"),
    (0, "Authenticated as assumedRoleId AROA…<redacted>:github-deploy-37167564754", "ok"),
    (0, "IMAGE: ***.dkr.ecr.eu-central-1.amazonaws.com/eks-devsecops/profile-card@sha256:506b0442a033…", "out"),
    (1, "ECR scan status: COMPLETE        ECR findings by severity: {}", "ok"),
    (1, "signed and verified", "ok"),
    (2, "serviceaccount/profile-card created    service/profile-card created    deployment.apps/profile-card created", "out"),
    (2, "poddisruptionbudget.policy/profile-card created    ingress.networking.k8s.io/profile-card created", "out"),
    (2, "networkpolicy…/allow-http-from-load-balancer created    networkpolicy…/default-deny created", "out"),
    (2, "deployment \"profile-card\" successfully rolled out", "ok"),
    (3, "can-i create deployments -n profile-card -> yes (expected yes)", "ok"),
    (3, "can-i create deployments -n kube-system -> no (expected no)", "ok"),
    (3, "can-i get secrets -n kube-system -> no (expected no)", "ok"),
    (3, "can-i create clusterrolebindings -> no (expected no)      can-i delete namespaces -> no (expected no)", "ok"),
], "GitHub Actions log (recorded, excerpt)"), [
    S("Assuming role with OIDC, authenticated as a session named after the run. Notice the image line: GitHub prints three stars instead of the account number, because the workflow masks it. Our public logs never show it.",
      tts="Assuming role with O I D C, authenticated as a session named after the run. Notice the image line: GitHub prints three stars instead of the account number, because the workflow masks it. Our public logs never show it."),
    S("ECR's own scan completed with zero findings, a second opinion after Trivy. Then cosign signed the image and verified the signature.",
      tts="E C R's own scan completed with zero findings, a second opinion after Trivy. Then co-sign signed the image and verified the signature."),
    S("kubectl applied our seven objects, and the rollout finished.", tts="Kube control applied our seven objects, and the rollout finished."),
    S("Then the pipeline proves its own limits. Yes, it may create deployments in its own namespace. No to kube-system, no to secrets, no to cluster role bindings, no to deleting namespaces. If any of those answers ever changes, the job fails.",
      tts="Then the pipeline proves its own limits. Yes, it may create deployments in its own namespace. No to kube system, no to secrets, no to cluster role bindings, no to deleting namespaces. If any of those answers ever changes, the job fails."),
])

# ---------------------------------------------------------------- 5. Application live
scene("The application goes live", "Recorded · kubectl", "Pods, service, ingress", terminal([
    (0, "$ kubectl -n profile-card get pods,svc,ingress -o wide", "cmd"),
    (0, "pod/profile-card-…-b6552   1/1   Running   10.42.16.30   ip-10-42-22-252…   (zone b)", "ok"),
    (0, "pod/profile-card-…-czjsj   1/1   Running   10.42.4.45    ip-10-42-7-30…     (zone a)", "ok"),
    (1, "service/profile-card   ClusterIP   172.20.212.124   80/TCP", "out"),
    (2, "ingress/profile-card   alb   eks-devsecops-profile-card-1786251604.eu-central-1.elb.amazonaws.com   80", "ok"),
    (3, "$ aws elbv2 describe-target-health …", "cmd"),
    (3, "|  8080 |  healthy  |  10.42.16.30  |", "ok"),
    (3, "|  8080 |  healthy  |  10.42.4.45   |", "ok"),
], "bash (recorded)"), [
    S("kubectl get pods: two pods running, on different nodes, in different availability zones.", tts="Kube control get pods: two pods running, on different nodes, in different availability zones."),
    S("The service is a ClusterIP: an internal address only, not exposed by itself.", tts="The service is a cluster I P: an internal address only, not exposed by itself."),
    S("And the Ingress has an address: the DNS name of the Application Load Balancer that the controller created for us.", tts="And the Ingress has an address: the D N S name of the Application Load Balancer that the controller created for us."),
    S("In AWS, the target group shows both pod IP addresses on port 8080, healthy. The load balancer talks straight to the pods.", tts="In AWS, the target group shows both pod I P addresses on port 8080, healthy. The load balancer talks straight to the pods."),
])

scene(None, "AWS Console · load balancer (recorded)", "The ALB the controller created", grid([
    card(0, "🌍", "internet-facing, application", "eks-devsecops-profile-card · eu-central-1a + 1b · active", "ok"),
], cols=1) + f'<div style="display:flex;gap:24px;margin-top:20px">{shot(0, "c14-alb.png", "ALB", "height:520px;width:auto")}'
      f'{shot(1, "c15-targets.png", "Target group", "height:520px;width:auto")}</div>', [
    S("In the console: the load balancer, internet facing, of type application, active in both availability zones. Terraform did not create it. The controller did, from our Ingress."),
    S("And its target group, with our two pods as targets, both healthy."),
])

scene(None, "Recorded · the browser", "Live on the internet",
      shot(0, "app-live-card.png", "The profile card in the browser", "height:700px;width:auto"), [
    S("And here it is in the browser: the profile card, with Amazon EKS now in the skills, served from our cluster. "
      "The footer shows the version and the commit of this exact build.",
      tts="And here it is in the browser: the profile card, with Amazon E K S now in the skills, served from our cluster. "
          "The footer shows the version and the commit of this exact build."),
])

scene(None, "The request path", "From the internet to the profile card", svg(
    box(0, 0, 300, 210, 140, "🌍", "Internet", ["browser"], "blue")
    + arrow(1, 215, 370, 265, 370)
    + box(1, 270, 300, 250, 140, "⚖️", "ALB", ["public subnets"], "ok", "#0f2a22")
    + arrow(2, 525, 370, 575, 370)
    + box(2, 580, 300, 250, 140, "🧭", "Ingress", ["rules: / → service"], "blue")
    + arrow(3, 835, 370, 885, 370)
    + box(3, 890, 300, 250, 140, "🔌", "Service", ["finds the pods"], "blue")
    + arrow(4, 1145, 370, 1195, 370)
    + box(4, 1200, 300, 250, 140, "📦", "Pods", ["private subnets"], "blue", "#16306a")
    + arrow(5, 1455, 370, 1505, 370)
    + box(5, 1510, 300, 210, 140, "🌐", "nginx", ["profile card"], "ok", "#0f2a22")
    + label(6, 860, 560, "target-type ip: the ALB sends traffic straight to pod IPs; the NetworkPolicy only lets the ALB subnets in", 26, "amber", "middle", 700)
), [
    S("Let us trace the request from the internet all the way to the pod. The browser connects to the load balancer's public address."),
    S("The Application Load Balancer lives in the public subnets."),
    S("The Ingress rules, which the controller turned into load balancer rules, say: every path goes to our service."),
    S("The service tells the controller which pods belong to it."),
    S("The pods live in the private subnets."),
    S("And inside each pod, nginx serves the profile card files, with the security headers.", tts="And inside each pod, engine x serves the profile card files, with the security headers."),
    S("Because we use target type IP, the load balancer sends traffic directly to the pod addresses, and our network policy lets exactly those load balancer subnets in, and nothing else.",
      tts="Because we use target type I P, the load balancer sends traffic directly to the pod addresses, and our network policy lets exactly those load balancer subnets in, and nothing else."),
])

scene(None, "A detail worth knowing", "Readiness gates appear from the second rollout", terminal([
    (0, "# first deployment: pods created before the controller knew the service", "dim"),
    (0, "NAME                            READY   STATUS    READINESS GATES", "out"),
    (0, "profile-card-664fb87c9c-b6552   1/1     Running   <none>", "warn"),
    (1, "# every later rollout: the controller injects a gate tied to the ALB target's health", "dim"),
    (1, "profile-card-d5bbfbc97-dlhvj    1/1     Running   1/1", "ok"),
    (1, "profile-card-d5bbfbc97-kt5z2    1/1     Running   1/1", "ok"),
], "bash (recorded)"), [
    S("One detail I noticed in the recording, and it is worth knowing. On the very first deployment, the readiness gates column says none. "
      "The pods were created at the same moment as the Ingress, before the controller knew about the service, so it could not attach a gate."),
    S("From the second rollout on, every pod gets a gate: it only counts as ready when the load balancer reports it healthy. That is what makes later rollouts zero downtime. "
      "In production, you deploy the Ingress and service first, or simply accept that the very first rollout has no gate."),
])

# ---------------------------------------------------------------- 6. Failed security check
scene("A security check fails, on purpose", "Recorded · a hurried developer", "Adding a dependency with a known vulnerability", terminal([
    (0, "$ npm install lodash@4.17.20", "cmd"),
    (0, "added 106 packages in 3s", "out"),
    (0, "$ git commit -am \"feat(app): add lodash for string helpers\"", "cmd"),
    (0, "$ git push", "cmd"),
    (0, "   2665ca0..1155ac6  main -> main", "out"),
], "bash (recorded)"), [
    S("Now let us deliberately make the security scan fail, so you can see why this stage exists. Imagine a hurried developer adds lodash, version 4.17.20, for a few string helpers, and pushes straight to main. "
      "That version has known high severity vulnerabilities.",
      tts="Now let us deliberately make the security scan fail, so you can see why this stage exists. Imagine a hurried developer adds lodash, version 4 point 17 point 20, for a few string helpers, and pushes straight to main. "
          "That version has known high severity vulnerabilities."),
])

scene(None, "Recorded · the pipeline stops it", "The pipeline failed. That is a successful security outcome.",
      shot(0, "gh-run-failed.png", "Failed run", "height:400px;width:auto")
      + '<div class="st" data-s="1" style="margin-top:16px;width:1600px">'
      + terminal([(1, "Run npm audit --audit-level=high", "cmd"),
                  (1, "lodash  <=4.17.23     Severity: high", "bad"),
                  (1, "Command Injection in lodash - GHSA-35jh-r3h4-6jhm", "bad"),
                  (1, "lodash vulnerable to Code Injection via `_.template` imports key names - GHSA-r5fr-rjxr-66jc", "bad"),
                  (1, "1 high severity vulnerability                         ##[error]Process completed with exit code 1.", "bad"),
                  (2, "Build and scan: skipped      Deploy to EKS: skipped      site: HTTP 200 (previous version)", "ok")], "GitHub Actions log (recorded)")
      + "</div>", [
    S("The run is red. The app job failed, and build and deploy were skipped."),
    S("The log shows why: npm audit found lodash with a command injection and a code injection advisory, severity high. Exit code one.",
      tts="The log shows why: N P M audit found lodash with a command injection and a code injection advisory, severity high. Exit code one."),
    S("Build and deploy never started, and the live site kept serving the previous version. This is exactly what we want. The pipeline failed, and that is actually a successful security outcome: the vulnerable code never reached production."),
])

scene(None, "Recorded · fix it, the right way", "Upgrade, check locally, push again", terminal([
    (0, "$ npm audit --audit-level=high", "cmd"),
    (0, "lodash  <=4.17.23   Severity: high", "bad"),
    (1, "$ npm install lodash@4.18.1", "cmd"),
    (1, "$ npm audit --audit-level=high", "cmd"),
    (1, "found 0 vulnerabilities", "ok"),
    (2, "$ git commit -am \"fix(app): upgrade lodash to 4.18.1 (GHSA-35jh-r3h4-6jhm and 3 more)\" && git push", "cmd"),
    (2, "Security checks: 5 × success · Build and scan: success · Deploy to EKS: success      # 3 min 23 s", "ok"),
], "bash (recorded)"), [
    S("The fix is the normal developer loop. Reproduce it locally: the same audit, the same finding."),
    S("Upgrade to the patched version, 4.18.1, and the audit is clean.", tts="Upgrade to the patched version, 4 point 18 point 1, and the audit is clean."),
    S("Commit with a message that names the advisory, and push. All five checks pass, the image is built and scanned, and the deployment goes green in three minutes and twenty three seconds."),
])

# ---------------------------------------------------------------- 7. Troubleshooting
scene("Troubleshooting a broken rollout", "Methodology", "Find the layer first, then the cause", checklist([
    (0, "1", "Users", "is the site up? (curl through the load balancer)"),
    (1, "2", "Application", "does the process start? (kubectl logs)"),
    (1, "3", "Container", "does it answer inside the pod? (kubectl exec)"),
    (2, "4", "Kubernetes", "pods, rollout, describe, events, service ports"),
    (3, "5", "AWS load balancer", "Ingress backends, target health"),
]), [
    S("Next, troubleshooting. When something breaks, do not start by guessing. First I check whether the problem is user facing at all: is the site up?"),
    S("Then I work through the layers: is it application level, does the process even start? Is it container level, does it answer inside the pod?"),
    S("Is it Kubernetes level: pods, rollout, events, ports?"),
    S("Or is it at the AWS load balancer level: the Ingress backends and the target health? Each layer has its command, and the evidence tells you where to stop."),
])

scene(None, "Recorded · a lesson first", "My first attempt to break it did not break anything", terminal([
    (0, "# change: readinessProbe path /healthz  ->  /health   (a typo)", "dim"),
    (0, "deploy run: success          # the rollout passed!", "warn"),
    (1, "$ for p in /healthz /health /does-not-exist; do curl -w '…' http://<alb>$p; done", "cmd"),
    (1, "/healthz         -> HTTP 200, text/plain", "ok"),
    (1, "/health          -> HTTP 200, text/html", "warn"),
    (1, "/does-not-exist  -> HTTP 200, text/html", "warn"),
    (2, "# a single-page app answers every unknown path with index.html: probes must use a dedicated endpoint", "dim"),
], "bash (recorded)"), [
    S("A lesson before the real incident. My first attempt to break the rollout was a typo in the readiness probe path: health instead of healthz. And the rollout passed!"),
    S("Here is why. Our nginx serves a single page app: any unknown path returns index dot html with status 200. So the typo path looked perfectly healthy. Only healthz returns plain text.",
      tts="Here is why. Our engine x serves a single page app: any unknown path returns index dot html with status 200. So the typo path looked perfectly healthy. Only healthz returns plain text."),
    S("The lesson: on single page apps, health probes must point at a dedicated endpoint, and you should test that a wrong path actually fails. I reverted the change, and broke it properly."),
])

scene(None, "Recorded · the real incident", "A probe on the wrong port", terminal([
    (0, "$ git diff", "cmd"),
    (0, "-            httpGet: {path: /healthz, port: http}", "bad"),
    (0, "+            httpGet: {path: /healthz, port: 80}", "ok"),
    (0, "$ git commit -am \"chore(k8s): probe the service port 80\" && git push", "cmd"),
    (1, "$ curl http://<alb>/            site: HTTP 200", "ok"),
    (1, "$ kubectl -n profile-card get pods", "cmd"),
    (1, "profile-card-5494bdfc4-ctgb6   1/1   Running   READINESS GATES 1/1", "ok"),
    (1, "profile-card-5494bdfc4-hxjh8   1/1   Running   READINESS GATES 1/1", "ok"),
    (1, "profile-card-868665fd8-sd6n9   0/1   Running   READINESS GATES 0/1", "bad"),
    (2, "$ kubectl -n profile-card rollout status deploy/profile-card", "cmd"),
    (2, "Waiting for deployment \"profile-card\" rollout to finish: 1 out of 2 new replicas have been updated...", "warn"),
], "bash (recorded)"), [
    S("The real incident: someone changes the readiness probe to port 80, thinking of the service port, and pushes."),
    S("Layer one, users: the site still answers, status 200. Good, so this is not an outage. Then the pods: two old pods ready, and one new pod at zero of one, with its readiness gate also at zero.",
      tts="Layer one, users: the site still answers, status 200. Good, so this is not an outage. Then the pods: two old pods ready, and one new pod at zero of one, with its readiness gate also at zero."),
    S("And the rollout is stuck waiting. Because of max unavailable zero, Kubernetes will not remove an old pod until a new one is ready. That is why users see nothing."),
])

scene(None, "Recorded · investigation", "describe, events, logs, exec", terminal([
    (0, "$ kubectl -n profile-card describe pod profile-card-868665fd8-sd6n9", "cmd"),
    (0, "Readiness:  http-get http://:80/healthz delay=0s timeout=1s period=5s", "warn"),
    (0, "Warning  Unhealthy  kubelet  Readiness probe failed: Get \"http://10.42.16.94:80/healthz\": … connection refused", "bad"),
    (1, "$ kubectl -n profile-card logs profile-card-868665fd8-sd6n9 --tail=3", "cmd"),
    (1, "[notice] start worker processes    [notice] start worker process 22    … 23", "ok"),
    (2, "$ kubectl -n profile-card exec <pod> -- wget -O- http://127.0.0.1:80/healthz", "cmd"),
    (2, "wget: can't connect to remote host (127.0.0.1): Connection refused          port 80 exit: 1", "bad"),
    (2, "$ kubectl -n profile-card exec <pod> -- wget -O- http://127.0.0.1:8080/healthz", "cmd"),
    (2, "ok                                                                           port 8080 exit: 0", "ok"),
    (3, "$ kubectl -n profile-card get svc profile-card -o jsonpath='{…port} -> {…targetPort}'", "cmd"),
    (3, "80 -> targetPort http   (http = containerPort 8080)", "warn"),
], "bash (recorded)"), [
    S("Describe the pod. The readiness probe goes to port 80, and the event says: connection refused."),
    S("Is it the application? The logs say no: nginx started normally, with its worker processes. The application is fine.", tts="Is it the application? The logs say no: engine x started normally, with its worker processes. The application is fine."),
    S("Is it the container? Exec into the pod and try both ports. Port 80: connection refused. Port 8080: ok. The container listens on 8080, as a non-root process must, because ports below 1024 need privileges."),
    S("And the service explains the confusion: the service listens on port 80 and forwards to the container port named http, which is 8080. The probe talks to the container directly, so it needs the container port. Root cause found."),
])

scene(None, "Recorded · the AWS side, and the fix", "Users never noticed. Revert, and it is green.", terminal([
    (0, "$ kubectl -n profile-card describe ingress profile-card", "cmd"),
    (0, "/   profile-card:http (10.42.16.30:8080,10.42.6.239:8080)          # only the old, ready pods", "ok"),
    (0, "$ aws elbv2 describe-target-health …", "cmd"),
    (0, "|  healthy  |  10.42.6.239  |       |  healthy  |  10.42.16.30  |", "ok"),
    (1, "deploy run: Deploy the exact digest: failure", "bad"),
    (1, "error: timed out waiting for the condition", "bad"),
    (2, "$ git revert --no-edit HEAD && git push", "cmd"),
    (2, "[main b98fc36] Revert \"chore(k8s): probe the service port 80\"", "out"),
    (2, "revert run: success", "ok"),
], "bash + GitHub Actions (recorded)"), [
    S("And the load balancer level: the Ingress backends and the target group contain only the two old pods, both healthy. The broken pod never received a single request. That is the readiness gate doing its job."),
    S("After five minutes, the pipeline's rollout check timed out, and the deploy job failed: a red run, telling the team something is wrong."),
    S("The fix: git revert, and push. The pipeline goes green, and at no point during this incident did a user see an error."),
])

# ---------------------------------------------------------------- 8. Why DevSecOps
scene("Why this is DevSecOps", "Putting it together", "Security at every step, not at the end", svg(
    "".join(box(i // 2, (i % 6) * 287, 0 if i < 6 else 300, 270, 220, ic, t, [d], "amber" if i % 2 else "blue", "#13233a")
            for i, (ic, t, d) in enumerate([
                ("🔑", "Secrets", "gitleaks"), ("📦", "Dependencies", "npm audit"), ("🐳", "Dockerfile", "hadolint"),
                ("🏗️", "Terraform", "Trivy config"), ("☸️", "Kubernetes", "Trivy + kubeconform"), ("🔍", "Image", "Trivy · ECR scan"),
                ("🧾", "Contents", "SBOM"), ("✍️", "Origin", "cosign"), ("🪪", "Identity", "OIDC · access entries"),
                ("📌", "Deployment", "digest · can-i"), ("🛡️", "Runtime", "PSA · NetworkPolicy"), ("🔭", "Cloud", "IMDSv2 · KMS · logs")]))
    + label(6, 860, 640, "Development + Security + Operations = DevSecOps", 40, "ok", "middle", 900)
), [
    S("Let us connect everything. Look at where security lives in this project: in the code, in the secrets check, in the dependencies."),
    S("In the Dockerfile and in the Terraform."),
    S("In the Kubernetes manifests and in the container image."),
    S("In the SBOM and the signature: what is inside, and where it came from.", tts="In the S-bom and the signature: what is inside, and where it came from."),
    S("In the identity of the pipeline, and in the deployment itself."),
    S("And at runtime: Pod Security, network policies, and the cloud settings around the nodes.", tts="And at runtime: pod security, network policies, and the cloud settings around the nodes."),
    S("That is DevSecOps: development, security and operations as one flow. Security is not a final step after deployment. If it is last, it is already too late.", tts="That is dev sec ops: development, security and operations as one flow. Security is not a final step after deployment. If it is last, it is already too late."),
])

scene("The final architecture", "What actually ran", "From the developer's laptop to the public URL", svg(
    box(0, 0, 0, 300, 130, "💻", "git push", ["developer"], "blue")
    + arrow(0, 305, 65, 355, 65)
    + box(0, 360, 0, 1360, 130, "⚙️", "GitHub Actions", ["gitleaks · tests · npm audit · hadolint · Trivy IaC · kubeconform → build → Trivy · SBOM · cosign"], "amber", "#2b2410")
    + arrow(1, 1040, 135, 1040, 175) + label(1, 1062, 166, "OIDC", 21, "sky")
    + box(1, 360, 180, 1360, 130, "📦", "Amazon ECR", ["immutable tags · scan on push · deployed by digest"], "blue")
    + box(2, 0, 330, 1720, 410, "☁️", "AWS eu-central-1 · VPC 10.42.0.0/16 · 2 AZs", [], "amber", "#111c2e")
    + box(2, 40, 410, 470, 290, "🌍", "Public subnets", ["ALB (internet-facing)", "NAT gateway"], "ok", "#0f2a22")
    + box(3, 560, 410, 700, 290, "🔒", "Private subnets · 2 × t3.medium", ["EKS 1.37 · access entries · KMS", "pods ×2: PSA restricted · NetworkPolicy", "LB controller via Pod Identity"], "blue", "#16306a")
    + box(4, 1300, 410, 380, 290, "🔐", "Around it", ["KMS: secrets", "IAM: roles", "CloudWatch: logs"], "violet")
    + arrow(4, 515, 555, 555, 555, "ok")
), [
    S("Here is the final architecture, exactly as it ran. The developer pushes. GitHub Actions runs every check, builds, scans, creates the SBOM and signs.",
      tts="Here is the final architecture, exactly as it ran. The developer pushes. GitHub Actions runs every check, builds, scans, creates the S-bom and signs."),
    S("Through OIDC it pushes to ECR, by digest.", tts="Through O I D C it pushes to E C R, by digest."),
    S("In Frankfurt, the VPC: the load balancer and the NAT gateway in the public subnets.", tts="In Frankfurt, the V P C: the load balancer and the NAT gateway in the public subnets."),
    S("The private nodes, the cluster with access entries and KMS, our restricted pods, and the controller with Pod Identity.", tts="The private nodes, the cluster with access entries and K M S, our restricted pods, and the controller with pod identity."),
    S("And KMS, IAM and CloudWatch around it. From the developer's laptop to the public URL, every step has a security control.", tts="And K M S, I A M and CloudWatch around it. From the developer's laptop to the public URL, every step has a security control."),
])

# ---------------------------------------------------------------- 9. Production improvements
scene("From lab to enterprise", "What we built vs. what a mature platform adds", "This project, and the next steps", svg(
    box(0, 0, 0, 840, 740, "✅", "Implemented in this project", [], "ok", "#0f2a22")
    + "".join(label(0, 30, 110 + i * 46, t, 24, "#d6ffe6", "start", 600) for i, t in enumerate([
        "Terraform, pinned modules, region + account guards", "private nodes, IMDSv2, encrypted disks, KMS secrets",
        "access entries, Pod Identity, GitHub OIDC", "gitleaks, npm audit, hadolint, Trivy (IaC + image)",
        "SBOM, cosign signature, deploy by digest", "PSA restricted, default-deny NetworkPolicy",
        "zero-downtime rollouts (readiness gates)", "audit logs, flow logs", "verified teardown"]))
    + box(1, 880, 0, 840, 740, "🏢", "A mature enterprise platform adds", [], "amber", "#2b2410")
    + "".join(label(1 + i // 5, 910, 110 + i * 40, t, 22, "#ffe9b0", "start", 600) for i, t in enumerate([
        "NAT gateway per AZ · remote state in S3 + locking", "separate AWS accounts + environments · staging first",
        "Route 53 + ACM + HTTPS · AWS WAF", "Secrets Manager + External Secrets",
        "admission policies: only signed images run", "runtime security (e.g. Falco, GuardDuty)",
        "central logging · Prometheus/Grafana · alerting", "backups + disaster recovery · cost optimisation",
        "branch protection · required reviews · approvals", "dependency updates · vulnerability SLAs",
        "policy as code across all clusters", "private API endpoint + self-hosted runners", "multi-region (if the business needs it)"]))
), [
    S("Let us be clear about what we built, and what a mature enterprise platform would add. On the left, what this project implements: the infrastructure as code with guard rails, private and encrypted nodes, keyless identities, "
      "scanning at every step, signed images deployed by digest, restricted pods, zero downtime rollouts, logs, and a verified teardown."),
    S("On the right, the next steps. One NAT gateway per zone, Terraform state in S3 with locking, separate AWS accounts and environments with staging before production, and HTTPS with Route 53, a certificate from ACM, and WAF in front.",
      tts="On the right, the next steps. One NAT gateway per zone, Terraform state in S 3 with locking, separate A W S accounts and environments with staging before production, and H T T P S with Route 53, a certificate from A C M, and WAF in front."),
    S("Secrets from Secrets Manager, admission policies that make signature verification mandatory, runtime security, central logging, Prometheus and Grafana with alerting, backups, disaster recovery and cost optimisation."),
    S("And the process side: branch protection, required reviews and approvals, dependency updates, vulnerability fix deadlines, policy as code, a private API endpoint with self hosted runners, and multiple regions if the business really needs it.",
      tts="And the process side: branch protection, required reviews and approvals, dependency updates, vulnerability fix deadlines, policy as code, a private A P I endpoint with self hosted runners, and multiple regions if the business really needs it."),
])

scene(None, "The HTTPS limitation", "Why this lab runs on plain HTTP", grid([
    card(0, "🌐", "No domain, no certificate", "TLS certificates are issued for names; this lab has only the ALB's AWS name", "amber"),
    card(1, "🔒", "In production", "Route 53 domain + ACM certificate + HTTPS listener + HTTP→HTTPS redirect", "ok"),
    card(2, "⚠️", "Why it is mandatory", "without TLS, anyone on the network can read and change the traffic", "bad"),
], cols=3), [
    S("One explicit limitation: this lab runs on plain HTTP. A TLS certificate is issued for a domain name, and for this tutorial there is no domain, only the load balancer's AWS generated name.",
      tts="One explicit limitation: this lab runs on plain H T T P. A T L S certificate is issued for a domain name, and for this tutorial there is no domain, only the load balancer's AWS generated name."),
    S("In a real production environment, I would put the domain in Route 53, issue a certificate with ACM, add an HTTPS listener with two Ingress annotations, and redirect all HTTP to HTTPS.",
      tts="In a real production environment, I would put the domain in Route 53, issue a certificate with A C M, add an H T T P S listener with two Ingress annotations, and redirect all H T T P to H T T P S."),
    S("And for a public application this is not optional. Without TLS, anyone on the network path can read the traffic, and change it.", tts="And for a public application this is not optional. Without T L S, anyone on the network path can read the traffic, and change it."),
])

scene("Cost", "Approximate eu-central-1 on-demand prices", "What does this platform cost?", grid([
    tile(0, "☸️", "EKS control plane", "~$0.10/h", "blue"),
    tile(0, "🖥️", "2 × t3.medium", "~$0.10/h", "blue"),
    tile(0, "🌐", "NAT gateway", "~$0.05/h", "blue"),
    tile(0, "⚖️", "ALB, public IPv4, EBS, KMS, logs", "~$0.05/h", "blue"),
    tile(1, "⏱️", "A 5–8 hour training day", "~$2–3", "amber", "buffer: under ~$10"),
    tile(2, "💡", "Cheaper for learning", "1 node · spot", "ok", "same-day teardown · or kind / minikube locally"),
], cols=3, gap=20), [
    S("And cost. Roughly, at on-demand prices in Frankfurt: ten cents per hour for the EKS control plane, ten cents for the two nodes, five for the NAT gateway, and about five more for the load balancer, public IP addresses, disks, KMS and logs. "
      "Around thirty cents per hour in total.",
      tts="And cost. Roughly, at on-demand prices in Frankfurt: ten cents per hour for the E K S control plane, ten cents for the two nodes, five for the NAT gateway, and about five more for the load balancer, public I P addresses, disks, K M S and logs. "
          "Around thirty cents per hour in total."),
    S("So a five to eight hour training day costs about two to three dollars. Keep a safety buffer of around ten. These are estimates: prices change, and your own bill is the truth, so check it in your account."),
    S("To make it cheaper for learning: one node instead of two, spot instances, and above all, delete the lab the same day. Or practise the Kubernetes parts locally first, with kind or minikube."),
])

# ---------------------------------------------------------------- 10. Teardown
scene("Teardown, done right", "The order matters", "Before destroying anything: only our resources, in the right order", checklist([
    (0, "0", "Stop deployments", "gh variable set DEPLOY_ENABLED --body false"),
    (1, "1", "Delete the Ingress first", "the controller removes the ALB, its target groups and security groups"),
    (2, "2", "terraform destroy", "everything Terraform created, including ECR (force_delete)"),
    (3, "3", "KMS key", "scheduled for deletion: AWS enforces a 7-day minimum (no cost while pending)"),
    (4, "4", "Verify", "by name, by tag Project=eks-devsecops, by real state; shared OIDC provider still there"),
]), [
    S("Now the part most tutorials skip: deleting everything. Before destroying anything, let us make sure we only delete resources belonging to this project, and in the right order. First, stop new deployments."),
    S("Step one: delete the Kubernetes Ingress first. The load balancer controller created the ALB, so the controller must remove it, with its target groups and security groups. "
      "If you run terraform destroy first, the controller dies before it can clean up, the ALB is orphaned, and deleting the VPC fails.",
      tts="Step one: delete the Kubernetes Ingress first. The load balancer controller created the A L B, so the controller must remove it, with its target groups and security groups. "
          "If you run terraform destroy first, the controller dies before it can clean up, the A L B is orphaned, and deleting the V P C fails."),
    S("Step two: terraform destroy. That includes the container registry, which has force delete set, so its images go with it."),
    S("Step three: the KMS key is scheduled for deletion. AWS enforces a waiting period of at least seven days, so you can recover from a mistake. A key waiting for deletion costs nothing.",
      tts="Step three: the K M S key is scheduled for deletion. AWS enforces a waiting period of at least seven days, so you can recover from a mistake. A key waiting for deletion costs nothing."),
    S("And step four: verify. The teardown script does all of this, and then runs the verification."),
])

scene(None, "Recorded · scripts/teardown.sh", "72 resources destroyed", terminal([
    (0, "$ gh variable set DEPLOY_ENABLED --body false", "cmd"),
    (0, "$ scripts/teardown.sh", "cmd"),
    (0, "==> Deleting the Ingress (the controller removes the load balancer)", "out"),
    (0, "==> Load balancer deleted", "ok"),
    (1, "==> terraform destroy", "out"),
    (1, "module.vpc.aws_nat_gateway.this[0]: Destruction complete after 1m0s", "out"),
    (1, "module.eks.aws_eks_cluster.this[0]: Destruction complete after 2m26s", "out"),
    (1, "module.vpc.aws_vpc.this[0]: Destruction complete after 1s", "out"),
    (1, "Destroy complete! Resources: 72 destroyed.", "ok"),
], "bash (recorded, excerpt)"), [
    S("Deploys off, then the script. The Ingress is deleted, and the script waits until the load balancer is really gone before it continues."),
    S("Then terraform destroy: the NAT gateway in one minute, the cluster in two and a half, and finally the VPC. Seventy two resources destroyed.", tts="Then terraform destroy: the NAT gateway in one minute, the cluster in two and a half, and finally the V P C. Seventy two resources destroyed."),
])

scene("Verifying that nothing is left", "Recorded · scripts/verify-teardown.sh", "Do not say \"everything is deleted\". Prove it.", terminal([
    (0, "Resources of project eks-devsecops in eu-central-1:", "out"),
    (0, "  gone  EKS cluster        gone  VPC          gone  subnets          gone  NAT gateways", "ok"),
    (0, "  gone  Elastic IPs        gone  EC2 nodes    gone  network interfaces   gone  security groups", "ok"),
    (0, "  gone  load balancer      gone  target groups   gone  ECR repository    gone  CloudWatch log groups", "ok"),
    (0, "  gone  KMS alias          gone  anything else tagged Project=eks-devsecops", "ok"),
    (1, "Global IAM resources of the project (counted only when tagged Project=eks-devsecops):", "out"),
    (1, "  gone  IAM roles          gone  IAM policies", "ok"),
    (2, "Shared resources that must still exist (never touched by this project):", "out"),
    (2, "  kept  GitHub OIDC identity provider", "ok"),
    (3, "KMS key: PendingDeletion (AWS keeps a deleted key for 7 days, at no cost, before removing it)", "out"),
    (3, "Clean: nothing of this project is left.", "ok"),
], "bash (recorded)"), [
    S("Do not just say everything has been deleted. Verify it. The script checks every resource type this project creates: the cluster, the VPC, subnets, NAT gateways, IP addresses, nodes, network interfaces, "
      "security groups, the load balancer and its target groups, the registry, the log groups, the KMS alias, and anything else tagged with our project.",
      tts="Do not just say everything has been deleted. Verify it. The script checks every resource type this project creates: the cluster, the V P C, subnets, NAT gateways, I P addresses, nodes, network interfaces, "
          "security groups, the load balancer and its target groups, the registry, the log groups, the K M S alias, and anything else tagged with our project."),
    S("Then IAM, which is global: our roles and policies are gone. They are matched by name and confirmed by the project tag, so another team's similarly named role can never be touched or miscounted.",
      tts="Then I A M, which is global: our roles and policies are gone. They are matched by name and confirmed by the project tag, so another team's similarly named role can never be touched or miscounted."),
    S("And the shared GitHub identity provider still exists. We did not modify it, and we did not delete it."),
    S("The KMS key is waiting out its seven days. Clean. And one more honest detail: the first time I ran this, it reported two deleted subnets as left over, because AWS's tag index lags behind. "
      "The script now checks each resource's real state, and it still counts anything it does not recognise as left over. When in doubt, fail safe.",
      tts="The K M S key is waiting out its seven days. Clean. And one more honest detail: the first time I ran this, it reported two deleted subnets as left over, because AWS's tag index lags behind. "
          "The script now checks each resource's real state, and it still counts anything it does not recognise as left over. When in doubt, fail safe."),
])

scene(None, "Recorded · before and after", "The account, exactly as we found it", terminal([
    (0, "VPCs:              1  (before: 1, the default VPC)", "ok"),
    (0, "EC2 instances:     0  (before: 0)", "ok"),
    (0, "Load balancers:    0  (before: 0)", "ok"),
    (0, "EKS clusters:      0  (before: 0)", "ok"),
    (0, "NAT gateways:      0  (before: 0)", "ok"),
    (0, "ECR repositories:  0  (before: 0)", "ok"),
    (0, "GitHub OIDC provider: 1  (before: 1, untouched)", "ok"),
], "bash (recorded)") + f'<div style="display:flex;gap:24px;margin-top:20px">{shot(1, "c20-eks-after.png", "EKS after", "height:360px;width:auto")}'
      f'{shot(1, "c22-lbs-after.png", "Load balancers after", "height:360px;width:auto")}</div>', [
    S("And the final comparison with the inventory from part one: every number is back to where it started, and the shared identity provider is untouched."),
    S("The console agrees: no clusters, no load balancers. We worked inside a controlled scope, and we only touched resources created for this project."),
])

# ---------------------------------------------------------------- 11. Rules + outcome
scene("Safety rules for shared accounts", "Rules I followed the whole time", "Working safely in someone else's account", checklist([
    (0, "🌍", "One region", "eu-central-1 only, enforced by Terraform"),
    (0, "🏷️", "Names and tags", "eks-devsecops-* · Project=eks-devsecops · Owner=sufyan"),
    (1, "🪪", "IAM", "only uniquely named project roles; never touch unrelated IAM"),
    (1, "🔗", "Shared GitHub OIDC provider", "reused read-only: never modified, never deleted"),
    (2, "🔍", "Plan before apply", "0 to change, 0 to destroy, every time"),
    (2, "🧹", "Leave no trace", "teardown the same day, verified against the starting inventory"),
]), [
    S("Let me repeat the rules I followed the whole time, because they matter more than any tool. One region, enforced by Terraform. Every resource named eks devsecops and tagged with the project and the owner.",
      tts="Let me repeat the rules I followed the whole time, because they matter more than any tool. One region, enforced by Terraform. Every resource named E K S dev sec ops and tagged with the project and the owner."),
    S("In IAM, only uniquely named project roles, and never anything unrelated. The shared GitHub identity provider was reused read only: never modified, never deleted.", tts="In I A M, only uniquely named project roles, and never anything unrelated. The shared GitHub identity provider was reused read only: never modified, never deleted."),
    S("Always read the plan before apply. And leave no trace: tear down the same day, and verify it against the inventory you took at the start. We work inside a controlled scope. We only touch resources created for this project."),
])

scene("What you can do now", "Learning outcomes", "You built a production-style EKS DevSecOps platform", grid([
    card(0, "🏗️", "Infrastructure", "VPC, EKS, private nodes, IAM, access entries, Pod Identity, LB controller"),
    card(1, "🐳", "Supply chain", "build, scan, SBOM, cosign, ECR with immutable tags, deploy by digest"),
    card(2, "⚙️", "Pipeline", "OIDC, secrets, dependencies, Dockerfile, Terraform and Kubernetes scans, auto-deploy"),
    card(3, "🔒 🔧", "Operate", "Kubernetes security, an ALB on the internet, troubleshooting by layer"),
    card(4, "🧹", "Clean up", "ordered teardown, verified, shared resources untouched"),
    card(5, "📚", "Repository", "github.com/sufyanahmadkamboh/sufyan-devops-eks-devsecops", "ok"),
], cols=3), [
    S("So, what can you do now? Build an AWS network and an EKS cluster with Terraform, with private nodes, secure IAM, access entries, Pod Identity and the load balancer controller.",
      tts="So, what can you do now? Build an A W S network and an E K S cluster with Terraform, with private nodes, secure I A M, access entries, pod identity and the load balancer controller."),
    S("Build a container, scan it, create its SBOM, sign it, and push it to a registry with immutable tags, then deploy it by digest.", tts="Build a container, scan it, create its S-bom, sign it, and push it to a registry with immutable tags, then deploy it by digest."),
    S("Run a DevSecOps pipeline with OIDC, scanning the code, the dependencies, the Dockerfile, the Terraform, the Kubernetes files and the image, and deploying automatically.",
      tts="Run a dev sec ops pipeline with O I D C, scanning the code, the dependencies, the Dockerfile, the Terraform, the Kubernetes files and the image, and deploying automatically."),
    S("Secure Kubernetes workloads, expose them through an AWS load balancer, and troubleshoot a failing rollout layer by layer."),
    S("And destroy the whole environment safely, and prove that nothing is left."),
    S("Everything is in the repository, with a study guide and hands-on labs. You didn't just watch someone explain EKS DevSecOps. You watched it get built, shipped, broken, fixed, and cleaned up on a real AWS account. "
      "Now build it yourself. Thanks for watching.",
      tts="Everything is in the repository, with a study guide and hands-on labs. You didn't just watch someone explain E K S dev sec ops. You watched it get built, shipped, broken, fixed, and cleaned up on a real AWS account. "
          "Now build it yourself. Thanks for watching."),
])
