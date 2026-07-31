provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Application  = var.application_name
      BusinessUnit = var.business_unit
      Environment  = var.environment
      ManagedBy    = "terraform"
      Owner        = var.owner_team
    }
  }
}