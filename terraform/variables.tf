variable "aws_region" {
  description = "AWS region for the demo."
  type        = string
  default     = "ap-south-1"
}
variable "project_name" {
  description = "Prefix for project resources."
  type        = string
  default     = "python-aws-platform-demo"
}
variable "environment" {
  description = "Environment label."
  type        = string
  default     = "learning"
}
variable "lambda_memory_mb" {
  description = "Lambda memory in MB."
  type        = number
  default     = 128
}
variable "lambda_timeout_seconds" {
  description = "Lambda timeout in seconds."
  type        = number
  default     = 5
}
