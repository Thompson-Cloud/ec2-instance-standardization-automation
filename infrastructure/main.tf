###############################################################################
# Production fleet definition
###############################################################################

locals {
  production_instances = {
    "inventory-web-01" = {
      role         = "web"
      subnet_index = 0
    }

    "inventory-web-02" = {
      role         = "web"
      subnet_index = 1
    }

    "inventory-web-03" = {
      role         = "web"
      subnet_index = 0
    }

    "inventory-api-01" = {
      role         = "api"
      subnet_index = 0
    }

    "inventory-api-02" = {
      role         = "api"
      subnet_index = 1
    }

    "inventory-api-03" = {
      role         = "api"
      subnet_index = 0
    }

    "inventory-api-04" = {
      role         = "api"
      subnet_index = 1
    }

    "inventory-api-05" = {
      role         = "api"
      subnet_index = 0
    }

    "inventory-worker-01" = {
      role         = "worker"
      subnet_index = 0
    }

    "inventory-worker-02" = {
      role         = "worker"
      subnet_index = 1
    }

    "inventory-cache-01" = {
      role         = "cache"
      subnet_index = 0
    }

    "inventory-cache-02" = {
      role         = "cache"
      subnet_index = 1
    }

    "inventory-report-01" = {
      role         = "reporting"
      subnet_index = 0
    }

    "inventory-report-02" = {
      role         = "reporting"
      subnet_index = 1
    }

    "inventory-report-03" = {
      role         = "reporting"
      subnet_index = 1
    }
  }
}

###############################################################################
# Amazon Linux AMI
###############################################################################

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

###############################################################################
# Networking
###############################################################################

resource "aws_vpc" "production" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.application_name}-${var.environment}-vpc"
  }
}

resource "aws_subnet" "private" {
  count = length(var.subnet_cidrs)

  availability_zone       = var.availability_zones[count.index]
  cidr_block              = var.subnet_cidrs[count.index]
  map_public_ip_on_launch = false
  vpc_id                  = aws_vpc.production.id

  tags = {
    Name = format(
      "%s-%s-private-%s",
      var.application_name,
      var.environment,
      substr(var.availability_zones[count.index], -1, 1)
    )

    NetworkTier = "private"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.production.id

  tags = {
    Name = "${var.application_name}-${var.environment}-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  route_table_id = aws_route_table.private.id
  subnet_id      = aws_subnet.private[count.index].id
}

###############################################################################
# Security
###############################################################################

resource "aws_security_group" "application" {
  name        = "${var.application_name}-${var.environment}-application-sg"
  description = "Security group for internal production application servers"
  vpc_id      = aws_vpc.production.id

  tags = {
    Name = "${var.application_name}-${var.environment}-application-sg"
  }
}

resource "aws_vpc_security_group_egress_rule" "application_outbound" {
  security_group_id = aws_security_group.application.id

  cidr_ipv4   = "0.0.0.0/0"
  description = "Permit application-initiated outbound traffic"
  ip_protocol = "-1"

  tags = {
    Name = "${var.application_name}-${var.environment}-outbound"
  }
}

###############################################################################
# Production EC2 fleet
###############################################################################

resource "aws_instance" "application" {
  for_each = local.production_instances

  ami                         = data.aws_ami.amazon_linux.id
  associate_public_ip_address = false
  instance_type               = var.source_instance_type

  subnet_id = aws_subnet.private[
    each.value.subnet_index
  ].id

  vpc_security_group_ids = [
    aws_security_group.application.id
  ]

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    delete_on_termination = true
    encrypted             = true
    volume_size           = 8
    volume_type           = "gp3"

    tags = {
      Name = "${each.key}-root"
    }
  }

  tags = {
    Name            = each.key
    ApplicationRole = each.value.role
    Backup          = "required"
    BusinessService = "inventory-management"
    CostCenter      = "cc-ecommerce-001"
    DataClass       = "internal"
    PatchGroup      = "production-linux"
  }
}