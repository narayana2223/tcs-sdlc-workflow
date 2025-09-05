import os
from typing import List

class KafkaConfig:
    """Kafka configuration settings"""
    
    def __init__(self):
        # Bootstrap servers
        self.bootstrap_servers = os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", 
            "localhost:9092"
        )
        
        # Producer settings
        self.batch_size = int(os.getenv("KAFKA_BATCH_SIZE", "16384"))  # 16KB
        self.linger_ms = int(os.getenv("KAFKA_LINGER_MS", "10"))  # 10ms
        self.compression_type = os.getenv("KAFKA_COMPRESSION_TYPE", "snappy")
        self.acks = os.getenv("KAFKA_ACKS", "all")
        self.retries = int(os.getenv("KAFKA_RETRIES", "3"))
        self.retry_backoff_ms = int(os.getenv("KAFKA_RETRY_BACKOFF_MS", "1000"))
        
        # Consumer settings
        self.max_poll_records = int(os.getenv("KAFKA_MAX_POLL_RECORDS", "100"))
        self.max_poll_interval_ms = int(os.getenv("KAFKA_MAX_POLL_INTERVAL_MS", "300000"))  # 5 minutes
        self.session_timeout_ms = int(os.getenv("KAFKA_SESSION_TIMEOUT_MS", "30000"))  # 30 seconds
        self.heartbeat_interval_ms = int(os.getenv("KAFKA_HEARTBEAT_INTERVAL_MS", "3000"))  # 3 seconds
        
        # Topic settings
        self.default_partitions = int(os.getenv("KAFKA_DEFAULT_PARTITIONS", "6"))
        self.default_replication_factor = int(os.getenv("KAFKA_DEFAULT_REPLICATION_FACTOR", "1"))
        self.retention_ms = int(os.getenv("KAFKA_RETENTION_MS", "604800000"))  # 1 week
        
        # Schema Registry (if using Avro)
        self.schema_registry_url = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
        
        # Security settings
        self.security_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
        self.sasl_mechanism = os.getenv("KAFKA_SASL_MECHANISM", "PLAIN")
        self.sasl_username = os.getenv("KAFKA_SASL_USERNAME", "")
        self.sasl_password = os.getenv("KAFKA_SASL_PASSWORD", "")
        
        # SSL settings (if using SSL)
        self.ssl_cafile = os.getenv("KAFKA_SSL_CAFILE", "")
        self.ssl_certfile = os.getenv("KAFKA_SSL_CERTFILE", "")
        self.ssl_keyfile = os.getenv("KAFKA_SSL_KEYFILE", "")
        
        # Performance tuning
        self.enable_idempotence = os.getenv("KAFKA_ENABLE_IDEMPOTENCE", "true").lower() == "true"
        self.max_in_flight_requests = int(os.getenv("KAFKA_MAX_IN_FLIGHT_REQUESTS", "5"))
        
        # Monitoring
        self.jmx_port = int(os.getenv("KAFKA_JMX_PORT", "9997"))
        
    def get_producer_config(self) -> dict:
        """Get producer configuration"""
        config = {
            'bootstrap_servers': self.bootstrap_servers,
            'batch_size': self.batch_size,
            'linger_ms': self.linger_ms,
            'compression_type': self.compression_type,
            'acks': self.acks,
            'retries': self.retries,
            'retry_backoff_ms': self.retry_backoff_ms,
            'enable_idempotence': self.enable_idempotence,
            'max_in_flight_requests_per_connection': self.max_in_flight_requests
        }
        
        # Add security config if needed
        if self.security_protocol != "PLAINTEXT":
            config.update(self._get_security_config())
        
        return config
    
    def get_consumer_config(self, group_id: str) -> dict:
        """Get consumer configuration"""
        config = {
            'bootstrap_servers': self.bootstrap_servers,
            'group_id': group_id,
            'max_poll_records': self.max_poll_records,
            'max_poll_interval_ms': self.max_poll_interval_ms,
            'session_timeout_ms': self.session_timeout_ms,
            'heartbeat_interval_ms': self.heartbeat_interval_ms,
            'enable_auto_commit': False,  # Manual commit for reliability
            'auto_offset_reset': 'earliest'
        }
        
        # Add security config if needed
        if self.security_protocol != "PLAINTEXT":
            config.update(self._get_security_config())
        
        return config
    
    def get_admin_config(self) -> dict:
        """Get admin client configuration"""
        config = {
            'bootstrap_servers': self.bootstrap_servers
        }
        
        # Add security config if needed
        if self.security_protocol != "PLAINTEXT":
            config.update(self._get_security_config())
        
        return config
    
    def _get_security_config(self) -> dict:
        """Get security configuration"""
        config = {
            'security_protocol': self.security_protocol
        }
        
        if self.security_protocol in ['SASL_PLAINTEXT', 'SASL_SSL']:
            config.update({
                'sasl_mechanism': self.sasl_mechanism,
                'sasl_plain_username': self.sasl_username,
                'sasl_plain_password': self.sasl_password
            })
        
        if self.security_protocol in ['SSL', 'SASL_SSL']:
            config.update({
                'ssl_cafile': self.ssl_cafile,
                'ssl_certfile': self.ssl_certfile,
                'ssl_keyfile': self.ssl_keyfile
            })
        
        return config
    
    def get_topic_config(self) -> dict:
        """Get default topic configuration"""
        return {
            'num_partitions': self.default_partitions,
            'replication_factor': self.default_replication_factor,
            'config': {
                'retention.ms': str(self.retention_ms),
                'compression.type': self.compression_type,
                'cleanup.policy': 'delete'
            }
        }

# Topic definitions
KAFKA_TOPICS = {
    'flight.events': {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': '604800000',  # 1 week
            'compression.type': 'snappy'
        }
    },
    'disruption.events': {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': '604800000',
            'compression.type': 'snappy'
        }
    },
    'passenger.events': {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': '604800000',
            'compression.type': 'snappy'
        }
    },
    'rebooking.events': {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': '604800000',
            'compression.type': 'snappy'
        }
    },
    'notification.events': {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': '604800000',
            'compression.type': 'snappy'
        }
    },
    'compliance.events': {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': '604800000',
            'compression.type': 'snappy'
        }
    },
    'cost.events': {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': '604800000',
            'compression.type': 'snappy'
        }
    },
    'external.data': {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': '604800000',
            'compression.type': 'snappy'
        }
    },
    'agent.decisions': {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': '604800000',
            'compression.type': 'snappy'
        }
    },
    'system.metrics': {
        'partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': '259200000',  # 3 days
            'compression.type': 'snappy'
        }
    }
}

# Consumer groups
CONSUMER_GROUPS = {
    'flight-service-group': ['flight.events'],
    'disruption-service-group': ['disruption.events', 'flight.events'],
    'passenger-service-group': ['passenger.events', 'disruption.events'],
    'rebooking-service-group': ['rebooking.events', 'passenger.events'],
    'notification-service-group': ['notification.events', 'passenger.events'],
    'compliance-service-group': ['compliance.events', 'disruption.events'],
    'cost-service-group': ['cost.events', 'disruption.events'],
    'external-service-group': ['external.data'],
    'agent-service-group': ['agent.decisions'],
    'metrics-service-group': ['system.metrics'],
    'analytics-group': ['flight.events', 'disruption.events', 'passenger.events', 'system.metrics']
}