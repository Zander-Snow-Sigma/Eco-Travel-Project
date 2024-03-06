variable "PUBLIC_KEY" {
  description = "The public key for a MongoDB account."
  type = string
}

variable "PRIVATE_KEY" {
  description = "The private key for a MongoDB account."
  type = string
}

variable "ORG_ID" {
  description = "The ID of the MongoDB organisation."
  type = string
}

variable "AWS_REGION" {
  description = "The AWS region where the MongoDB cluster will be deployed."
  type = string
}

variable "DB_USERNAME" {
  description = "Username for database access."
  type = string
}

variable "DB_PASSWORD" {
  description = "Password for database access."
  type = string
}