# Git-Based Deployment Guide

## 🎯 Overview

This guide shows you how to deploy your Flask app using Git, making it easy to update by simply pushing to your repository.

## 🚀 Benefits of Git-Based Deployment

- ✅ **Easy Updates**: Just `git push` and your app updates automatically
- ✅ **Version Control**: Track all changes and rollback if needed
- ✅ **CI/CD**: Automatic deployment on push (optional)
- ✅ **No File Uploads**: No need to use SCP or manually upload files

## 📋 Setup Options

### Option 1: Manual Git Deployment (Simplest)

Deploy by pulling from Git when you want to update.

### Option 2: Automatic Deployment (Recommended)

Automatically deploy when you push to GitHub using GitHub Actions.

---

## 🛠️ Initial Setup (One-Time)

### Step 1: Connect to Your EC2 Instance

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

### Step 2: Run Git Setup Script

```bash
# Edit the script first to add your Git repository URL
nano deployment/git_setup.sh
```

**Edit these lines:**
```bash
GIT_REPO_URL="https://github.com/your-username/stock_ticker_generator.git"
GIT_BRANCH="main"  # or "master" if that's your default branch
```

**Save and run:**
```bash
chmod +x deployment/git_setup.sh
./deployment/git_setup.sh
```

This will:
- Install all dependencies
- Clone your repository
- Set up PostgreSQL
- Create virtual environment
- Install Python packages

### Step 3: Complete Deployment

```bash
# Run the deployment script
chmod +x deployment/aws_ec2_deploy.sh
./deployment/aws_ec2_deploy.sh
```

---

## 🔄 Manual Deployment (When You Push Updates)

### Method 1: SSH and Deploy

```bash
# Connect to EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Run deployment script
cd /opt/stock_ticker_generator
./deployment/deploy_from_git.sh
```

### Method 2: One-Line Command

From your local machine:

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP "cd /opt/stock_ticker_generator && ./deployment/deploy_from_git.sh"
```

---

## 🤖 Automatic Deployment (GitHub Actions)

### Step 1: Set Up GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Add these secrets:

   **EC2_HOST**: Your EC2 public IP address
   ```
   Example: 54.123.45.67
   ```

   **EC2_SSH_KEY**: Your private key (.pem file content)
   ```
   Copy the entire content of your .pem file
   ```

### Step 2: Enable GitHub Actions

The workflow file is already created at `.github/workflows/deploy.yml`

Just push to your repository and it will automatically deploy!

### Step 3: Test Automatic Deployment

```bash
# Make a small change
echo "# Test" >> README.md

# Commit and push
git add .
git commit -m "Test deployment"
git push origin main
```

GitHub Actions will automatically:
1. Detect the push
2. SSH into your EC2 instance
3. Pull latest code
4. Install dependencies
5. Restart your app

---

## 📝 Workflow Comparison

### Before (Manual Upload):
```bash
# Every time you want to update:
1. Make changes locally
2. scp files to EC2
3. SSH into EC2
4. Manually restart app
```

### Now (Git-Based):
```bash
# Every time you want to update:
1. Make changes locally
2. git push
3. Done! (if using GitHub Actions)
   OR
3. SSH and run: ./deployment/deploy_from_git.sh
```

---

## 🔧 Useful Commands

### Check Deployment Status

```bash
# On EC2
sudo supervisorctl status stock_ticker_app
```

### View Deployment Logs

```bash
# On EC2
sudo tail -f /var/log/stock_ticker_app/access.log
sudo tail -f /var/log/stock_ticker_app/error.log
```

### Manual Git Pull

```bash
# On EC2
cd /opt/stock_ticker_generator
git pull origin main
./deployment/deploy_from_git.sh
```

### Rollback to Previous Version

```bash
# On EC2
cd /opt/stock_ticker_generator
git log  # Find the commit hash you want
git checkout <commit-hash>
./deployment/deploy_from_git.sh
```

---

## 🎯 Recommended Setup

1. **Initial Setup**: Use `git_setup.sh` (one-time)
2. **Automatic Deployment**: Set up GitHub Actions
3. **Manual Fallback**: Use `deploy_from_git.sh` if needed

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** - It contains secrets
2. **Use GitHub Secrets** - Store sensitive data in GitHub Secrets
3. **Restrict SSH access** - Only allow your IP in security group
4. **Use SSH keys** - Never use passwords for SSH

---

## 🚨 Troubleshooting

### GitHub Actions Not Working?

1. Check if workflow file exists: `.github/workflows/deploy.yml`
2. Verify secrets are set correctly
3. Check GitHub Actions logs for errors

### Deployment Fails?

```bash
# Check app logs
sudo tail -f /var/log/stock_ticker_app/error.log

# Check if app is running
sudo supervisorctl status stock_ticker_app

# Restart manually
sudo supervisorctl restart stock_ticker_app
```

### Git Pull Fails?

```bash
# Check if you have uncommitted changes
git status

# Stash changes if needed
git stash
git pull origin main
git stash pop
```

---

## ✅ Checklist

- [ ] Repository is on GitHub
- [ ] EC2 instance is running
- [ ] Ran `git_setup.sh` successfully
- [ ] App is deployed and running
- [ ] GitHub Actions secrets are set (for auto-deploy)
- [ ] Tested manual deployment
- [ ] Tested automatic deployment (if using GitHub Actions)

---

**Now you can deploy with just `git push`! 🎉**

