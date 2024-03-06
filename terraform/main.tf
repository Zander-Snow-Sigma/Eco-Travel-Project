terraform {
  required_providers {
    mongodbatlas = {
      source = "mongodb/mongodbatlas"
      version = "1.15.1"
    }
  }
}

provider "mongodbatlas" {
  public_key = var.PUBLIC_KEY
  private_key = var.PRIVATE_KEY
}

resource "mongodbatlas_project" "GreenRoute" {
  name = "GreenRoute"
  org_id = var.ORG_ID
}

resource "mongodbatlas_project_ip_access_list" "GreenRouteIpAccessList" {
  project_id = mongodbatlas_project.GreenRoute.id
  cidr_block = "0.0.0.0/0"
}

resource "mongodbatlas_cluster" "GreenRouteCluster" {
  project_id              = mongodbatlas_project.GreenRoute.id
  name                    = "GreenRoute"

  provider_name = "TENANT"
  backing_provider_name = "AWS"
  provider_region_name = var.AWS_REGION
  provider_instance_size_name = "M0"
}

resource "mongodbatlas_database_user" "GreenRouteUser" {
  username = var.DB_USERNAME
  password = var.DB_PASSWORD
  project_id = mongodbatlas_project.GreenRoute.id
  auth_database_name = "admin"
  roles {
    role_name = "readWrite"
    database_name = "admin"
  }
  scopes {
    name = mongodbatlas_cluster.GreenRouteCluster.name
    type = "CLUSTER"
  }
}