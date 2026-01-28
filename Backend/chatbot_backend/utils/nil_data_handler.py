"""
NIL Data Handler Module
Provides specialized functionality for handling NIL data cases across all databases
"""

from typing import List, Dict, Any, Tuple
from utils.logging_utils import logger, log_database_operation, log_warning

class NILDataHandler:
    """Handles NIL data detection and processing for all databases"""
    
    def __init__(self):
        # Define NIL detection patterns for each database
        self.nil_patterns = {
            "bse": {
                "fields": ["Link", "Nature", "Summary"],
                "nil_values": ["NIL", "NULL", "", "N/A"]
            },
            "sebi": {
                "fields": ["pdf_link", "summary"],
                "nil_values": ["NIL", "NULL", "", "N/A"]
            },
            "rbi": {
                "fields": ["pdf_link", "summary"],
                "nil_values": ["NIL", "NULL", "", "N/A"]
            }
        }
    
    def is_nil_record(self, record: Any, database: str) -> bool:
        """
        Check if a record is a NIL record based on database-specific criteria
        
        Args:
            record: The record to check
            database: The database type (bse, sebi, rbi)
            
        Returns:
            True if the record is a NIL record, False otherwise
        """
        db_config = self.nil_patterns.get(database.lower())
        if not db_config:
            return False
        
        nil_fields = db_config["fields"]
        nil_values = db_config["nil_values"]
        
        # Check if all required fields are NIL
        nil_field_count = 0
        for field in nil_fields:
            if hasattr(record, field):
                field_value = getattr(record, field)
                if field_value in nil_values:
                    nil_field_count += 1
        
        # Consider it NIL if all required fields are NIL
        return nil_field_count == len(nil_fields)
    
    def filter_nil_records(self, records: List[Any], database: str) -> Tuple[List[Any], int]:
        """
        Filter out NIL records from a list of records
        
        Args:
            records: List of records to filter
            database: The database type (bse, sebi, rbi)
            
        Returns:
            Tuple of (filtered_records, nil_count)
        """
        if not records:
            return [], 0
        
        filtered_records = []
        nil_count = 0
        
        for record in records:
            if self.is_nil_record(record, database):
                nil_count += 1
            else:
                filtered_records.append(record)
        
        log_database_operation(database, "nil_filtering", {
            "total_records": len(records),
            "nil_records": nil_count,
            "valid_records": len(filtered_records)
        })
        
        return filtered_records, nil_count
    
    def is_pure_nil_dataset(self, records: List[Any], database: str) -> bool:
        """
        Check if all records in a dataset are NIL records
        
        Args:
            records: List of records to check
            database: The database type (bse, sebi, rbi)
            
        Returns:
            True if all records are NIL, False otherwise
        """
        if not records:
            return False
        
        for record in records:
            if not self.is_nil_record(record, database):
                return False
        
        return True
    
    def has_partial_nil_data(self, records: List[Any], database: str) -> bool:
        """
        Check if a dataset contains some NIL records mixed with valid records
        
        Args:
            records: List of records to check
            database: The database type (bse, sebi, rbi)
            
        Returns:
            True if there are mixed NIL and valid records, False otherwise
        """
        if not records:
            return False
        
        nil_count = 0
        for record in records:
            if self.is_nil_record(record, database):
                nil_count += 1
        
        # Has partial NIL data if some but not all records are NIL
        return 0 < nil_count < len(records)
    
    def handle_entity_matching(self, records: List[Any], entities: List[str], database: str) -> bool:
        """
        Check if the returned records actually match the requested entities
        
        Args:
            records: List of records to check
            entities: List of requested entities
            database: The database type (bse, sebi, rbi)
            
        Returns:
            True if records match entities, False otherwise
        """
        if not entities or not records:
            return True  # No entities to match or no records to check
        
        # For BSE, check EntityName field
        if database.lower() == "bse":
            entity_match_count = 0
            for record in records:
                if hasattr(record, 'EntityName'):
                    for entity in entities:
                        # More flexible matching - check if either entity name is contained in the other
                        record_entity = record.EntityName.lower()
                        requested_entity = entity.lower()
                        if requested_entity in record_entity or record_entity in requested_entity:
                            entity_match_count += 1
                            break
            
            # If none of the returned records match the requested entities,
            # treat as NIL data case (fallback results are not relevant)
            if entity_match_count == 0:
                log_warning("NILDataHandler", "No records match requested entities", {
                    "database": database,
                    "requested_entities": entities,
                    "records_count": len(records)
                })
                return False
        
        return True

# Global instance
nil_handler = NILDataHandler()

def get_nil_handler():
    """Get the global NIL data handler instance"""
    return nil_handler