# AWS Load Balancer Controller: turns the app's Ingress into an Application Load Balancer.
# It gets AWS permissions through EKS Pod Identity: no access keys in the cluster.

resource "aws_iam_policy" "lb_controller" {
  name        = "${local.name}-lb-controller"
  description = "AWS Load Balancer Controller v3.5.0 (upstream docs/install/iam_policy.json)"
  policy      = file("${path.module}/policies/aws-load-balancer-controller-v3.5.0.json")
}

data "aws_iam_policy_document" "pod_identity_trust" {
  statement {
    actions = ["sts:AssumeRole", "sts:TagSession"]
    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lb_controller" {
  name               = "${local.name}-lb-controller"
  assume_role_policy = data.aws_iam_policy_document.pod_identity_trust.json
}

resource "aws_iam_role_policy_attachment" "lb_controller" {
  role       = aws_iam_role.lb_controller.name
  policy_arn = aws_iam_policy.lb_controller.arn
}

resource "aws_eks_pod_identity_association" "lb_controller" {
  cluster_name    = module.eks.cluster_name
  namespace       = "kube-system"
  service_account = "aws-load-balancer-controller"
  role_arn        = aws_iam_role.lb_controller.arn
}

resource "helm_release" "lb_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  version    = "3.5.0"
  namespace  = "kube-system"
  wait       = true

  values = [yamlencode({
    clusterName  = module.eks.cluster_name
    region       = var.region
    vpcId        = module.vpc.vpc_id # nodes block instance metadata, so tell the controller directly
    replicaCount = 2
    serviceAccount = {
      create = true
      name   = "aws-load-balancer-controller"
    }
    # Load balancers and security groups created by the controller carry the project tags too.
    defaultTags = local.tags
  })]

  depends_on = [aws_eks_pod_identity_association.lb_controller, module.eks]
}
