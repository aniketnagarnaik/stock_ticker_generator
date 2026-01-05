# Remote Deployment Archive

This folder contains all remote hosting and deployment configurations that have been archived for future use.

## Contents

### `aws_ec2/`
All AWS EC2 deployment scripts and documentation:
- **Setup Scripts**: `aws_ec2_setup.sh`, `git_setup.sh`, `add_swap.sh`
- **Deployment Scripts**: `aws_ec2_deploy.sh`, `deploy_from_git.sh`, `health_check.sh`
- **Documentation**: `AWS_EC2_DEPLOYMENT_GUIDE.md`, `GIT_DEPLOYMENT_GUIDE.md`, `QUICK_START.md`

### GitHub Actions Workflows
- **`deploy.yml`**: Automated deployment to AWS EC2 on git push
- **`daily-refresh.yml`**: Daily stock data refresh for remote endpoint

### Render Deployment
- **`RENDER_DEPLOYMENT.md`**: Render.com deployment guide

## When to Use

These files are archived for when you decide to deploy the application to a remote hosting provider. For now, the application is running locally only.

## Restoration

To restore these files for deployment:
1. Copy the contents of `aws_ec2/` back to a `deployment/` folder
2. Move `deploy.yml` and `daily-refresh.yml` back to `.github/workflows/`
3. Move `RENDER_DEPLOYMENT.md` back to `docs/` if needed
4. Follow the respective deployment guides
