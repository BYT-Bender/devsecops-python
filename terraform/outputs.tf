output "cluster_name" {
  description = "The name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "The endpoint URL for the EKS Kubernetes API server"
  value       = module.eks.cluster_endpoint
}

output "vpc_id" {
  description = "The ID of the VPC created for the cluster"
  value       = module.vpc.vpc_id
}
