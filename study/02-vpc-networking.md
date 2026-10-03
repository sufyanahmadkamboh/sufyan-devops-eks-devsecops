# 2. VPC networking

## What is it?

A **VPC** (Virtual Private Cloud) is your own private network inside AWS. You choose its address range and split it into **subnets**.

| Part | Job |
|---|---|
| **CIDR block** | the address range, written like `10.42.0.0/16` (65,536 addresses starting at 10.42.0.0) |
| **Subnet** | a slice of the VPC inside **one** availability zone |
| **Internet gateway (IGW)** | the VPC's door to the internet |
| **Public subnet** | a subnet whose route table sends internet traffic to the IGW |
| **Private subnet** | a subnet with no route from the internet |
| **NAT gateway** | lets private machines *start* connections to the internet (to download images), while nothing can connect *in* |
| **Route table** | the rules "traffic for X goes to Y" for a subnet |
| **Security group (SG)** | a firewall around a network interface: which traffic may come in and go out |
| **VPC flow logs** | records of every connection: source, destination, port, accepted or rejected |

## Why this project uses it

The worker nodes that run the app should **not** be on the internet. Only the load balancer should be. So:

- **Private subnets** hold the nodes and the pods. They have no public IP addresses.
- **Public subnets** hold only the Application Load Balancer and the NAT gateway.
- The **NAT gateway** lets the nodes pull container images and updates.

## How it works

```
                  internet
                     │
              Internet gateway
                     │
  ┌──────── public subnets (10.42.48.0/24, 10.42.49.0/24) ────────┐
  │   Application Load Balancer          NAT gateway              │
  └───────────────│─────────────────────────▲─────────────────────┘
                  ▼ (HTTP to pod IPs)        │ (outbound only)
  ┌──────── private subnets (10.42.0.0/20, 10.42.16.0/20) ────────┐
  │   EKS worker nodes and pods (no public IPs)                    │
  └────────────────────────────────────────────────────────────────┘
```

- The public subnets' route table: `0.0.0.0/0 → internet gateway`.
- The private subnets' route table: `0.0.0.0/0 → NAT gateway`.
- **One NAT gateway** keeps the lab cheap. In production you use one per availability zone, so losing a zone does not cut off the other zone's internet access.

### Subnet tags for load balancers

The AWS Load Balancer Controller (chapter 10) needs to know where to put load balancers. It looks for tags:
- `kubernetes.io/role/elb = 1` on public subnets (internet-facing load balancers)
- `kubernetes.io/role/internal-elb = 1` on private subnets (internal load balancers)

### An important EKS detail for later

With the **VPC CNI** (the network plugin of EKS), **pods get IP addresses from the VPC's private subnets**. In this project the two app pods had the IPs 10.42.8.223 and 10.42.18.155. That matters in chapter 11: a firewall rule that says "allow the VPC" also allows every pod in the cluster.

## Where it is configured

[`terraform/vpc.tf`](../terraform/vpc.tf) (community module `terraform-aws-modules/vpc/aws`, version 6.7.3):

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.7.3"

  name = local.name
  cidr = "10.42.0.0/16"
  azs  = slice(data.aws_availability_zones.available.names, 0, 2)

  private_subnets = ["10.42.0.0/20", "10.42.16.0/20"]
  public_subnets  = ["10.42.48.0/24", "10.42.49.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  public_subnet_tags  = { "kubernetes.io/role/elb" = 1 }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = 1 }

  manage_default_security_group  = true
  default_security_group_ingress = []
  default_security_group_egress  = []

  enable_flow_log                                 = true
  create_flow_log_cloudwatch_log_group            = true
  create_flow_log_cloudwatch_iam_role             = true
  flow_log_max_aggregation_interval               = 60
  flow_log_cloudwatch_log_group_retention_in_days = 7
}
```

Two security habits are in there:
- The VPC's **default security group allows nothing**, so nothing accidentally attached to it is open.
- **Flow logs** record connections every 60 seconds, kept for 7 days, which you will want during an investigation.

## Try it

After `terraform apply` (lab 6):

```bash
aws ec2 describe-subnets --filters Name=tag:Project,Values=eks-devsecops \
  --query 'Subnets[].[CidrBlock,AvailabilityZone,MapPublicIpOnLaunch]' --output table
kubectl get nodes -o wide        # EXTERNAL-IP must be <none>
```

## Common mistakes

- Putting worker nodes in public subnets "to make it work". Use a NAT gateway instead.
- Forgetting the subnet tags: the load balancer controller cannot find a subnet and the Ingress stays without an address.
- Choosing a CIDR that overlaps with a network you may connect to later (office VPN, another VPC).
- Assuming a security group or "the VPC CIDR" separates pods: on EKS, pod IPs are VPC IPs.

## Check yourself

1. What is the difference between an internet gateway and a NAT gateway?
2. Why do the private subnets need a NAT gateway at all?
3. What would break if the public subnets had no `kubernetes.io/role/elb` tag?

### Answers

<details><summary>Answers</summary>

1. The internet gateway allows traffic in both directions for resources with public IPs. A NAT gateway only lets private resources start outgoing connections; nothing from the internet can connect in through it.
2. The nodes must download container images (ECR), reach the EKS API and other AWS services, and fetch OS updates.
3. The AWS Load Balancer Controller would not find a subnet for an internet-facing load balancer, so the Ingress would get no address.

</details>

Next: [3. Terraform](03-terraform.md)
