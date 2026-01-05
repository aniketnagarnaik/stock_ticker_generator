#!/bin/bash
###############################################################################
# Quick Health Check Script
# Checks if all services are running properly
###############################################################################

echo "🔍 Checking Application Health..."
echo "================================="

# Check Supervisor status
echo ""
echo "📊 Supervisor Status:"
sudo supervisorctl status stock_ticker_app

# Check if app is responding
echo ""
echo "🌐 Application Response:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:5000 || echo "❌ App not responding on port 5000"

# Check Nginx status
echo ""
echo "🌐 Nginx Status:"
sudo systemctl status nginx --no-pager | head -5

# Check PostgreSQL status
echo ""
echo "🐘 PostgreSQL Status:"
sudo systemctl status postgresql --no-pager | head -5

# Check if database is accessible
echo ""
echo "🗄️  Database Connection:"
sudo -u postgres psql -c "SELECT version();" stocks_db 2>/dev/null && echo "✅ Database accessible" || echo "⚠️  Database check failed"

# Get public IP
echo ""
echo "🌍 Public IP:"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "Your app should be accessible at: http://${PUBLIC_IP}"

echo ""
echo "✅ Health check complete!"


