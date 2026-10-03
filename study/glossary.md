# Glossary

| Term | Meaning |
|---|---|
| **access entry (EKS)** | an EKS API object that gives an IAM principal Kubernetes permissions, optionally scoped to namespaces; replaces the `aws-auth` ConfigMap |
| **actionlint** | a linter for GitHub Actions workflow files |
| **add-on (EKS)** | an AWS-provided cluster component: VPC CNI, CoreDNS, kube-proxy, Pod Identity agent |
| **ALB** | Application Load Balancer: AWS's managed HTTP/HTTPS load balancer |
| **AWS Load Balancer Controller** | a Kubernetes controller that creates ALBs from Ingress objects |
| **availability zone (AZ)** | an isolated data center (or group) inside an AWS region |
| **CIDR** | notation for an IP range, e.g. `10.42.0.0/16` |
| **control plane** | the Kubernetes API server, scheduler and database; run by AWS in EKS |
| **cosign** | Sigstore's tool to sign and verify container images |
| **CSP** | Content-Security-Policy: a response header that tells the browser which scripts and styles it may run |
| **CVE** | the public ID of a known vulnerability |
| **default deny** | a NetworkPolicy that blocks all traffic, so only explicit exceptions are allowed |
| **deregistration delay** | how long an ALB keeps a removed target before forgetting it |
| **digest** | the SHA-256 hash of an image (`sha256:…`); identifies exact content and cannot be moved |
| **ECR** | Elastic Container Registry: AWS's image registry |
| **EKS** | Elastic Kubernetes Service: Kubernetes with an AWS-managed control plane |
| **emptyDir** | a temporary, pod-local directory |
| **environment (GitHub)** | a named deployment target (`production`) with rules, e.g. only the `main` branch |
| **gitleaks** | a scanner for secrets in git history |
| **hadolint** | a linter for Dockerfiles |
| **Helm** | a package manager for Kubernetes; Terraform uses it to install the load balancer controller |
| **hop limit (IMDS)** | how many network hops the IMDSv2 token response may travel; 1 keeps it away from pods |
| **IAM** | Identity and Access Management: users, roles and policies in AWS |
| **IAM role** | an identity without a password whose temporary credentials can be assumed |
| **immutable subject** | GitHub's OIDC subject format with numeric owner and repository IDs |
| **immutable tags (ECR)** | an image tag cannot be overwritten once pushed |
| **IMDS / IMDSv2** | the EC2 instance metadata service; v2 requires a session token |
| **Ingress** | a Kubernetes object describing HTTP routing from outside into Services |
| **internet gateway** | a VPC's connection to the internet |
| **IRSA** | IAM Roles for Service Accounts: the older way to give pods AWS permissions (not used here) |
| **KMS** | Key Management Service: AWS's managed encryption keys |
| **kubeconform** | validates Kubernetes manifests against the official schemas |
| **Kustomize** | builds Kubernetes manifests from a base and edits (here: the image digest) |
| **lateral movement** | an attacker moving from one compromised system to another |
| **least privilege** | every identity gets only the permissions it needs |
| **managed node group** | EC2 worker nodes whose lifecycle EKS manages |
| **multi-stage build** | a Dockerfile that builds in one stage and copies only the result into a small final stage |
| **NAT gateway** | lets private subnets start outbound connections; nothing can connect in |
| **NetworkPolicy** | Kubernetes rules for which traffic pods may receive and send |
| **OIDC** | OpenID Connect: identity with signed tokens; GitHub uses it so jobs can assume AWS roles |
| **Pod Identity (EKS)** | gives a Kubernetes service account an IAM role without keys |
| **Pod Security Admission** | built-in check that enforces `privileged`, `baseline` or `restricted` levels per namespace |
| **preStop hook** | an action Kubernetes runs before stopping a container (here: sleep 15 s) |
| **private / public subnet** | a subnet without / with a route from the internet gateway |
| **readiness gate** | an extra condition a pod must meet before it counts as ready (here: ALB target healthy) |
| **region** | a geographic area of AWS, e.g. `eu-central-1` (Frankfurt) |
| **rolling update** | replacing pods one by one during a deployment |
| **route table** | rules that send a subnet's traffic to a gateway |
| **SBOM** | software bill of materials: the list of components in an image (Syft, CycloneDX) |
| **seccomp** | a Linux filter that blocks dangerous system calls (`RuntimeDefault`) |
| **security group** | an AWS firewall around network interfaces |
| **securityContext** | Kubernetes settings for a pod's or container's privileges |
| **smoke test** | a quick check that the deployed system answers |
| **state (Terraform)** | Terraform's record of the resources it manages |
| **target type ip** | the ALB sends traffic directly to pod IP addresses |
| **trust policy** | the part of an IAM role that says who may assume it |
| **Trivy** | a scanner for vulnerabilities and misconfigurations |
| **version skew** | old and new versions of an app running at the same time and mixing requests |
| **VPC** | Virtual Private Cloud: your private network in AWS |
| **VPC CNI** | the EKS network plugin; gives pods VPC IPs and enforces NetworkPolicies |
| **VPC flow logs** | records of network connections in a VPC |
| **zizmor** | a security auditor for GitHub Actions workflows |
