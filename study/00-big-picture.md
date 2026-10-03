# 0. The big picture

## The story in one paragraph

A small website (a profile card written in React) has to go from a developer's laptop to the internet. It should run on **Amazon EKS** (Kubernetes managed by AWS), every change should be **checked and deployed automatically**, and nobody should be able to break in easily. At the end, everything is **deleted**, and the deletion is **proven**. This project does exactly that, and everything in it was really built, attacked and deleted on an AWS account.

## An everyday analogy

Think of a restaurant kitchen:

| Kitchen | This project |
|---|---|
| The building, with a back door for deliveries and a front door for guests | the **VPC**: private subnets (kitchen) and public subnets (front door) |
| The kitchen staff and stoves | the **EKS cluster** and its **worker nodes** |
| The recipe book everyone follows | **Terraform**: the infrastructure written down as code |
| Health inspection before a dish leaves the kitchen | **Trivy** scanning and the CI checks |
| A staff badge that only opens one door, for one shift | **OIDC**: short-lived AWS access for the pipeline, for one namespace |
| The waiter who brings food to guests | the **Application Load Balancer**, created from a Kubernetes **Ingress** |
| Kitchen rules: no fire in the cold room, staff only in their area | **Pod Security** and **NetworkPolicies** |
| Closing time: everything off, doors locked, checklist signed | **teardown** and its **verification script** |

## What happens when a developer pushes code

```
git push ─► GitHub Actions
   CI  (every push and pull request): secret scan, tests, dependency audit, Dockerfile lint,
                                      image scan, Terraform + Kubernetes checks, pipeline checks
   CD  (push to main): job 1 build + scan (no cloud access)
                       job 2 get temporary AWS access (OIDC) → push to ECR → sign → deploy → test
AWS (Frankfurt, eu-central-1)
   VPC with 2 availability zones
     public subnets:  load balancer, NAT gateway
     private subnets: EKS worker nodes (no public IPs) running 2 copies of the app
```

## What was measured

| | Result |
|---|---|
| Build everything with Terraform | 72 resources in 12 min 30 s |
| `git push` to live website | 3 min 37 s |
| First image scan | **blocked**: a real HIGH vulnerability in the base image, then fixed |
| Privileged pod, outbound traffic, stealing node credentials | all refused or blocked |
| Another pod reaching the app directly | **worked** at first, then fixed and blocked |
| Requests during a deployment | 3 of 280 failed, then fixed: 401 of 401 succeeded |
| Delete everything | 72 resources destroyed, verification clean, 62 minutes on AWS in total |

Two attacks found real weaknesses. That is normal and good: the point of testing is to find them before an attacker does. You will learn both fixes in chapters 11 and 12.

## The tools, one line each

| Tool | Job in this project | Chapter |
|---|---|---|
| AWS (IAM, regions, tags) | the cloud account and its rules | 1 |
| Amazon VPC | the private network | 2 |
| Terraform | builds and deletes all AWS resources from code | 3 |
| Amazon EKS | runs Kubernetes for us | 4 |
| React, Vite, Docker, nginx | the app and its container image | 5 |
| Trivy | finds vulnerabilities and misconfigurations | 6 |
| GitHub Actions | runs the checks and the deployment | 7, 9 |
| OIDC, IAM roles, EKS access entries | access without stored keys, least privilege | 8 |
| Amazon ECR, cosign | stores and signs the images | 9 |
| AWS Load Balancer Controller | turns an Ingress into a load balancer | 10 |
| Pod Security, NetworkPolicy | rules for what pods may do | 11 |
| Readiness gates, preStop | deployments without errors | 12 |
| `scripts/teardown.sh` | deletes everything and proves it | 13 |

## Check yourself

1. Where do the worker nodes run, and can someone on the internet reach them?
2. What does the pipeline need to reach AWS, and what is *not* stored anywhere?
3. Why is it good news that two attacks worked at first?

### Answers

<details><summary>Answers</summary>

1. In the private subnets of the VPC, without public IP addresses. Only the load balancer in the public subnets is reachable from the internet.
2. A short-lived token from GitHub (OIDC) that AWS exchanges for temporary credentials. No AWS access key is stored in GitHub.
3. Because they were found and fixed in a test, with measurements, instead of being found by an attacker in production.

</details>

Next: [1. AWS basics for this project](01-aws-basics.md)
