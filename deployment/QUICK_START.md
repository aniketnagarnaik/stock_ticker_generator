# AWS EC2 Quick Start Guide

## 🚀 Quick Start (5 Minutes)

### 1. Launch EC2 Instance

1. Go to [AWS EC2 Console](https://console.aws.amazon.com/ec2/)
2. Click "Launch Instance"
3. Select:
   - **AMI**: Ubuntu 24.04 LTS (Canonical, Ubuntu, 24.04, amd64 noble image)
   - **Instance Type**: t2.micro (Free tier)
   - **Key Pair**: Create new (download .pem file)
   - **Security Group**: Allow SSH (22), HTTP (80), HTTPS (443)
4. Click "Launch Instance"

### 2. Connect to Instance

```bash
# On your local machine
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### 3. Run Setup

**Option A: Git-Based Setup (Recommended)**
```bash
# Edit git_setup.sh first to add your repository URL
nano deployment/git_setup.sh
# Set GIT_REPO_URL="https://github.com/your-username/repo.git"

# Run Git-based setup
chmod +x deployment/git_setup.sh
./deployment/git_setup.sh
```

**Option B: Manual Upload**
```bash
# Upload your files (from local machine):
scp -i your-key.pem -r /path/to/stock_ticker_generator/* ubuntu@YOUR_IP:/opt/stock_ticker_generator/

# Then run setup
cd /opt/stock_ticker_generator
chmod +x deployment/aws_ec2_setup.sh
./deployment/aws_ec2_setup.sh
```

**⚠️ IMPORTANT**: Edit `aws_ec2_setup.sh` and change PostgreSQL password!

### 4. Deploy App

```bash
chmod +x deployment/aws_ec2_deploy.sh
./deployment/aws_ec2_deploy.sh
```

### 5. Access Your App

Open browser: `http://YOUR_EC2_PUBLIC_IP`

## 📋 What Gets Installed

- ✅ Python 3.11 + pip
- ✅ PostgreSQL 14
- ✅ Nginx (web server)
- ✅ Supervisor (process manager)
- ✅ Certbot (SSL certificates)
- ✅ All Python dependencies

## 🔧 Common Commands

```bash
# Check app status
sudo supervisorctl status stock_ticker_app

# Restart app
sudo supervisorctl restart stock_ticker_app

# View logs
sudo tail -f /var/log/stock_ticker_app/access.log

# Check database
sudo -u postgres psql stocks_db
```

## 💰 Cost

- **Free Tier (12 months)**: $0/month
- **After Free Tier**: ~$8-10/month (t2.micro)

## 🔄 Easy Updates with Git

After initial setup, you can update your app easily:

```bash
# On EC2, run:
cd /opt/stock_ticker_generator
./deployment/deploy_from_git.sh
```

Or set up **automatic deployment** with GitHub Actions - see `GIT_DEPLOYMENT_GUIDE.md`

## 📚 Full Guides

- **Basic Deployment**: `AWS_EC2_DEPLOYMENT_GUIDE.md`
- **Git-Based Deployment**: `GIT_DEPLOYMENT_GUIDE.md` (Recommended!)

