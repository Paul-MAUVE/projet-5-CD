provider "aws" {
  region = "eu-west-3"

  default_tags {
    tags = {
      Project   = "OC-P5"
      ManagedBy = "Terraform"
    }
  }
}