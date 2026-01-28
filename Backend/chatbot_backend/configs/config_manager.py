"""
Configuration Manager Module
Provides a unified interface for accessing configuration across all databases
"""

from typing import Dict, Any, Optional
from configs.bse import (
    BSE_SYSTEM_INSTRUCTIONS,
    BSE_INTENT_CLASSIFICATION_PROMPT,
    BSE_ENTITY_EXTRACTION_PROMPT,
    BSE_RESPONSE_GENERATION_PROMPT,
    BSE_RD_INNOVATION_PROMPT,
    BSE_NIL_DATA_RESPONSE_PROMPT
)

from configs.sebi import (
    SEBI_SYSTEM_INSTRUCTIONS,
    SEBI_INTENT_CLASSIFICATION_PROMPT,
    SEBI_ENTITY_EXTRACTION_PROMPT,
    SEBI_RESPONSE_GENERATION_PROMPT,
    SEBI_NIL_DATA_RESPONSE_PROMPT
)

from configs.rbi import (
    RBI_SYSTEM_INSTRUCTIONS,
    RBI_INTENT_CLASSIFICATION_PROMPT,
    RBI_ENTITY_EXTRACTION_PROMPT,
    RBI_RESPONSE_GENERATION_PROMPT,
    RBI_NIL_DATA_RESPONSE_PROMPT
)

class ConfigManager:
    """Manages configuration access for all databases"""
    
    def __init__(self):
        # Define configuration mappings for each database
        self.configs = {
            "bse": {
                "system_instructions": BSE_SYSTEM_INSTRUCTIONS,
                "intent_classification_prompt": BSE_INTENT_CLASSIFICATION_PROMPT,
                "entity_extraction_prompt": BSE_ENTITY_EXTRACTION_PROMPT,
                "response_generation_prompt": BSE_RESPONSE_GENERATION_PROMPT,
                "rd_innovation_prompt": BSE_RD_INNOVATION_PROMPT,
                "nil_data_response_prompt": BSE_NIL_DATA_RESPONSE_PROMPT
            },
            "sebi": {
                "system_instructions": SEBI_SYSTEM_INSTRUCTIONS,
                "intent_classification_prompt": SEBI_INTENT_CLASSIFICATION_PROMPT,
                "entity_extraction_prompt": SEBI_ENTITY_EXTRACTION_PROMPT,
                "response_generation_prompt": SEBI_RESPONSE_GENERATION_PROMPT,
                "nil_data_response_prompt": SEBI_NIL_DATA_RESPONSE_PROMPT
            },
            "rbi": {
                "system_instructions": RBI_SYSTEM_INSTRUCTIONS,
                "intent_classification_prompt": RBI_INTENT_CLASSIFICATION_PROMPT,
                "entity_extraction_prompt": RBI_ENTITY_EXTRACTION_PROMPT,
                "response_generation_prompt": RBI_RESPONSE_GENERATION_PROMPT,
                "nil_data_response_prompt": RBI_NIL_DATA_RESPONSE_PROMPT
            }
        }
    
    def get_system_instructions(self, database: str) -> str:
        """Get system instructions for a specific database"""
        return self.configs.get(database.lower(), {}).get("system_instructions", "")
    
    def get_intent_classification_prompt(self, database: str) -> str:
        """Get intent classification prompt for a specific database"""
        return self.configs.get(database.lower(), {}).get("intent_classification_prompt", "")
    
    def get_entity_extraction_prompt(self, database: str) -> str:
        """Get entity extraction prompt for a specific database"""
        return self.configs.get(database.lower(), {}).get("entity_extraction_prompt", "")
    
    def get_response_generation_prompt(self, database: str, is_rd_query: bool = False) -> str:
        """Get response generation prompt for a specific database"""
        db_config = self.configs.get(database.lower(), {})
        if is_rd_query and database.lower() == "bse":
            return db_config.get("rd_innovation_prompt", db_config.get("response_generation_prompt", ""))
        return db_config.get("response_generation_prompt", "")
    
    def get_nil_data_response_prompt(self, database: str) -> str:
        """Get NIL data response prompt for a specific database"""
        return self.configs.get(database.lower(), {}).get("nil_data_response_prompt", "")
    
    def get_all_configs_for_database(self, database: str) -> Dict[str, Any]:
        """Get all configurations for a specific database"""
        return self.configs.get(database.lower(), {})

# Global instance
config_manager = ConfigManager()

def get_config_manager():
    """Get the global configuration manager instance"""
    return config_manager