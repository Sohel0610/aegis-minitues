"""
Audit Logger Utility Module
Centralized audit logging for tracking all critical operations in the Minutes Generator
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class AuditLogger:
    """Centralized audit logging utility for tracking system operations"""
    
    @staticmethod
    def log_action(
        conn,
        entity_type: str,
        entity_id: Optional[int],
        entity_name: str,
        action: str,  # 'created', 'updated', 'deleted'
        performed_by: str,
        old_data: Optional[Dict[Any, Any]] = None,
        new_data: Optional[Dict[Any, Any]] = None,
        vertical_id: Optional[int] = None,
        company_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        remarks: Optional[str] = None
    ) -> Optional[int]:
        """
        Log an audit entry to the audit_logs table
        
        Args:
            conn: Database connection object
            entity_type: Type of entity ('company', 'meeting', 'user', 'agenda', etc.)
            entity_id: ID of the entity (None for batch operations)
            entity_name: Human-readable name of the entity
            action: Action performed ('created', 'updated', 'deleted')
            performed_by: Email/username of user who performed the action
            old_data: Previous state of the entity (for updates/deletes)
            new_data: New state of the entity (for creates/updates)
            vertical_id: Business vertical ID (if applicable)
            company_name: Company name (if applicable)
            ip_address: User's IP address
            user_agent: Browser/client user agent string
            remarks: Additional notes or context
            
        Returns:
            Audit log entry ID if successful, None if failed
        """
        try:
            cursor = conn.cursor()
            
            # Convert dictionaries to JSON strings for JSONB storage
            old_data_json = json.dumps(old_data) if old_data else None
            new_data_json = json.dumps(new_data) if new_data else None
            
            cursor.execute("""
                INSERT INTO audit_logs 
                (entity_type, entity_id, entity_name, action, performed_by, 
                 old_data, new_data, vertical_id, company_name, 
                 ip_address, user_agent, remarks, performed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            """, (
                entity_type,
                entity_id,
                entity_name,
                action,
                performed_by,
                old_data_json,
                new_data_json,
                vertical_id,
                company_name,
                ip_address,
                user_agent,
                remarks
            ))
            
            result = cursor.fetchone()
            audit_id = result['id'] if result else None
            
            # Note: Don't commit here - let the calling function handle transaction
            # This allows audit logging to be part of the same transaction as the main operation
            
            logger.info(
                f"Audit log created: {action} {entity_type} '{entity_name}' by {performed_by} (audit_id: {audit_id})"
            )
            return audit_id
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Don't fail the main operation if audit logging fails
            return None
    
    @staticmethod
    def log_company_created(
        conn, 
        company_id: int, 
        company_name: str, 
        company_data: dict, 
        user_email: str, 
        vertical_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[int]:
        """
        Log company creation
        
        Args:
            conn: Database connection
            company_id: ID of the newly created company
            company_name: Name of the company
            company_data: Complete company data (all fields)
            user_email: Email of user who created the company
            vertical_id: Business vertical ID
            ip_address: User's IP address
            user_agent: User's browser info
            
        Returns:
            Audit log entry ID
        """
        return AuditLogger.log_action(
            conn=conn,
            entity_type='company',
            entity_id=company_id,
            entity_name=company_name,
            action='created',
            performed_by=user_email,
            new_data=company_data,
            vertical_id=vertical_id,
            company_name=company_name,
            ip_address=ip_address,
            user_agent=user_agent,
            remarks=f"Company '{company_name}' added to system"
        )
    
    @staticmethod
    def log_company_deleted(
        conn, 
        company_id: int, 
        company_name: str, 
        company_data: dict, 
        user_email: str,
        deleted_records_count: int = 0,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[int]:
        """
        Log company deletion
        
        Args:
            conn: Database connection
            company_id: ID of the deleted company
            company_name: Name of the deleted company
            company_data: Complete company data before deletion
            user_email: Email of user who deleted the company
            deleted_records_count: Number of related records deleted
            ip_address: User's IP address
            user_agent: User's browser info
            
        Returns:
            Audit log entry ID
        """
        return AuditLogger.log_action(
            conn=conn,
            entity_type='company',
            entity_id=company_id,
            entity_name=company_name,
            action='deleted',
            performed_by=user_email,
            old_data=company_data,
            company_name=company_name,
            ip_address=ip_address,
            user_agent=user_agent,
            remarks=f"Company '{company_name}' deleted along with {deleted_records_count} related records"
        )
    
    @staticmethod
    def log_company_updated(
        conn, 
        company_id: int, 
        company_name: str, 
        old_data: dict, 
        new_data: dict, 
        user_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[int]:
        """
        Log company update
        
        Args:
            conn: Database connection
            company_id: ID of the updated company
            company_name: Name of the company
            old_data: Company data before update
            new_data: Company data after update
            user_email: Email of user who updated the company
            ip_address: User's IP address
            user_agent: User's browser info
            
        Returns:
            Audit log entry ID
        """
        # Calculate what changed
        changed_fields = []
        for key in new_data.keys():
            if key in old_data and old_data[key] != new_data[key]:
                changed_fields.append(key)
        
        remarks = f"Company '{company_name}' updated. Changed fields: {', '.join(changed_fields)}" if changed_fields else f"Company '{company_name}' updated"
        
        return AuditLogger.log_action(
            conn=conn,
            entity_type='company',
            entity_id=company_id,
            entity_name=company_name,
            action='updated',
            performed_by=user_email,
            old_data=old_data,
            new_data=new_data,
            company_name=company_name,
            ip_address=ip_address,
            user_agent=user_agent,
            remarks=remarks
        )
    
    @staticmethod
    def log_meeting_created(
        conn,
        meeting_id: int,
        company_name: str,
        meeting_type: str,
        meeting_number: str,
        user_email: str,
        meeting_data: dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[int]:
        """Log meeting creation"""
        entity_name = f"{company_name} - {meeting_type} #{meeting_number}"
        return AuditLogger.log_action(
            conn=conn,
            entity_type='meeting',
            entity_id=meeting_id,
            entity_name=entity_name,
            action='created',
            performed_by=user_email,
            new_data=meeting_data,
            company_name=company_name,
            ip_address=ip_address,
            user_agent=user_agent,
            remarks=f"Meeting '{entity_name}' created"
        )
    
    @staticmethod
    def log_meeting_finalized(
        conn,
        meeting_id: int,
        company_name: str,
        meeting_type: str,
        meeting_number: str,
        user_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[int]:
        """Log meeting finalization (locking)"""
        entity_name = f"{company_name} - {meeting_type} #{meeting_number}"
        return AuditLogger.log_action(
            conn=conn,
            entity_type='meeting',
            entity_id=meeting_id,
            entity_name=entity_name,
            action='finalized',
            performed_by=user_email,
            company_name=company_name,
            ip_address=ip_address,
            user_agent=user_agent,
            remarks=f"Meeting '{entity_name}' finalized and locked"
        )
    
    @staticmethod
    def log_meeting_unlocked(
        conn,
        meeting_id: int,
        company_name: str,
        meeting_type: str,
        meeting_number: str,
        user_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[int]:
        """Log meeting unlock (master admin only)"""
        entity_name = f"{company_name} - {meeting_type} #{meeting_number}"
        return AuditLogger.log_action(
            conn=conn,
            entity_type='meeting',
            entity_id=meeting_id,
            entity_name=entity_name,
            action='unlocked',
            performed_by=user_email,
            company_name=company_name,
            ip_address=ip_address,
            user_agent=user_agent,
            remarks=f"Meeting '{entity_name}' unlocked by master admin"
        )
    
    @staticmethod
    def log_user_role_changed(
        conn,
        user_email: str,
        old_role: str,
        new_role: str,
        performed_by: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[int]:
        """Log user role/permission changes"""
        return AuditLogger.log_action(
            conn=conn,
            entity_type='user',
            entity_id=None,
            entity_name=user_email,
            action='role_changed',
            performed_by=performed_by,
            old_data={'role': old_role},
            new_data={'role': new_role},
            ip_address=ip_address,
            user_agent=user_agent,
            remarks=f"User '{user_email}' role changed from '{old_role}' to '{new_role}'"
        )


def get_client_ip(request) -> Optional[str]:
    """
    Extract client IP address from request headers
    
    Args:
        request: FastAPI Request object
        
    Returns:
        IP address string or None
    """
    try:
        # Check for forwarded IP first (proxy/load balancer)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return None
    except Exception as e:
        logger.warning(f"Failed to extract client IP: {e}")
        return None


def get_user_agent(request) -> Optional[str]:
    """
    Extract user agent string from request headers
    
    Args:
        request: FastAPI Request object
        
    Returns:
        User agent string or None
    """
    try:
        return request.headers.get('User-Agent')
    except Exception as e:
        logger.warning(f"Failed to extract user agent: {e}")
        return None
