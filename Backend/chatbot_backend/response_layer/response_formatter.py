"""
Response Formatter - Claude-quality response generation
Adaptive formatting for conversational, tabular, visual, and executive modes
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


class ResponseFormat(Enum):
    """Response format types"""
    CONVERSATIONAL = "conversational"  # Natural prose
    TABULAR = "tabular"  # Structured table
    VISUAL = "visual"  # Chart/graph
    EXECUTIVE = "executive"  # Concise summary for C-suite


@dataclass
class FormattedResponse:
    """Formatted response object"""
    response_type: str  # 'text', 'table', 'chart'
    content: Any  # Response content (string, dict, etc.)
    format: ResponseFormat
    metadata: Dict[str, Any]


class ResponseFormatter:
    """
    Claude-quality response formatter
    Generates responses with no preambles, concise, professional tone
    """
    
    def __init__(self):
        # Phrases to avoid (Claude doesn't use these)
        self.avoid_phrases = [
            "I'd be happy to",
            "I'll help you with that",
            "Let me assist you",
            "Here's what I found",
            "I hope this helps",
        ]
    
    def format_conversational(
        self,
        notifications: List[Any],
        entity_name: Optional[str] = None,
        query_context: Optional[str] = None
    ) -> FormattedResponse:
        """
        Format as conversational response (Claude-style)
        
        Args:
            notifications: List of notification objects
            entity_name: Entity name if filtered
            query_context: Original query for context
            
        Returns:
            FormattedResponse with conversational text
        """
        if not notifications:
            content = self._format_no_data_response(entity_name, query_context)
            return FormattedResponse(
                response_type="text",
                content=content,
                format=ResponseFormat.CONVERSATIONAL,
                metadata={"count": 0}
            )
        
        # Group by company
        company_groups = self._group_by_company(notifications)
        
        # Format response
        response_parts = []
        
        for company, notifs in company_groups.items():
            count = len(notifs)
            
            # Company header (no excessive formatting)
            response_parts.append(f"\n{company} ({count} notification{'s' if count != 1 else ''})")
            response_parts.append("=" * (len(company) + len(str(count)) + 20))
            response_parts.append("")
            
            # Notifications
            for n in notifs:
                date = self._safe_get(n, ['Date', 'notice_date'], 'Unknown')
                subject = self._safe_get(n, ['Nature', 'notice_type', 'subject'], 'Notification')
                summary = self._safe_get(n, ['Summary', 'summary'], '')
                
                if date != 'Unknown':
                    date = str(date)
                
                response_parts.append(f"Date: {date}")
                
                if subject and subject != "NIL":
                    response_parts.append(f"Subject: {subject}")
                
                if summary and summary != "NIL":
                    response_parts.append(f"Summary: {summary}")
                
                response_parts.append("")  # Blank line between notifications
        
        content = "\n".join(response_parts)
        
        return FormattedResponse(
            response_type="text",
            content=content,
            format=ResponseFormat.CONVERSATIONAL,
            metadata={"count": len(notifications), "companies": len(company_groups)}
        )
    
    def format_tabular(
        self,
        notifications: List[Any],
        entity_name: Optional[str] = None,
        columns: Optional[List[str]] = None
    ) -> FormattedResponse:
        """
        Format as table response
        
        Args:
            notifications: List of notification objects
            entity_name: Entity name if filtered
            columns: Custom column names
            
        Returns:
            FormattedResponse with table structure
        """
        if not notifications:
            return FormattedResponse(
                response_type="table",
                content={
                    "title": f"Notifications for {entity_name}" if entity_name else "Search Results",
                    "columns": columns or ["Company", "Date", "Subject", "Summary"],
                    "rows": [],
                    "message": "No notifications found"
                },
                format=ResponseFormat.TABULAR,
                metadata={"count": 0}
            )
        
        # Default columns
        if columns is None:
            columns = ["Company", "Date", "Subject", "Summary"]
        
        # Build rows
        rows = []
        for n in notifications:
            company = self._safe_get(n, ['EntityName', 'entity_name'], 'Unknown')
            date = self._safe_get(n, ['Date', 'notice_date'], 'Unknown')
            subject = self._safe_get(n, ['Nature', 'notice_type', 'subject'], 'Unknown')
            summary = self._safe_get(n, ['Summary', 'summary'], '')
            
            if date != 'Unknown':
                date = str(date)
            
            # Shorten summary for table view
            short_summary = self._shorten_summary(summary)
            
            rows.append([company, date, subject, short_summary])
        
        content = {
            "title": f"Notifications for {entity_name}" if entity_name else "Search Results",
            "columns": columns,
            "rows": rows,
            "total_count": len(rows)
        }
        
        return FormattedResponse(
            response_type="table",
            content=content,
            format=ResponseFormat.TABULAR,
            metadata={"count": len(notifications)}
        )
    
    def format_executive(
        self,
        notifications: List[Any],
        entity_name: Optional[str] = None
    ) -> FormattedResponse:
        """
        Format as executive summary (C-suite friendly)
        
        Args:
            notifications: List of notification objects
            entity_name: Entity name if filtered
            
        Returns:
            FormattedResponse with executive summary
        """
        if not notifications:
            content = f"No recent notifications for {entity_name}." if entity_name else "No notifications found."
            return FormattedResponse(
                response_type="text",
                content=content,
                format=ResponseFormat.EXECUTIVE,
                metadata={"count": 0}
            )
        
        # Executive summary structure
        company_groups = self._group_by_company(notifications)
        
        summary_parts = []
        
        # High-level overview
        total_count = len(notifications)
        company_count = len(company_groups)
        
        if entity_name:
            summary_parts.append(f"{entity_name}: {total_count} notification{'s' if total_count != 1 else ''}")
        else:
            summary_parts.append(f"Overview: {total_count} notifications across {company_count} entities")
        
        summary_parts.append("")
        
        # Key highlights (most recent per company)
        summary_parts.append("Key Highlights:")
        for company, notifs in list(company_groups.items())[:5]:  # Top 5 companies
            most_recent = notifs[0]  # Assuming sorted by date desc
            date = self._safe_get(most_recent, ['Date', 'notice_date'], 'Unknown')
            subject = self._safe_get(most_recent, ['Nature', 'notice_type'], 'Update')
            
            if date != 'Unknown':
                date = str(date)
            
            summary_parts.append(f"• {company} ({date}): {subject}")
        
        content = "\n".join(summary_parts)
        
        return FormattedResponse(
            response_type="text",
            content=content,
            format=ResponseFormat.EXECUTIVE,
            metadata={
                "count": total_count,
                "companies": company_count,
                "format": "executive"
            }
        )
    
    def _format_no_data_response(
        self,
        entity_name: Optional[str],
        query_context: Optional[str]
    ) -> str:
        """Format response when no data found (Claude-style)"""
        if entity_name:
            return f"No notifications found for {entity_name}."
        elif query_context:
            return f"No notifications match your query."
        else:
            return "No notifications found."
    
    def _group_by_company(self, notifications: List[Any]) -> Dict[str, List[Any]]:
        """Group notifications by company"""
        groups = {}
        for n in notifications:
            company = self._safe_get(n, ['EntityName', 'entity_name'], 'Unknown')
            if company not in groups:
                groups[company] = []
            groups[company].append(n)
        return groups
    
    def _safe_get(self, obj: Any, attr_names: List[str], default: Any) -> Any:
        """Safely get attribute from object or dict"""
        for attr in attr_names:
            if hasattr(obj, attr):
                val = getattr(obj, attr)
                if val is not None:
                    return val
            elif isinstance(obj, dict):
                val = obj.get(attr)
                if val is not None:
                    return val
        return default
    
    def _shorten_summary(self, summary: str, max_length: int = 100) -> str:
        """Shorten summary for table view"""
        if not summary or summary == "NIL":
            return "No summary available"
        
        # Extract first sentence or key points
        sentences = re.split(r'[.\\n]', summary)
        key_points = [s.strip() for s in sentences if s.strip()]
        
        if not key_points:
            return "No summary available"
        
        # Take first point, truncate if too long
        first_point = key_points[0]
        if len(first_point) > max_length:
            return first_point[:max_length-3] + "..."
        
        return first_point


# Global instance
_response_formatter = None

def get_response_formatter() -> ResponseFormatter:
    """Get singleton instance of ResponseFormatter"""
    global _response_formatter
    if _response_formatter is None:
        _response_formatter = ResponseFormatter()
    return _response_formatter
