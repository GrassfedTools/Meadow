terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
  backend "s3" {
    bucket = "meadow-testing-terraform-state-7894313"
    key    = "state"
    region = "eu-west-2"
  }
}

provider "aws" {
  region = "us-east-1"
}

data "aws_caller_identity" "current" {}

module "meadow" {
  source              = "../"
  organisation_name   = "Meadow Testing"
  dynamodb_table_name = "meadow-users"
  zone_id             = "Z0113789CFPZ63JFOFKB"
  domain_name         = "meadow-testing.grassfed.tools"
  region              = "us-east-1"
  honeypot_secret     = "11111111"
  website_domain      = "grassfed.tools"
  account_id          = data.aws_caller_identity.current.account_id
}

output "barn_bucket" {
  value = module.meadow.barn_bucket
}