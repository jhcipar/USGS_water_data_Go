terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
    # redshift = {
    #   source  = "brainly/redshift"
    #   version = "1.0.2"
    # }
  }

  required_version = ">= 1.1.0"
}

provider "aws" {
  region  = var.aws_region
  profile = "default"
}

# Create s3 bucket
resource "aws_s3_bucket" "stock-data-lake" {
  bucket_prefix = var.bucket_prefix
  force_destroy = true
}

# Create s3 bucket access control list for s3 bucket
resource "aws_s3_bucket_acl" "stock-data-lake-acl" {
  bucket = aws_s3_bucket.stock-data-lake.id
  acl    = "private"
}