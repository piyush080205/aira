"""
Database utilities for proper session management and transaction handling
"""
import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
from sqlalchemy.orm import Session
from models import SessionLocal

logger = logging.getLogger(__name:__)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions with automatic commit/rollback
    
    Usage:
        with get_db_session() as db:
            user = db.query(User).first()
            # Auto-commit on success, auto-rollback on error
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database transaction failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


@asynccontextmanager
async def get_async_db_session() -> AsyncGenerator[Session, None]:
    """
    Async context manager for database sessions
    
    Usage:
        async with get_async_db_session() as db:
            user = db.query(User).first()
            # Auto-commit on success, auto-rollback on error
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database transaction failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions
    
    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseTransaction:
    """
    Context manager for explicit transaction control with savepoints
    
    Usage:
        with get_db_session() as db:
            with DatabaseTransaction(db) as tx:
                # Do some work
                tx.savepoint("checkpoint1")
                # Do more work
                if error:
                    tx.rollback_to_savepoint("checkpoint1")
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.savepoints = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        return False
    
    def savepoint(self, name: str):
        """Create a savepoint"""
        sp = self.session.begin_nested()
        self.savepoints[name] = sp
        logger.debug(f"Created savepoint: {name}")
    
    def rollback_to_savepoint(self, name: str):
        """Rollback to a specific savepoint"""
        if name in self.savepoints:
            self.savepoints[name].rollback()
            logger.info(f"Rolled back to savepoint: {name}")
        else:
            logger.warning(f"Savepoint not found: {name}")
    
    def commit(self):
        """Explicitly commit the transaction"""
        self.session.commit()
        logger.debug("Transaction committed")
    
    def rollback(self):
        """Explicitly rollback the transaction"""
        self.session.rollback()
        logger.info("Transaction rolled back")


# Made with Bob
