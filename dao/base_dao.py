"""
Base DAO class with common database operations
"""

from typing import List, Dict, Optional, Any
from database.database import db_manager


class BaseDAO:
    """Base DAO class with common database operations"""
    
    def __init__(self, model_class):
        self.model_class = model_class
        self.session = db_manager.get_session()
    
    def get_all(self) -> List[Any]:
        """Get all records from the table"""
        try:
            return self.session.query(self.model_class).all()
        finally:
            self.session.close()
    
    def get_by_id(self, record_id: int) -> Optional[Any]:
        """Get record by ID"""
        try:
            return self.session.query(self.model_class).filter(
                self.model_class.id == record_id
            ).first()
        finally:
            self.session.close()
    
    def create(self, **kwargs) -> Any:
        """Create a new record"""
        try:
            record = self.model_class(**kwargs)
            self.session.add(record)
            self.session.commit()
            return record
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.close()
    
    def update(self, record_id: int, **kwargs) -> Optional[Any]:
        """Update a record by ID"""
        try:
            record = self.session.query(self.model_class).filter(
                self.model_class.id == record_id
            ).first()
            
            if record:
                for key, value in kwargs.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                self.session.commit()
                return record
            return None
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.close()
    
    def delete(self, record_id: int) -> bool:
        """Delete a record by ID"""
        try:
            record = self.session.query(self.model_class).filter(
                self.model_class.id == record_id
            ).first()
            
            if record:
                self.session.delete(record)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            raise e
        finally:
            self.session.close()
    
    def get_session(self):
        """Get database session"""
        return db_manager.get_session()
