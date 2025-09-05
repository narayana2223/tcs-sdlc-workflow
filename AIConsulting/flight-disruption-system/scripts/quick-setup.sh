#!/bin/bash
# Quick setup script for Flight Disruption Management System

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Flight Disruption Management System - Quick Setup${NC}"
echo "=================================================================="

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker Desktop first.${NC}"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose V2 is not available. Please update Docker Desktop.${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is installed and running${NC}"

# Check available resources
available_memory=$(docker system info --format '{{.MemTotal}}' 2>/dev/null || echo "0")
if [ "$available_memory" -lt 8000000000 ]; then
    echo -e "${YELLOW}⚠️  Warning: Less than 8GB RAM available. System may run slowly.${NC}"
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating environment configuration...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file from template${NC}"
    echo -e "${YELLOW}⚠️  Please edit .env file and add your API keys before continuing!${NC}"
    
    read -p "Do you want to continue with default configuration? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Please edit the .env file and run this script again.${NC}"
        exit 0
    fi
else
    echo -e "${GREEN}✅ Environment configuration found${NC}"
fi

# Make scripts executable
echo -e "\n${YELLOW}Setting up scripts...${NC}"
chmod +x scripts/*.sh
echo -e "${GREEN}✅ Scripts are now executable${NC}"

# Pull Docker images in parallel for faster startup
echo -e "\n${YELLOW}Pulling Docker images (this may take a few minutes)...${NC}"
docker-compose pull --parallel || {
    echo -e "${YELLOW}⚠️  Some images failed to pull. Will try to build from source.${NC}"
}

# Create necessary directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p logs shared/monitoring/grafana/dashboards shared/monitoring/grafana/provisioning/dashboards shared/monitoring/grafana/provisioning/datasources

echo -e "${GREEN}✅ Directories created${NC}"

# Start the infrastructure services first
echo -e "\n${YELLOW}Starting infrastructure services...${NC}"
docker-compose up -d postgres redis zookeeper kafka
echo -e "${GREEN}✅ Infrastructure services starting${NC}"

# Wait for infrastructure to be ready
echo -e "\n${YELLOW}Waiting for infrastructure to be ready...${NC}"
sleep 10

# Check if database is ready
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T postgres pg_isready -U flight_user -d flight_disruption &> /dev/null; then
        break
    fi
    sleep 2
    attempt=$((attempt + 1))
    echo -n "."
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "\n${RED}❌ Database failed to start. Check logs: docker-compose logs postgres${NC}"
    exit 1
fi

echo -e "\n${GREEN}✅ Database is ready${NC}"

# Start application services
echo -e "\n${YELLOW}Starting application services...${NC}"
docker-compose up -d
echo -e "${GREEN}✅ All services starting${NC}"

# Wait for services to be healthy
echo -e "\n${YELLOW}Waiting for services to be healthy (this may take 2-3 minutes)...${NC}"
sleep 30

# Run health check
echo -e "\n${YELLOW}Running health checks...${NC}"

services=(
    "api-gateway:8000"
    "disruption-predictor:8001"
    "passenger-management:8002"
)

healthy_services=0
total_services=${#services[@]}

for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d':' -f1)
    service_url="http://localhost:$(echo $service | cut -d':' -f2)/health"
    
    if curl -f -s --max-time 10 "$service_url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name is healthy${NC}"
        healthy_services=$((healthy_services + 1))
    else
        echo -e "${RED}❌ $service_name is not responding${NC}"
    fi
done

# Check infrastructure
if docker-compose exec -T postgres pg_isready -U flight_user -d flight_disruption &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL is healthy${NC}"
    healthy_services=$((healthy_services + 1))
    total_services=$((total_services + 1))
else
    echo -e "${RED}❌ PostgreSQL is not healthy${NC}"
    total_services=$((total_services + 1))
fi

if docker-compose exec -T redis redis-cli ping | grep PONG > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is healthy${NC}"
    healthy_services=$((healthy_services + 1))
    total_services=$((total_services + 1))
else
    echo -e "${RED}❌ Redis is not healthy${NC}"
    total_services=$((total_services + 1))
fi

# Show results
echo -e "\n=================================================================="
echo -e "${BLUE}Setup Complete!${NC}"
echo -e "=================================================================="

if [ $healthy_services -eq $total_services ]; then
    echo -e "${GREEN}🎉 All services are running successfully!${NC}\n"
    
    echo -e "${BLUE}Access URLs:${NC}"
    echo "• API Gateway:        http://localhost:8000"
    echo "• API Documentation:  http://localhost:8000/docs"
    echo "• Grafana Dashboard:  http://localhost:3000 (admin/admin_password)"
    echo "• Prometheus:         http://localhost:9090"
    echo "• Kibana:             http://localhost:5601"
    
    echo -e "\n${BLUE}Getting Started:${NC}"
    echo "1. Open API docs: http://localhost:8000/docs"
    echo "2. Create a JWT token: POST /api/v1/auth/token (username: admin, password: admin)"
    echo "3. Use the token to authenticate API requests"
    echo "4. Check monitoring: http://localhost:3000"
    
    echo -e "\n${BLUE}Useful Commands:${NC}"
    echo "• View logs:          docker-compose logs -f [service-name]"
    echo "• Check health:       ./scripts/health-check.sh"
    echo "• Stop system:        docker-compose down"
    echo "• Restart system:     docker-compose restart"
    echo "• Collect logs:       ./scripts/collect-logs.sh"
    
else
    echo -e "${YELLOW}⚠️  System started but some services are not healthy (${healthy_services}/${total_services})${NC}\n"
    
    echo -e "${BLUE}Troubleshooting:${NC}"
    echo "1. Check logs: docker-compose logs [service-name]"
    echo "2. Restart unhealthy services: docker-compose restart [service-name]"
    echo "3. Check .env file for missing API keys"
    echo "4. Ensure you have at least 8GB RAM and 4 CPU cores"
    
    echo -e "\n${BLUE}Most common issues:${NC}"
    echo "• Missing OpenAI API key (required for predictions)"
    echo "• Insufficient system resources"
    echo "• Port conflicts (check if ports 8000-8005 are free)"
fi

echo -e "\n${BLUE}Next Steps:${NC}"
echo "1. Edit .env file and add your API keys (especially OpenAI)"
echo "2. Restart services: docker-compose restart"
echo "3. Read GETTING_STARTED.md for detailed usage instructions"
echo "4. Load your flight and passenger data"
echo "5. Configure monitoring alerts"

echo -e "\n${GREEN}Happy disruption management! ✈️${NC}"