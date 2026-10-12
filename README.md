# Python AWS Platform Demo

A low-cost end-to-end project for Python, GitHub, GitHub Actions, Terraform, AWS IAM OIDC, Lambda, Function URLs, and CloudWatch Logs.

## Architecture
Pull request -> CI checks -> merge to `main` -> GitHub `production` environment -> OIDC -> AWS IAM role -> Terraform -> Lambda + public Function URL + CloudWatch Logs.

**Security:** The Function URL is public (`AuthType = NONE`) for learning only. Do not put secrets or sensitive data in this demo. Remove it when finished.

## Prerequisites
- Git, GitHub account, Python 3.12, AWS CLI v2, Terraform >= 1.10
- AWS account and billing alerts
- An AWS identity allowed to create the backend bucket, IAM OIDC provider/role/policy, and demo resources
- Example region: `ap-south-1` (Mumbai)

## 1. Create GitHub repo
Create an empty repo named `python-aws-platform-demo`, unzip this project, then:

```bash
git init
git add .
git commit -m "Initial Python AWS platform demo"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_OWNER/python-aws-platform-demo.git
git push -u origin main
```

## 2. Create remote Terraform state bucket
Configure AWS CLI locally with an administrator/deployment setup identity, then choose a globally unique bucket name:

```bash
aws sts get-caller-identity
aws configure
export AWS_REGION=ap-south-1
export STATE_BUCKET="YOUR-UNIQUE-terraform-state-bucket"
aws s3api create-bucket --bucket "$STATE_BUCKET" --region "$AWS_REGION" --create-bucket-configuration LocationConstraint="$AWS_REGION"
aws s3api put-public-access-block --bucket "$STATE_BUCKET" --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-versioning --bucket "$STATE_BUCKET" --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket "$STATE_BUCKET" --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
```

Create `terraform/backend.hcl` locally (ignored by Git):

```hcl
bucket       = "YOUR-UNIQUE-terraform-state-bucket"
key          = "python-aws-platform-demo/terraform.tfstate"
region       = "ap-south-1"
encrypt      = true
use_lockfile = true
```

## 3. Set up AWS OIDC (no static AWS keys)
In AWS Console, go to **IAM -> Identity providers -> Add provider**:
- Provider type: OpenID Connect
- URL: `https://token.actions.githubusercontent.com`
- Audience: `sts.amazonaws.com`
If it already exists, reuse it.

Create an IAM role for **Web identity**, then set this trust policy. Replace `YOUR_AWS_ACCOUNT_ID` and `YOUR_GITHUB_OWNER`; the repo and environment names must match exactly:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::YOUR_AWS_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_OWNER/python-aws-platform-demo:environment:production"
      }
    }
  }]
}
```

Attach a custom permissions policy to that role. Replace account ID and bucket placeholders. This is a teaching policy scoped to the project names; review and adjust only when an AWS `AccessDenied` error identifies a missing action.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::YOUR-UNIQUE-terraform-state-bucket"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": [
        "arn:aws:s3:::YOUR-UNIQUE-terraform-state-bucket/python-aws-platform-demo/terraform.tfstate",
        "arn:aws:s3:::YOUR-UNIQUE-terraform-state-bucket/python-aws-platform-demo/terraform.tfstate.tflock"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction", "lambda:DeleteFunction", "lambda:GetFunction",
        "lambda:GetFunctionConfiguration", "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration", "lambda:TagResource",
        "lambda:UntagResource", "lambda:ListTags",
        "lambda:CreateFunctionUrlConfig", "lambda:DeleteFunctionUrlConfig",
        "lambda:GetFunctionUrlConfig", "lambda:UpdateFunctionUrlConfig",
        "lambda:AddPermission", "lambda:RemovePermission", "lambda:GetPolicy"
      ],
      "Resource": "arn:aws:lambda:ap-south-1:YOUR_AWS_ACCOUNT_ID:function:python-aws-platform-demo*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole", "iam:DeleteRole", "iam:GetRole",
        "iam:UpdateAssumeRolePolicy", "iam:TagRole", "iam:UntagRole",
        "iam:AttachRolePolicy", "iam:DetachRolePolicy", "iam:ListAttachedRolePolicies",
        "iam:PutRolePolicy", "iam:DeleteRolePolicy", "iam:GetRolePolicy",
        "iam:ListRolePolicies", "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/python-aws-platform-demo*"
    },
    {
      "Effect": "Allow",
      "Action": ["iam:GetPolicy", "iam:GetPolicyVersion"],
      "Resource": "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup", "logs:DeleteLogGroup", "logs:PutRetentionPolicy",
        "logs:DescribeLogGroups", "logs:ListTagsForResource", "logs:TagResource",
        "logs:UntagResource"
      ],
      "Resource": "arn:aws:logs:ap-south-1:YOUR_AWS_ACCOUNT_ID:log-group:/aws/lambda/python-aws-platform-demo*"
    }
  ]
}
```

Keep `iam:PassRole` limited to the demo Lambda execution role. IAM requirements can vary with provider/API versions; if `apply` returns `AccessDenied`, add only the specific missing permission. Never broaden the OIDC trust subject to all repositories.

## 4. Configure GitHub
In **Settings -> Environments**, create `production`. Add required reviewers and restrict branches to `main` if your GitHub plan/settings support it.

Under **Settings -> Secrets and variables -> Actions -> Variables**, add:
- `AWS_ROLE_ARN`: `arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/YOUR_DEPLOYMENT_ROLE_NAME`
- `AWS_REGION`: `ap-south-1`
- `TF_STATE_BUCKET`: the bucket name

These values are not credentials. Do not add static AWS access keys.

## 5. Run the pipeline
1. Open a pull request to `main`. CI runs linting, unit tests, Terraform formatting, initialization without a backend, and validation.
2. Merge to `main`.
3. The deploy workflow requests short-lived AWS credentials through OIDC, packages the app, initializes Terraform with the S3 backend, plans, applies, and curls the endpoint.
4. Open the Function URL printed in workflow logs. Try `/?name=Prudhvi`.

## 6. Test locally
```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
ruff check app tests
terraform -chdir=terraform fmt -check -recursive
terraform -chdir=terraform init -backend-config=backend.hcl
terraform -chdir=terraform validate
terraform -chdir=terraform plan
```

Do not run local `terraform apply` while GitHub Actions is deploying.

## 7. Verify and troubleshoot
```bash
curl "$(terraform -chdir=terraform output -raw function_url)"
curl "$(terraform -chdir=terraform output -raw function_url)?name=Prudhvi"
```
Check CloudWatch log group `/aws/lambda/python-aws-platform-demo`.

## 8. Clean up
From repo root:

```bash
terraform -chdir=terraform init -backend-config=backend.hcl
terraform -chdir=terraform destroy
```

Review the destroy plan first. Then, only if no longer needed, delete the state bucket. Because versioning is enabled, remove all object versions and delete markers before deleting the bucket. Remove the deployment role/OIDC provider only if no other workload uses them. Check AWS Billing after cleanup.

## Extensions after the baseline works
1. Add Python endpoints and unit tests.
2. Add variables, outputs, and resource tags.
3. Separate plan/apply jobs and require an approval gate.
4. Add a dev environment with a separate state key and role.
5. Add Bandit and Checkov security scans.
6. Add Docker as a local extension; ECS is a separate, potentially billable deployment.
7. Add alarms only after checking pricing.
