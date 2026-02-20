"""
Agenda Integration Service

Connects AI-generated agendas from AEGIS backend to Minutes Chatbot database.
Reads mom.json files created by AI assistant and imports agendas to PostgreSQL.
"""

import json
import logging
from sqlalchemy.orm import Session
from minutes_chatbot.database.models import Agenda, User
from minutes_chatbot.services import AuthService, AgendaService
from datetime import datetime
from typing import Optional, List, Dict
import os

logger = logging.getLogger(__name__)


class AgendaIntegrationService:
    """Service for integrating AI-generated agendas into chatbot database"""
    
    @staticmethod
    def import_from_mom_json(
        db: Session,
        mom_json_path: str,
        user_email: str
    ) -> List[Agenda]:
        """
        Import agendas from AI-generated mom.json file.
        
        Args:
            db: Database session
            mom_json_path: Path to mom.json file
            user_email: Email of user who owns this meeting
        
        Returns:
            List of created Agenda objects
        """
        try:
            # Read mom.json
            with open(mom_json_path, 'r', encoding='utf-8') as f:
                mom_data = json.load(f)
            
            logger.info(f"Loaded MoM data from: {mom_json_path}")
            
            # Get or create user
            user = AuthService.get_user_by_email(db=db, email=user_email)
            if not user:
                user = AuthService.create_user(db=db, email=user_email, name=user_email.split('@')[0])
                logger.info(f"Created new user: {user_email}")
            
            # Extract meeting metadata
            meeting_title = mom_data.get('title', 'Untitled Meeting')
            meeting_date = mom_data.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            # Get agendas from mom.json
            agenda_items = mom_data.get('agenda', [])
            
            if not agenda_items:
                logger.warning("No agenda items found in mom.json")
                return []
            
            # Create agenda entries in database
            created_agendas = []
            
            for idx, agenda_item in enumerate(agenda_items):
                # Create agenda title from meeting title + item number
                agenda_title = f"{meeting_title} - Item {idx + 1}"
                
                # Create agenda
                agenda = AgendaService.create_agenda(
                    db=db,
                    user_id=user.id,
                    title=agenda_title,
                    content=agenda_item,  # The actual agenda text
                    meeting_date=meeting_date
                )
                
                created_agendas.append(agenda)
                logger.info(f"Created agenda: {agenda_title}")
            
            logger.info(f"Successfully imported {len(created_agendas)} agendas")
            return created_agendas
            
        except FileNotFoundError:
            logger.error(f"mom.json file not found: {mom_json_path}")
            raise Exception(f"File not found: {mom_json_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in mom.json: {str(e)}")
            raise Exception(f"Invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error importing agendas: {str(e)}")
            raise
    
    @staticmethod
    def import_from_task_id(
        db: Session,
        task_id: str,
        user_email: str,
        base_path: str = None
    ) -> List[Agenda]:
        """
        Import agendas from AI assistant task directory.
        
        Args:
            db: Database session
            task_id: AI assistant task ID
            user_email: Email of user who owns this meeting
            base_path: Optional base path (defaults to AEGIS backend path)
        
        Returns:
            List of created Agenda objects
        """
        if base_path is None:
            base_path = "/Users/sohelkumarsahoo/Downloads/aegis_chatbot_shared_3/aegis_backend/public/ai_assistant_mom"
        
        # Construct path to mom.json
        mom_json_path = os.path.join(base_path, task_id, "mom.json")
        
        return AgendaIntegrationService.import_from_mom_json(
            db=db,
            mom_json_path=mom_json_path,
            user_email=user_email
        )
    
    @staticmethod
    def import_all_from_directory(
        db: Session,
        directory_path: str,
        user_email: str
    ) -> Dict[str, List[Agenda]]:
        """
        Import agendas from all mom.json files in a directory.
        
        Args:
            db: Database session
            directory_path: Path to directory containing task folders
            user_email: Email of user who owns these meetings
        
        Returns:
            Dictionary mapping task_id to list of created agendas
        """
        results = {}
        
        if not os.path.exists(directory_path):
            logger.warning(f"Directory does not exist: {directory_path}")
            return results
        
        # Iterate through task directories
        for task_id in os.listdir(directory_path):
            task_dir = os.path.join(directory_path, task_id)
            
            if not os.path.isdir(task_dir):
                continue
            
            mom_json_path = os.path.join(task_dir, "mom.json")
            
            if os.path.exists(mom_json_path):
                try:
                    agendas = AgendaIntegrationService.import_from_mom_json(
                        db=db,
                        mom_json_path=mom_json_path,
                        user_email=user_email
                    )
                    results[task_id] = agendas
                    logger.info(f"Imported {len(agendas)} agendas from task {task_id}")
                except Exception as e:
                    logger.error(f"Failed to import from task {task_id}: {str(e)}")
                    results[task_id] = []
        
        return results
