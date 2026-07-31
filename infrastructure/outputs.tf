output "application_instance_ids" {
  description = "Map of production instance names to EC2 instance IDs"

  value = {
    for name, instance in aws_instance.application :
    name => instance.id
  }
}

output "application_instance_roles" {
  description = "Map of production instance names to application roles"

  value = {
    for name, configuration in local.production_instances :
    name => configuration.role
  }
}

output "application_security_group_id" {
  description = "Security group attached to the production application fleet"
  value       = aws_security_group.application.id
}

output "availability_zones" {
  description = "Availability Zones hosting the production application"
  value       = var.availability_zones
}

output "current_instance_type" {
  description = "Current instance type used by the production fleet"
  value       = var.source_instance_type
}

output "instance_names" {
  description = "Names of all production EC2 instances"
  value       = sort(keys(aws_instance.application))
}

output "private_subnet_ids" {
  description = "IDs of the production private subnets"
  value       = aws_subnet.private[*].id
}

output "production_vpc_id" {
  description = "ID of the production VPC"
  value       = aws_vpc.production.id
}

output "role_summary" {
  description = "Number of EC2 instances assigned to each application role"

  value = {
    web = length([
      for instance in values(local.production_instances) :
      instance if instance.role == "web"
    ])

    api = length([
      for instance in values(local.production_instances) :
      instance if instance.role == "api"
    ])

    worker = length([
      for instance in values(local.production_instances) :
      instance if instance.role == "worker"
    ])

    cache = length([
      for instance in values(local.production_instances) :
      instance if instance.role == "cache"
    ])

    reporting = length([
      for instance in values(local.production_instances) :
      instance if instance.role == "reporting"
    ])
  }
}

output "total_instance_count" {
  description = "Total number of production EC2 instances"
  value       = length(aws_instance.application)
}