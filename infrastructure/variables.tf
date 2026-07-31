variable "application_name" {
  description = "Name of the production application"
  type        = string
  default     = "inventory-platform"
}

variable "aws_region" {
  description = "AWS Region hosting the production environment"
  type        = string
  default     = "us-east-1"
}

variable "availability_zones" {
  description = "Availability Zones used by the production environment"
  type        = list(string)

  default = [
    "us-east-1a",
    "us-east-1b"
  ]

  validation {
    condition     = length(var.availability_zones) == 2
    error_message = "Exactly two Availability Zones must be provided."
  }
}

variable "business_unit" {
  description = "Business unit supported by the application"
  type        = string
  default     = "ecommerce"
}

variable "environment" {
  description = "Application deployment environment"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "owner_team" {
  description = "Team responsible for the production infrastructure"
  type        = string
  default     = "cloud-operations"
}

variable "source_instance_type" {
  description = "Current EC2 instance type used by the production fleet"
  type        = string
  default     = "t3.micro"

  validation {
    condition     = var.source_instance_type == "t3.micro"
    error_message = "The existing production fleet must initially use t3.micro."
  }
}

variable "subnet_cidrs" {
  description = "CIDR blocks assigned to the production private subnets"
  type        = list(string)

  default = [
    "10.10.1.0/24",
    "10.10.2.0/24"
  ]

  validation {
    condition     = length(var.subnet_cidrs) == 2
    error_message = "Exactly two subnet CIDR blocks must be provided."
  }
}

variable "vpc_cidr" {
  description = "CIDR range assigned to the production VPC"
  type        = string
  default     = "10.10.0.0/16"
}