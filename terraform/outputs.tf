output "function_name" {
  description = "Deployed Lambda function name."
  value       = aws_lambda_function.app.function_name
}
output "function_url" {
  description = "Public HTTPS endpoint; anyone with the URL can invoke it."
  value       = aws_lambda_function_url.app.function_url
}
output "cloudwatch_log_group" {
  description = "Lambda CloudWatch log group."
  value       = aws_cloudwatch_log_group.lambda.name
}
