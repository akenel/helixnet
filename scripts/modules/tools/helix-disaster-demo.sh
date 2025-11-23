#!/bin/bash
# disaster-demo.sh

echo "💥 SIMULATED DISASTER SCENARIO 💥"
echo "---------------------------------"
echo "Oh no! The VELIX system has experienced:"
echo "❌ Database corruption"
echo "❌ Configuration loss"
echo "❌ Service outage"
echo ""
echo "Time to demonstrate recovery!"

# Simulate damage
echo -e "\n🔧 Simulating system damage..."
docker stop postgres redis
docker rm postgres redis
echo "✅ Damage simulated!"

# Show recovery instructions
echo -e "\n🔧 INSERT YOUR BACKUP USB DRIVE NOW"
read -p "Press Enter when USB is connected..."

# Show restore process
echo -e "\n🔧 Beginning recovery process..."
if [ -d "/mnt/usb/velix-demo" ]; then
  echo "Backup found! Please run:"
  echo "cd /mnt/usb/velix-demo"
  echo "ls -lt # to see available backups"
  echo "./latest/restore-demo.sh"
else
  echo "❌ No backup found! This is why we need:"
  echo "   - Automated backups"
  echo "   - Offsite storage"
  echo "   - Regular testing"
fi