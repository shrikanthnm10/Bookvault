# 📚 BookVault — Classic Book Directory App

A Python Flask app with **Amazon RDS (MySQL)** reader reviews system, deployed on **ECS Fargate** via a full **CI/CD pipeline** in **eu-north-1 (Stockholm)**.

---

## 📁 Project Structure

```
bookvault-app/
├── app.py                              # Flask app — books + reviews API + RDS connection
├── requirements.txt                    # flask, pymysql
├── Dockerfile                          # Container definition
├── buildspec.yml                       # AWS CodeBuild — build & push Docker image to ECR
├── appspec.yml                         # AWS CodeDeploy — deploy to EC2/ECS
├── start_container.sh                  # Start Docker container with RDS env vars
├── stop_container.sh                   # Stop & clean old container
├── 01-bookvault-vpc-stack.yaml         # VPC, Subnets, IGW, NAT Gateway
├── 02-bookvault-rds-stack.yaml         # RDS MySQL in private subnets
├── 03-bookvault-alb-stack.yaml         # Application Load Balancer
├── 04-bookvault-ecr-stack.yaml         # ECR Docker image registry
├── 05-bookvault-ecs-stack.yaml         # ECS Fargate cluster + service
├── 06-bookvault-codebuild-stack.yaml   # CodeBuild project
├── 07-bookvault-codepipeline-stack.yaml # CodePipeline (Source → Build → Deploy)
└── README.md
```

---

## 🌍 AWS Region

**eu-north-1 — Stockholm, Sweden**

All stacks, resources, and the CI/CD pipeline are configured for this region.

---

## 🚀 Run Locally

### Step 1 — Start a local MySQL (or use RDS endpoint directly)
```bash
# Option A: Use Docker for local MySQL
docker run -d --name mysql-local \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=BookVaultDB \
  -p 3306:3306 mysql:8

# Option B: Skip DB locally — app will warn but still serve books page
```

### Step 2 — Set environment variables
```bash
export DB_HOST=localhost        # or your RDS endpoint
export DB_USER=root             # or admin
export DB_PASSWORD=root         # your password
export DB_NAME=BookVaultDB
```

### Step 3 — Run the app
```bash
pip install -r requirements.txt
python app.py
```
Visit: **http://localhost:5000**

---

## ☁️ AWS CI/CD Setup — Step by Step

> ⚠️ **Deploy stacks in order!** Some stacks import CloudFormation exports from previous stacks.

### STEP 1 — Deploy VPC Stack
```bash
aws cloudformation deploy \
  --template-file 01-bookvault-vpc-stack.yaml \
  --stack-name bookvault-vpc \
  --region eu-north-1
```

### STEP 2 — Deploy ALB Stack
```bash
aws cloudformation deploy \
  --template-file 03-bookvault-alb-stack.yaml \
  --stack-name bookvault-alb \
  --region eu-north-1
```

### STEP 3 — Deploy ECR Stack
```bash
aws cloudformation deploy \
  --template-file 04-bookvault-ecr-stack.yaml \
  --stack-name bookvault-ecr \
  --region eu-north-1
```

### STEP 4 — Deploy ECS Stack
```bash
aws cloudformation deploy \
  --template-file 05-bookvault-ecs-stack.yaml \
  --stack-name bookvault-ecs \
  --capabilities CAPABILITY_NAMED_IAM \
  --region eu-north-1 \
  --parameter-overrides SecretsManagerArn=arn:aws:secretsmanager:eu-north-1:YOUR_ACCOUNT:secret:bookvault-rds-secret-XXXX
```

### STEP 5 — Deploy RDS Stack
> ⚠️ Deploy RDS **after** ECS so the ECS Security Group export (`bookvault-ecs-sg-id`) exists.
```bash
aws cloudformation deploy \
  --template-file 02-bookvault-rds-stack.yaml \
  --stack-name bookvault-rds \
  --region eu-north-1 \
  --parameter-overrides \
    DBPassword=YourStrongPassword123!
```

### STEP 6 — Store GitHub Token in Secrets Manager
```bash
aws secretsmanager create-secret \
  --name github-token \
  --secret-string '{"token":"ghp_YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"}' \
  --region eu-north-1
```

### STEP 7 — Deploy CodeBuild Stack
```bash
aws cloudformation deploy \
  --template-file 06-bookvault-codebuild-stack.yaml \
  --stack-name bookvault-codebuild \
  --capabilities CAPABILITY_NAMED_IAM \
  --region eu-north-1 \
  --parameter-overrides \
    AWSAccountId=YOUR_12_DIGIT_ACCOUNT_ID \
    GitHubOwner=YOUR_GITHUB_USERNAME \
    GitHubRepo=bookvault-app
```

### STEP 8 — Deploy CodePipeline Stack
```bash
aws cloudformation deploy \
  --template-file 07-bookvault-codepipeline-stack.yaml \
  --stack-name bookvault-pipeline \
  --capabilities CAPABILITY_NAMED_IAM \
  --region eu-north-1 \
  --parameter-overrides \
    GitHubOwner=YOUR_GITHUB_USERNAME \
    GitHubRepo=bookvault-app
```

### STEP 9 — Push & Deploy!
```bash
git add .
git commit -m "initial BookVault deployment"
git push origin main
```
✅ CodePipeline auto-triggers → builds Docker image → pushes to ECR → deploys to ECS!

---

## 🔐 Secrets Manager Setup

Store your RDS password securely (never in plain text!):

```bash
# Create the secret
aws secretsmanager create-secret \
  --name bookvault-rds-secret \
  --secret-string '{"password":"YourStrongPassword123!"}' \
  --region eu-north-1

# Reference in ECS Task Definition via CloudFormation:
# ValueFrom: arn:aws:secretsmanager:eu-north-1:ACCOUNT_ID:secret:bookvault-rds-secret-XXXX
```

---

## 🌐 API Endpoints

| Method | Endpoint      | Description                        |
|--------|---------------|------------------------------------|
| GET    | `/`           | Main book directory UI             |
| GET    | `/health`     | Health check + RDS connectivity    |
| GET    | `/api/books`  | All books as JSON                  |
| POST   | `/review`     | Submit a review → saved to RDS     |
| GET    | `/reviews`    | View all reviews from RDS          |

### POST /review (form data)
```
name    = "Jane Smith"
email   = "jane@example.com"
message = "Absolutely loved reading about these classics!"
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE IF NOT EXISTS reviews (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100)  NOT NULL,
    email      VARCHAR(150)  NOT NULL,
    message    TEXT          NOT NULL,
    created_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);
```
> Table is auto-created on app startup via `init_db()` — no manual SQL needed!

---

## 📋 CloudFormation Stack Deploy Order

| Order | Stack File                        | Stack Name         | Depends On        |
|-------|-----------------------------------|--------------------|-------------------|
| 1     | 01-bookvault-vpc-stack.yaml       | bookvault-vpc      | —                 |
| 2     | 03-bookvault-alb-stack.yaml       | bookvault-alb      | VPC               |
| 3     | 04-bookvault-ecr-stack.yaml       | bookvault-ecr      | —                 |
| 4     | 05-bookvault-ecs-stack.yaml       | bookvault-ecs      | VPC, ALB, ECR     |
| 5     | 02-bookvault-rds-stack.yaml       | bookvault-rds      | VPC, ECS          |
| 6     | 06-bookvault-codebuild-stack.yaml | bookvault-codebuild| ECR               |
| 7     | 07-bookvault-codepipeline-stack.yaml | bookvault-pipeline | CodeBuild, ECS |

---

## 🛠️ Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Backend   | Python 3.11, Flask                |
| Database  | Amazon RDS (MySQL 8), PyMySQL     |
| Container | Docker                            |
| Registry  | Amazon ECR                        |
| Compute   | ECS Fargate (Serverless)          |
| Networking| VPC, ALB, NAT Gateway             |
| CI/CD     | CodePipeline + CodeBuild + ECS    |
| Secrets   | AWS Secrets Manager               |
| Region    | eu-north-1 (Stockholm, Sweden)    |

---

## 🧹 Teardown (Delete All Resources)

Delete stacks in **reverse order** to avoid dependency errors:

```bash
aws cloudformation delete-stack --stack-name bookvault-pipeline --region eu-north-1
aws cloudformation delete-stack --stack-name bookvault-codebuild --region eu-north-1
aws cloudformation delete-stack --stack-name bookvault-rds --region eu-north-1
aws cloudformation delete-stack --stack-name bookvault-ecs --region eu-north-1
aws cloudformation delete-stack --stack-name bookvault-ecr --region eu-north-1
aws cloudformation delete-stack --stack-name bookvault-alb --region eu-north-1
aws cloudformation delete-stack --stack-name bookvault-vpc --region eu-north-1
```
