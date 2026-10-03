# Network: two availability zones. Worker nodes live in private subnets (no public IPs);
# only the load balancer lives in the public subnets.
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.7.3"

  name = local.name
  cidr = "10.42.0.0/16"
  azs  = slice(data.aws_availability_zones.available.names, 0, 2)

  private_subnets = ["10.42.0.0/20", "10.42.16.0/20"]
  public_subnets  = ["10.42.48.0/24", "10.42.49.0/24"]

  # One NAT gateway keeps the lab cheap. Production: one per AZ (single_nat_gateway = false).
  enable_nat_gateway = true
  single_nat_gateway = true

  # Subnet discovery for the AWS Load Balancer Controller.
  public_subnet_tags  = { "kubernetes.io/role/elb" = 1 }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = 1 }

  # The default security group of this VPC allows nothing.
  manage_default_security_group  = true
  default_security_group_ingress = []
  default_security_group_egress  = []

  # VPC flow logs: who talked to whom, for investigations.
  enable_flow_log                                 = true
  create_flow_log_cloudwatch_log_group            = true
  create_flow_log_cloudwatch_iam_role             = true
  flow_log_max_aggregation_interval               = 60
  flow_log_cloudwatch_log_group_retention_in_days = 7
}
