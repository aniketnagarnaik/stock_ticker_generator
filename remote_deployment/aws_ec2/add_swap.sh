#!/bin/bash
###############################################################################
# Add Swap Space to EC2 Instance
# This helps with DuckDB memory requirements
###############################################################################

set -e  # Exit on any error

echo "💾 Adding Swap Space to EC2 Instance"
echo "====================================="

# Check current swap
echo "📊 Current Memory Status:"
free -h

# Check if swap already exists
if [ -f /swapfile ]; then
    echo "⚠️  Swap file already exists. Removing old one..."
    sudo swapoff /swapfile 2>/dev/null || true
    sudo rm -f /swapfile
fi

# Create 2GB swap file
echo ""
echo "🔧 Creating 2GB swap file..."
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make it permanent
echo ""
echo "💾 Making swap permanent..."
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify
echo ""
echo "✅ Swap space added successfully!"
echo ""
echo "📊 New Memory Status:"
free -h

echo ""
echo "🎉 Done! Your instance now has 2GB of swap space."
echo "   This should help with DuckDB memory requirements."


