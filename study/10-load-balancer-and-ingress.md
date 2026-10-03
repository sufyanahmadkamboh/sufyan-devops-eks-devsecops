# 10. Load Balancer Controller and Ingress

## What is it?

- A Kubernetes **Service** gives a group of pods one stable address inside the cluster.
- An **Ingress** describes how HTTP traffic from outside reaches Services ("everything under `/` goes to the Service `profile-card`").
- An Ingress does nothing by itself: an **ingress controller** reads it and makes it real. The **AWS Load Balancer Controller** makes it real as an **Application Load Balancer (ALB)**, a managed HTTP load balancer from AWS.
- **EKS Pod Identity** gives a pod (here the controller) AWS permissions through an IAM role, without any access keys in the cluster.

## Why this project uses it

The ALB is managed, highly available across zones, integrates with AWS certificates and WAF, and the controller keeps it in sync with Kubernetes automatically.

**Alternatives:** a Service of type `LoadBalancer` (a Network Load Balancer per Service), ingress-nginx behind one load balancer, Gateway API implementations.

## How it works

1. Terraform installs the controller with **Helm** (chart 3.5.0, 2 replicas, in `kube-system`).
2. The controller's service account `aws-load-balancer-controller` is linked to the IAM role `eks-devsecops-lb-controller` by a **Pod Identity association**. The role's permissions come from the controller's official policy file for version 3.5.0.
3. The pipeline applies the Ingress. The controller sees `ingressClassName: alb` and creates an ALB, a target group, listeners and security groups.
4. With **target type `ip`**, the ALB sends traffic straight to the **pod IP addresses** (possible because pods have VPC IPs), not through node ports.
5. The ALB is placed in subnets tagged `kubernetes.io/role/elb` (the public subnets, chapter 2).

### Why the nodes block instance metadata, and what that means for the controller

The controller would normally ask the instance metadata service for the VPC ID and region. With the hop limit of 1 (chapter 4) pods cannot reach it, so Terraform passes `vpcId` and `region` to the Helm chart directly.

## Where it is configured

[`terraform/load-balancer-controller.tf`](../terraform/load-balancer-controller.tf):

```hcl
resource "aws_eks_pod_identity_association" "lb_controller" {
  cluster_name    = module.eks.cluster_name
  namespace       = "kube-system"
  service_account = "aws-load-balancer-controller"
  role_arn        = aws_iam_role.lb_controller.arn
}

resource "helm_release" "lb_controller" {
  chart   = "aws-load-balancer-controller"
  version = "3.5.0"
  values = [yamlencode({
    clusterName  = module.eks.cluster_name
    region       = var.region
    vpcId        = module.vpc.vpc_id
    replicaCount = 2
    defaultTags  = local.tags   # the ALB and its security groups get the project tags too
  })]
}
```

[`k8s/ingress.yaml`](../k8s/ingress.yaml):

```yaml
metadata:
  annotations:
    alb.ingress.kubernetes.io/load-balancer-name: eks-devsecops-profile-card
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}]'
    alb.ingress.kubernetes.io/healthcheck-path: /healthz
    alb.ingress.kubernetes.io/target-group-attributes: deregistration_delay.timeout_seconds=10
    alb.ingress.kubernetes.io/load-balancer-attributes: >-
      routing.http.drop_invalid_header_fields.enabled=true,routing.http.desync_mitigation_mode=strictest
spec:
  ingressClassName: alb
```

- `drop_invalid_header_fields` and `desync_mitigation_mode=strictest` protect against HTTP request smuggling at the edge.
- The deregistration delay is explained in chapter 12.

Recorded result: the Ingress got the address `eks-devsecops-profile-card-604868946.eu-central-1.elb.amazonaws.com`, and `curl` returned `HTTP/1.1 200 OK` with all security headers.

### Why HTTP only

HTTPS needs a TLS **certificate**, and a certificate is issued for a **domain name**. This lab has no domain, so it runs on plain HTTP. With a domain you request a certificate from **AWS Certificate Manager (ACM)** and add two annotations (`certificate-arn` and an HTTPS listener with a redirect from HTTP).

### Teardown note

The ALB is created by the **controller**, not by Terraform. If you run `terraform destroy` first, the controller is deleted before it can remove the ALB, and the ALB plus its security groups block the deletion of the VPC. So the teardown deletes the Ingress first (chapter 13).

## Try it

```bash
kubectl -n kube-system get deploy aws-load-balancer-controller
kubectl -n profile-card get ingress profile-card
H=$(kubectl -n profile-card get ingress profile-card -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl -sS -D - -o /dev/null "http://$H/"
aws elbv2 describe-load-balancers --names eks-devsecops-profile-card --query 'LoadBalancers[0].Scheme'
```

## Common mistakes

- Missing subnet tags: the Ingress never gets an address.
- Giving the controller credentials as Kubernetes secrets instead of Pod Identity.
- Forgetting `vpcId`/`region` when IMDS is blocked: the controller cannot start.
- Running `terraform destroy` before deleting the Ingress.

## Check yourself

1. What creates the ALB, Terraform or the controller?
2. What does `target-type: ip` change?
3. What is missing for HTTPS, and how would you add it?

### Answers

<details><summary>Answers</summary>

1. The AWS Load Balancer Controller, when it sees the Ingress. Terraform only installs the controller.
2. The ALB registers the pod IP addresses directly as targets, instead of sending traffic to node ports and through kube-proxy.
3. A domain name and a certificate for it. Request one in ACM, add the certificate ARN and an HTTPS listener (with an HTTP→HTTPS redirect) as Ingress annotations.

</details>

Next: [11. Kubernetes workload security](11-workload-security.md)
