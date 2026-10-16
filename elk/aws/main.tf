terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-west-3"
}

resource "aws_opensearch_domain" "oc_p5_elk" {
  domain_name    = "oc-p5-elk"
  engine_version = "Elasticsearch_7.10"

  cluster_config {
    instance_type = "t3.small.search"
  }

  ebs_options {
    ebs_enabled = true
    volume_size = 10
    volume_type = "gp3"
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  advanced_security_options {
    enabled                        = true
    internal_user_database_enabled = true

    master_user_options {
      master_user_name     = var.opensearch_master_username
      master_user_password = var.opensearch_master_password
    }
  }

  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowHTTPFromMyIP"
        Effect    = "Allow"
        Principal = "*"
        Action    = "es:ESHttp*"
        Resource  = "arn:aws:es:eu-west-3:617711904835:domain/oc-p5-elk/*"

        Condition = {
          IpAddress = {
            "aws:SourceIp" = var.allowed_ip
          }
        }
      }
    ]
  })

  tags = {
    Project = "OC-P5"
    Name    = "oc-p5-elk"
  }
}

output "elasticsearch" {
  description = "URL de la base de données ElasticSearch"
  value       = aws_opensearch_domain.oc_p5_elk.endpoint
}

output "kibana" {
  description = "URL de connexion à l'instance Kibana"
  value       = aws_opensearch_domain.oc_p5_elk.dashboard_endpoint
}
