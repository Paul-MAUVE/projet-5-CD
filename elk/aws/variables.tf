variable "opensearch_master_username" {
  description = "Identifiant administrateur OpenSearch"
  type        = string
  default     = "oc-p5-admin"
}

variable "opensearch_master_password" {
  description = "Mot de passe administrateur OpenSearch"
  type        = string
  sensitive   = true
}

variable "allowed_ip" {
  description = "Adresse IPv4 publique autorisée à accéder à OpenSearch"
  type        = string
}