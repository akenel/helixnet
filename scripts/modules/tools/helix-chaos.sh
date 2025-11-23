# chaos.sh
echo "Simulating network partition..."
docker network disconnect velix-network postgres

sleep 30  # Show failure state

echo "Demonstrating failover..."
# Show read replicas taking over