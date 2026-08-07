module "vpc" {
  source       = "./modules/vpc"
  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
}

module "eks" {
  source       = "./modules/eks"
  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
  subnet_ids   = module.vpc.private_subnet_ids
}

module "rds" {
  source            = "./modules/rds"
  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.private_subnet_ids
  db_password       = var.db_password
  eks_sg_id         = module.eks.node_security_group_id
}
