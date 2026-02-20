"""
Enhanced Agenda Integration Service

Imports ALL meeting data from AI-generated mom.json:
- Agendas
- Decisions
- Action Items
- Attendees
"""

import json
import logging
from sqlalchemy.orm import Session
from minutes_chatbot.database.models import Agenda, Decision, ActionItem, Attendee, User, Document, Embedding
from minutes_chatbot.services import AuthService, AgendaService
from minutes_chatbot.services.embedding_service import EmbeddingService
from datetime import datetime
from typing import Optional, List, Dict
import os

logger = logging.getLogger(__name__)


class MeetingIntegrationService:
    """Service for integrating complete AI-generated meeting data into chatbot database"""
    
    @staticmethod
    def import_complete_meeting_from_mom_json(
        db: Session,
        mom_json_path: str,
        user_email: str
    ) -> Dict:
        """
        Import complete meeting data from AI-generated mom.json file.
        
        Imports:
        - Agendas
        - Decisions
        - Action Items
        - Attendees
        
        Args:
            db: Database session
            mom_json_path: Path to mom.json file
            user_email: Email of user who owns this meeting
        
        Returns:
            Dictionary with counts of imported items
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
            meeting_date_str = mom_data.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            # Parse meeting date
            try:
                meeting_date = datetime.strptime(meeting_date_str, '%Y-%m-%d').date()
            except:
                # Try alternative formats
                try:
                    meeting_date = datetime.strptime(meeting_date_str, '%dth %B, %Y').date()
                except:
                    try:
                        meeting_date = datetime.strptime(meeting_date_str, '%dst %B, %Y').date()
                    except:
                        try:
                            meeting_date = datetime.strptime(meeting_date_str, '%dnd %B, %Y').date()
                        except:
                            meeting_date = datetime.now().date()
                            logger.warning(f"Could not parse date: {meeting_date_str}, using today")
            
            results = {
                'agendas': 0,
                'decisions': 0,
                'action_items': 0,
                'attendees': 0
            }
            
            # 1. Import Agendas
            agenda_items = mom_data.get('agenda', [])
            for idx, agenda_item in enumerate(agenda_items):
                agenda_title = f"{meeting_title} - Item {idx + 1}"
                agenda = Agenda(
                    user_id=user.id,
                    agenda_title=agenda_title,
                    agenda_content=agenda_item,
                    meeting_date=meeting_date
                )
                db.add(agenda)
                results['agendas'] += 1
            
            # 2. Import Decisions
            decisions = mom_data.get('decisions', [])
            for decision_text in decisions:
                decision = Decision(
                    user_id=user.id,
                    meeting_title=meeting_title,
                    decision_text=decision_text,
                    meeting_date=meeting_date
                )
                db.add(decision)
                results['decisions'] += 1
            
            # 3. Import Action Items
            action_items = mom_data.get('action_items', [])
            for item in action_items:
                if isinstance(item, dict):
                    task = item.get('task', '')
                    assignee = item.get('assignee', 'Unassigned')
                else:
                    task = str(item)
                    assignee = 'Unassigned'
                
                action_item = ActionItem(
                    user_id=user.id,
                    meeting_title=meeting_title,
                    task_description=task,
                    assignee=assignee,
                    status='pending',
                    meeting_date=meeting_date
                )
                db.add(action_item)
                results['action_items'] += 1
            
            # 4. Import Attendees
            attendees = mom_data.get('attendees', [])
            for attendee in attendees:
                if isinstance(attendee, dict):
                    name = attendee.get('name', '')
                    role = attendee.get('role', '')
                else:
                    name = str(attendee)
                    role = ''
                
                attendee_obj = Attendee(
                    user_id=user.id,
                    meeting_title=meeting_title,
                    attendee_name=name,
                    attendee_role=role,
                    meeting_date=meeting_date
                )
                db.add(attendee_obj)
                results['attendees'] += 1
            
            # Commit all changes
            db.commit()
            
            logger.info(f"Successfully imported meeting data:")
            logger.info(f"  - Agendas: {results['agendas']}")
            logger.info(f"  - Decisions: {results['decisions']}")
            logger.info(f"  - Action Items: {results['action_items']}")
            logger.info(f"  - Attendees: {results['attendees']}")
            
            # Create embeddings for semantic search
            try:
                embeddings_created = MeetingIntegrationService._create_embeddings_for_meeting(
                    db=db,
                    user_id=user.id,
                    meeting_title=meeting_title
                )
                results['embeddings'] = embeddings_created
                logger.info(f"  - Embeddings: {embeddings_created}")
            except Exception as e:
                logger.error(f"Error creating embeddings: {str(e)}")
                results['embeddings'] = 0
            
            return results
            
        except FileNotFoundError:
            logger.error(f"mom.json file not found: {mom_json_path}")
            raise Exception(f"File not found: {mom_json_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in mom.json: {str(e)}")
            raise Exception(f"Invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error importing meeting data: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    def import_from_task_id(
        db: Session,
        task_id: str,
        user_email: str,
        base_path: str = None
    ) -> Dict:
        """
        Import complete meeting data from AI assistant task directory.
        
        Args:
            db: Database session
            task_id: AI assistant task ID
            user_email: Email of user who owns this meeting
            base_path: Optional base path (defaults to AEGIS backend path)
        
        Returns:
            Dictionary with counts of imported items
        """
        if base_path is None:
            base_path = "/Users/sohelkumarsahoo/Downloads/aegis_chatbot_shared_3/aegis_backend/public/ai_assistant_mom"
        
        # Construct path to mom.json
        mom_json_path = os.path.join(base_path, task_id, "mom.json")
        
        return MeetingIntegrationService.import_complete_meeting_from_mom_json(
            db=db,
            mom_json_path=mom_json_path,
            user_email=user_email
        )
    
    @staticmethod
    def import_all_from_directory(
        db: Session,
        directory_path: str,
        user_email: str
    ) -> Dict[str, Dict]:
        """
        Import all meetings from all mom.json files in a directory.
        
        Args:
            db: Database session
            directory_path: Path to directory containing task folders
            user_email: Email of user who owns these meetings
        
        Returns:
            Dictionary mapping task_id to import results
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
                    import_results = MeetingIntegrationService.import_complete_meeting_from_mom_json(
                        db=db,
                        mom_json_path=mom_json_path,
                        user_email=user_email
                    )
                    results[task_id] = import_results
                    logger.info(f"Imported meeting from task {task_id}")
                except Exception as e:
                    logger.error(f"Failed to import from task {task_id}: {str(e)}")
                    results[task_id] = {'error': str(e)}
        
        return results
    
    @staticmethod
    def _create_embeddings_for_meeting(
        db: Session,
        user_id: int,
        meeting_title: str
    ) -> int:
        """
        Create embeddings for all meeting data (agendas, decisions, action items, attendees).
        
        Args:
            db: Database session
            user_id: User ID
            meeting_title: Meeting title to filter data
        
        Returns:
            Number of embeddings created
        """
        embedding_service = EmbeddingService()
        embeddings_created = 0
        
        try:
            # Get all agendas for this meeting
            agendas = db.query(Agenda).filter(
                Agenda.user_id == user_id,
                Agenda.meeting_date.isnot(None)  # Filter by meeting
            ).all()
            
            # Get all decisions for this meeting
            decisions = db.query(Decision).filter(
                Decision.user_id == user_id,
                Decision.meeting_title == meeting_title
            ).all()
            
            # Get all action items for this meeting
            action_items = db.query(ActionItem).filter(
                ActionItem.user_id == user_id,
                ActionItem.meeting_title == meeting_title
            ).all()
            
            # Get all attendees for this meeting
            attendees = db.query(Attendee).filter(
                Attendee.user_id == user_id,
                Attendee.meeting_title == meeting_title
            ).all()
            
            # Create a virtual document for this meeting
            document = Document(
                user_id=user_id,
                filename=f"{meeting_title}.json",
                file_path=f"virtual://{meeting_title}",
                file_type="application/json",
                file_size=0,
                extracted_text=f"Meeting: {meeting_title}"
            )
            db.add(document)
            db.flush()  # Get document ID
            
            logger.info(f"Creating embeddings for meeting: {meeting_title}")
            logger.info(f"  - Agendas: {len(agendas)}")
            logger.info(f"  - Decisions: {len(decisions)}")
            logger.info(f"  - Action Items: {len(action_items)}")
            logger.info(f"  - Attendees: {len(attendees)}")
            
            # Create embeddings for agendas
            for idx, agenda in enumerate(agendas):
                text = f"Agenda: {agenda.agenda_title} - {agenda.agenda_content}"
                vector = embedding_service.generate_embedding(text)
                
                embedding = Embedding(
                    document_id=document.id,
                    chunk_text=text,
                    chunk_index=idx,
                    embedding_vector=vector
                )
                db.add(embedding)
                embeddings_created += 1
            
            # Create embeddings for decisions
            for idx, decision in enumerate(decisions):
                text = f"Decision: {decision.decision_text}"
                vector = embedding_service.generate_embedding(text)
                
                embedding = Embedding(
                    document_id=document.id,
                    chunk_text=text,
                    chunk_index=len(agendas) + idx,
                    embedding_vector=vector
                )
                db.add(embedding)
                embeddings_created += 1
            
            # Create embeddings for action items
            for idx, action_item in enumerate(action_items):
                text = f"Action Item: {action_item.task_description} (Assignee: {action_item.assignee})"
                vector = embedding_service.generate_embedding(text)
                
                embedding = Embedding(
                    document_id=document.id,
                    chunk_text=text,
                    chunk_index=len(agendas) + len(decisions) + idx,
                    embedding_vector=vector
                )
                db.add(embedding)
                embeddings_created += 1
            
            # Create embeddings for attendees
            for idx, attendee in enumerate(attendees):
                # Create text with attendee name and role
                if attendee.attendee_role:
                    text = f"Attendee: {attendee.attendee_name} - {attendee.attendee_role}"
                else:
                    text = f"Attendee: {attendee.attendee_name}"
                
                vector = embedding_service.generate_embedding(text)
                
                embedding = Embedding(
                    document_id=document.id,
                    chunk_text=text,
                    chunk_index=len(agendas) + len(decisions) + len(action_items) + idx,
                    embedding_vector=vector
                )
                db.add(embedding)
                embeddings_created += 1
            
            db.commit()
            logger.info(f"Created {embeddings_created} embeddings for meeting: {meeting_title}")
            
            return embeddings_created
            
        except Exception as e:
            logger.error(f"Error creating embeddings for meeting: {str(e)}")
            db.rollback()
            raise
