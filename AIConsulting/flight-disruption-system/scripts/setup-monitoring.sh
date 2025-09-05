#!/bin/bash
# Setup script for Flight Disruption Management System monitoring

set -e

echo "Setting up monitoring for Flight Disruption Management System..."

# Create monitoring directories
mkdir -p shared/monitoring/grafana/dashboards
mkdir -p shared/monitoring/grafana/provisioning/dashboards
mkdir -p shared/monitoring/grafana/provisioning/datasources
mkdir -p shared/monitoring/alertmanager

# Set permissions
chmod +x scripts/*.sh

# Create Grafana dashboard for system overview
cat > shared/monitoring/grafana/dashboards/system-overview.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Flight Disruption System Overview",
    "tags": ["flight", "disruption", "overview"],
    "style": "dark",
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "System Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up",
            "legendFormat": "{{job}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "palette-classic"
            },
            "custom": {
              "displayMode": "list",
              "orientation": "horizontal"
            },
            "mappings": [
              {
                "options": {
                  "0": {
                    "color": "red",
                    "index": 0,
                    "text": "Down"
                  },
                  "1": {
                    "color": "green",
                    "index": 1,
                    "text": "Up"
                  }
                },
                "type": "value"
              }
            ],
            "thresholds": {
              "steps": [
                {
                  "color": "red",
                  "value": null
                },
                {
                  "color": "green",
                  "value": 1
                }
              ]
            }
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(gateway_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        }
      },
      {
        "id": 3,
        "title": "Response Time (95th percentile)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(gateway_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{job}}"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 24,
          "x": 0,
          "y": 8
        }
      },
      {
        "id": 4,
        "title": "Disruption Predictions",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(disruption_predictions_total[1h])",
            "legendFormat": "{{predicted_disruption_type}}"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 16
        }
      },
      {
        "id": 5,
        "title": "Passenger Rebookings",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(rebookings_total[5m])",
            "legendFormat": "{{status}}"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 16
        }
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "10s"
  }
}
EOF

# Create Alertmanager configuration
cat > shared/monitoring/alertmanager/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@flight-disruption-system.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
  - match:
      severity: critical
    receiver: 'critical-alerts'
  - match:
      severity: warning
    receiver: 'warning-alerts'

receivers:
- name: 'web.hook'
  webhook_configs:
  - url: 'http://notification:8000/api/v1/alerts/webhook'
    send_resolved: true

- name: 'critical-alerts'
  email_configs:
  - to: 'operations@airline.com'
    subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  webhook_configs:
  - url: 'http://notification:8000/api/v1/alerts/critical'
    send_resolved: true

- name: 'warning-alerts'
  email_configs:
  - to: 'monitoring@airline.com'
    subject: 'WARNING: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}

inhibit_rules:
- source_match:
    severity: 'critical'
  target_match:
    severity: 'warning'
  equal: ['alertname', 'instance']
EOF

# Create health check script
cat > scripts/health-check.sh << 'EOF'
#!/bin/bash
# Health check script for all services

services=(
    "api-gateway:8000"
    "disruption-predictor:8001"
    "passenger-management:8002"
    "cost-optimizer:8003"
    "compliance:8004"
    "notification:8005"
)

echo "Checking health of all services..."

all_healthy=true

for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d':' -f1)
    service_url="http://$service/health"
    
    if curl -f -s "$service_url" > /dev/null; then
        echo "✓ $service_name is healthy"
    else
        echo "✗ $service_name is unhealthy"
        all_healthy=false
    fi
done

# Check database
if pg_isready -h postgres -p 5432 > /dev/null 2>&1; then
    echo "✓ PostgreSQL is healthy"
else
    echo "✗ PostgreSQL is unhealthy"
    all_healthy=false
fi

# Check Redis
if redis-cli -h redis ping | grep PONG > /dev/null; then
    echo "✓ Redis is healthy"
else
    echo "✗ Redis is unhealthy"
    all_healthy=false
fi

if $all_healthy; then
    echo "All services are healthy!"
    exit 0
else
    echo "Some services are unhealthy!"
    exit 1
fi
EOF

chmod +x scripts/health-check.sh

# Create log aggregation script
cat > scripts/collect-logs.sh << 'EOF'
#!/bin/bash
# Collect logs from all services

timestamp=$(date +%Y%m%d_%H%M%S)
log_dir="logs/collected_$timestamp"

mkdir -p "$log_dir"

echo "Collecting logs to $log_dir..."

# Collect Docker logs
services=(
    "flight-api-gateway"
    "flight-disruption-predictor"
    "flight-passenger-management"
    "flight-cost-optimizer"
    "flight-compliance"
    "flight-notification"
    "flight-postgres"
    "flight-redis"
    "flight-kafka"
)

for service in "${services[@]}"; do
    echo "Collecting logs for $service..."
    docker logs "$service" > "$log_dir/${service}.log" 2>&1
done

# Create summary
echo "Log collection completed at $(date)" > "$log_dir/README.txt"
echo "Logs collected for ${#services[@]} services" >> "$log_dir/README.txt"
echo "Total log size: $(du -sh $log_dir | cut -f1)" >> "$log_dir/README.txt"

echo "Logs collected in $log_dir"
EOF

chmod +x scripts/collect-logs.sh

echo "Monitoring setup completed!"
echo ""
echo "Available scripts:"
echo "  scripts/health-check.sh    - Check health of all services"
echo "  scripts/collect-logs.sh    - Collect logs from all services"
echo ""
echo "Monitoring URLs (after starting with docker-compose):"
echo "  Grafana:    http://localhost:3000 (admin/admin_password)"
echo "  Prometheus: http://localhost:9090"
echo "  Kibana:     http://localhost:5601"