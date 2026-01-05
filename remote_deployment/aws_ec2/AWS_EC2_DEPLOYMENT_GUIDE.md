# AWS EC2 Deployment Guide for Flask + PostgreSQL App

## 🎯 Overview

This guide will help you deploy your Flask + PostgreSQL app on AWS EC2 using the free tier.

## 📋 Prerequisites

- AWS account with free tier access
- Basic knowledge of Linux commands
- Your Flask app code (this repository)

## 🆓 AWS Free Tier Benefits

### What You Get (First 12 Months):
- **EC2 t2.micro**: 750 hours/month (enough for 24/7 operation)
- **EBS Storage**: 30GB free
- **Data Transfer**: 15GB outbound/month
- **Elastic IP**: Free if instance is running

### Cost After Free Tier:
- **t2.micro**: ~$8-10/month
- **t3.small**: ~$15/month (recommended for production)

## 🚀 Step-by-Step Setup

### Step 1: Launch EC2 Instance

1. **Go to EC2 Console**
   - Login to AWS Console
   - Navigate to EC2 → Instances
   - Click "Launch Instance"

2. **Configure Instance**
   - **Name**: `stock-ticker-app`
   - **AMI**: Ubuntu 24.04 LTS (Canonical, Ubuntu, 24.04, amd64 noble image) - Free tier eligible
   - **Instance Type**: t2.micro (Free tier) or t3.small
   - **Key Pair**: Create new or use existing
   - **Network Settings**: 
     - Allow SSH (port 22) from your IP
     - Allow HTTP (port 80) from anywhere
     - Allow HTTPS (port 443) from anywhere
   - **Storage**: 20GB (free tier includes 30GB)

3. **Launch Instance**
   - Click "Launch Instance"
   - Download and save your key pair (.pem file)
   - **Important**: Keep this file secure!

### Step 2: Connect to Your Instance

```bash
# Make key file executable (only first time)
chmod 400 your-key.pem

# Connect to instance
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### Step 3: Initial Server Setup

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Git (if not already installed)
sudo apt-get install -y git
```

### Step 4: Clone Your Repository

```bash
# Create app directory
sudo mkdir -p /opt/stock_ticker_generator
sudo chown $USER:$USER /opt/stock_ticker_generator
cd /opt/stock_ticker_generator

# Clone your repository
git clone https://github.com/your-username/stock_ticker_generator.git .

# Or upload files using SCP from your local machine:
# scp -i your-key.pem -r /path/to/stock_ticker_generator ubuntu@YOUR_EC2_IP:/opt/
```

### Step 5: Run Setup Script

```bash
# Make scripts executable
chmod +x deployment/aws_ec2_setup.sh
chmod +x deployment/aws_ec2_deploy.sh

# Run initial setup
./deployment/aws_ec2_setup.sh
```

**Important**: Edit the setup script and change the PostgreSQL password!

### Step 6: Deploy Your App

```bash
# Make sure you're in the project directory
cd /opt/stock_ticker_generator

# Run deployment script
./deployment/aws_ec2_deploy.sh
```

### Step 7: Configure Environment Variables

Edit the `.env` file:

```bash
nano /opt/stock_ticker_generator/.env
```

Set your environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `POLYGON_API_KEY`: Your Polygon API key (if needed)
- `SECRET_KEY`: Flask secret key (auto-generated)

### Step 8: Initialize Database

```bash
cd /opt/stock_ticker_generator
source venv/bin/activate

# Set database URL
export DATABASE_URL="postgresql://flask_user:YOUR_PASSWORD@localhost:5432/stocks_db"

# Initialize database (creates tables)
python3 -c "from database.database import db_manager; print('Database ready')"
```

### Step 9: Set Up SSL (Optional but Recommended)

If you have a domain name:

```bash
sudo certbot --nginx -d your-domain.com
```

This will:
- Get free SSL certificate from Let's Encrypt
- Configure Nginx for HTTPS
- Set up auto-renewal

## 🔧 Useful Commands

### Application Management

```bash
# Check app status
sudo supervisorctl status stock_ticker_app

# Restart app
sudo supervisorctl restart stock_ticker_app

# View app logs
sudo tail -f /var/log/stock_ticker_app/access.log
sudo tail -f /var/log/stock_ticker_app/error.log

# Stop app
sudo supervisorctl stop stock_ticker_app

# Start app
sudo supervisorctl start stock_ticker_app
```

### Database Management

```bash
# Connect to PostgreSQL
sudo -u postgres psql stocks_db

# Backup database
pg_dump -U flask_user stocks_db > backup.sql

# Restore database
psql -U flask_user stocks_db < backup.sql
```

### Nginx Management

```bash
# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# View Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### System Management

```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check running processes
htop

# Update system
sudo apt-get update && sudo apt-get upgrade -y
```

## 🔒 Security Best Practices

1. **Change Default Passwords**
   - PostgreSQL password
   - SSH key (use key-based auth, not passwords)

2. **Configure Firewall**
   ```bash
   sudo ufw status
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   ```

3. **Regular Updates**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

4. **Backup Database Regularly**
   ```bash
   # Add to crontab for daily backups
   crontab -e
   # Add: 0 2 * * * pg_dump -U flask_user stocks_db > /backups/backup_$(date +\%Y\%m\%d).sql
   ```

## 📊 Monitoring

### Check Application Health

```bash
# Check if app is running
curl http://localhost:5000/api/health

# Check database connection
sudo -u postgres psql -c "SELECT version();"
```

### Monitor Resources

```bash
# CPU and Memory
htop

# Disk usage
df -h

# Network
sudo netstat -tulpn
```

## 🚨 Troubleshooting

### App Not Starting

```bash
# Check Supervisor logs
sudo tail -f /var/log/stock_ticker_app/error.log

# Check if port is in use
sudo netstat -tulpn | grep 5000

# Restart Supervisor
sudo supervisorctl restart stock_ticker_app
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
sudo -u postgres psql -l

# Test connection
psql -U flask_user -d stocks_db -h localhost
```

### Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

## 💰 Cost Management

### Monitor AWS Costs

1. **Set Up Billing Alerts**
   - Go to AWS Billing Dashboard
   - Set up CloudWatch billing alarms
   - Get alerts at 50%, 75%, 90%, 100% of budget

2. **Check Free Tier Usage**
   - Go to AWS Billing → Free Tier
   - Monitor EC2 hours used
   - Monitor EBS storage used

3. **Optimize Costs**
   - Use t2.micro during free tier
   - Stop instance when not in use (if testing)
   - Use Elastic IP (free if instance running)

## 📝 Next Steps

1. **Set Up Domain** (optional)
   - Point domain to EC2 Elastic IP
   - Configure SSL with Let's Encrypt

2. **Set Up Backups**
   - Automated database backups
   - Store backups in S3 (free tier: 5GB)

3. **Set Up Monitoring**
   - CloudWatch alarms
   - Application health checks

4. **Set Up CI/CD** (optional)
   - GitHub Actions
   - Auto-deploy on push

## 🆘 Getting Help

- **AWS Support**: Basic support is free
- **Documentation**: Check AWS EC2 docs
- **Community**: AWS forums, Stack Overflow

## ✅ Checklist

- [ ] EC2 instance launched
- [ ] Connected via SSH
- [ ] Setup script run
- [ ] PostgreSQL configured
- [ ] App deployed
- [ ] Nginx configured
- [ ] Firewall configured
- [ ] SSL certificate (if domain)
- [ ] Backups configured
- [ ] Monitoring set up

---

**Congratulations! Your Flask app is now running on AWS EC2! 🎉**

