"""
Database Connection Manager for Flight Disruption Management System

Handles PostgreSQL connections, session management, and connection pooling
for production-ready database operations.
"""

import asyncio
import os
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional, Dict, Any
import structlog
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import Engine
import asyncpg

from .schemas import Base

logger = structlog.get_logger()


class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        self.database_url = os.getenv(
            'DATABASE_URL',
            'postgresql://flight_user:flight_password@localhost:5432/flight_disruption'
        )
        self.async_database_url = self.database_url.replace('postgresql://', 'postgresql+asyncpg://')
        
        # Connection pool settings
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '20'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '30'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))
        
        # Performance settings
        self.echo = os.getenv('DB_ECHO', 'false').lower() == 'true'
        self.echo_pool = os.getenv('DB_ECHO_POOL', 'false').lower() == 'true'


class DatabaseManager:
    """Centralized database connection and session management"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._async_engine: Optional[create_async_engine] = None
        self._session_maker: Optional[sessionmaker] = None
        self._async_session_maker: Optional[async_sessionmaker] = None
        self._initialized = False
        
        logger.info("DatabaseManager initialized", database_url=self._mask_credentials(self.config.database_url))
    
    def _mask_credentials(self, url: str) -> str:
        """Mask database credentials for logging"""
        import re
        return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', url)
    
    def initialize_sync_engine(self) -> Engine:
        """Initialize synchronous database engine"""
        if self._engine is None:
            self._engine = create_engine(
                self.config.database_url,
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=self.config.echo,
                echo_pool=self.config.echo_pool,
                # Performance optimizations
                connect_args={
                    "application_name": "flight_disruption_system",
                    "options": "-c timezone=UTC"
                }
            )
            
            # Add connection event listeners for monitoring
            event.listen(self._engine, "connect", self._on_connect)
            event.listen(self._engine, "checkout", self._on_checkout)
            event.listen(self._engine, "checkin", self._on_checkin)
            
            self._session_maker = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            logger.info("Synchronous database engine initialized")
        
        return self._engine
    
    def initialize_async_engine(self):
        """Initialize asynchronous database engine"""
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                self.config.async_database_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=self.config.echo,
                # Performance optimizations for async
                connect_args={
                    "application_name": "flight_disruption_system_async",
                    "server_settings": {
                        "timezone": "UTC",
                        "application_name": "flight_disruption_system"
                    }
                }
            )
            
            self._async_session_maker = async_sessionmaker(
                bind=self._async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
            
            logger.info("Asynchronous database engine initialized")
        
        return self._async_engine
    
    def _on_connect(self, dbapi_connection, connection_record):
        """Handle new database connections"""
        logger.debug("New database connection established")
    
    def _on_checkout(self, dbapi_connection, connection_record, connection_proxy):
        """Handle connection checkout from pool"""
        logger.debug("Database connection checked out from pool")
    
    def _on_checkin(self, dbapi_connection, connection_record):
        """Handle connection checkin to pool"""
        logger.debug("Database connection returned to pool")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get synchronous database session"""
        if not self._session_maker:
            self.initialize_sync_engine()
        
        session = self._session_maker()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get asynchronous database session"""
        if not self._async_session_maker:
            self.initialize_async_engine()
        
        session = self._async_session_maker()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Async database session error", error=str(e))
            raise
        finally:
            await session.close()
    
    async def create_tables(self):
        """Create all database tables"""
        if not self._async_engine:
            self.initialize_async_engine()
        
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    
    async def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        if not self._async_engine:
            self.initialize_async_engine()
        
        async with self._async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("All database tables dropped")
    
    async def check_connection(self) -> bool:
        """Check database connectivity"""
        try:
            if not self._async_engine:
                self.initialize_async_engine()
            
            async with self._async_engine.begin() as conn:
                result = await conn.execute("SELECT 1")
                return result.scalar() == 1
        except Exception as e:
            logger.error("Database connection check failed", error=str(e))
            return False
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        stats = {}
        
        if self._engine:
            pool = self._engine.pool
            stats['sync'] = {
                'pool_size': pool.size(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'checked_in': pool.checkedin()
            }
        
        if self._async_engine:
            pool = self._async_engine.pool
            stats['async'] = {
                'pool_size': pool.size(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'checked_in': pool.checkedin()
            }
        
        return stats
    
    async def close_connections(self):
        """Close all database connections"""
        if self._async_engine:
            await self._async_engine.dispose()
            logger.info("Async database connections closed")
        
        if self._engine:
            self._engine.dispose()
            logger.info("Sync database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for common operations

def get_db_session() -> Generator[Session, None, None]:
    """Get synchronous database session (convenience function)"""
    return db_manager.get_session()


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get asynchronous database session (convenience function)"""
    async with db_manager.get_async_session() as session:
        yield session


async def init_database():
    """Initialize database and create tables"""
    logger.info("Initializing database...")
    
    # Check connection first
    connection_ok = await db_manager.check_connection()
    if not connection_ok:
        logger.error("Cannot connect to database")
        raise RuntimeError("Database connection failed")
    
    # Create tables
    await db_manager.create_tables()
    
    logger.info("Database initialization completed successfully")


async def get_database_health() -> Dict[str, Any]:
    """Get database health information"""
    try:
        connection_ok = await db_manager.check_connection()
        stats = db_manager.get_connection_stats()
        
        return {
            "status": "healthy" if connection_ok else "unhealthy",
            "connection_ok": connection_ok,
            "pool_stats": stats,
            "database_url": db_manager._mask_credentials(db_manager.config.database_url)
        }
    except Exception as e:
        logger.error("Failed to get database health", error=str(e))
        return {
            "status": "error",
            "error": str(e)
        }


# Migration utilities

class MigrationManager:
    """Database migration management"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = structlog.get_logger().bind(component="migration_manager")
    
    async def run_migration(self, migration_script: str):
        """Run a database migration script"""
        self.logger.info("Running migration", script=migration_script)
        
        async with self.db_manager.get_async_session() as session:
            try:
                await session.execute(migration_script)
                await session.commit()
                self.logger.info("Migration completed successfully")
            except Exception as e:
                await session.rollback()
                self.logger.error("Migration failed", error=str(e))
                raise
    
    async def seed_reference_data(self):
        """Seed the database with reference data"""
        self.logger.info("Seeding reference data...")
        
        from .seed_data import get_reference_airports, get_reference_aircraft
        
        async with self.db_manager.get_async_session() as session:
            try:
                # Seed airports
                airports = get_reference_airports()
                for airport_data in airports:
                    airport = Airport(**airport_data)
                    session.add(airport)
                
                # Seed aircraft
                aircraft = get_reference_aircraft()
                for aircraft_data in aircraft:
                    aircraft_obj = Aircraft(**aircraft_data)
                    session.add(aircraft_obj)
                
                await session.commit()
                self.logger.info("Reference data seeded successfully")
                
            except Exception as e:
                await session.rollback()
                self.logger.error("Failed to seed reference data", error=str(e))
                raise


# Export the main components
__all__ = [
    'DatabaseConfig',
    'DatabaseManager', 
    'db_manager',
    'get_db_session',
    'get_async_db_session',
    'init_database',
    'get_database_health',
    'MigrationManager'
]