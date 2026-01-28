#!/usr/bin/env python3
"""
Mock LLM response module for testing
"""
import json
from typing import List

def generate_mock_response(system_prompt: str, user_prompt: str) -> str:
    """
    Generate a mock response based on the prompts
    """
    # Extract relevant information from the user prompt
    if "notifications for Tata Motors" in user_prompt:
        return "Tata Motors Ltd had a notification on 2025-08-10. The nature of the notification was related to quarterly financial results. For more details, please check the official BSE website."
    elif "regulatory updates from 01-09-2025" in user_prompt:
        return "On 01-09-2025, SEBI issued updates regarding disclosure requirements for listed companies. The update focuses on enhanced transparency in financial reporting."
    elif "monetary policy updates from 01-09-2025" in user_prompt:
        return "RBI announced monetary policy updates on 01-09-2025. The key changes include adjustments to repo rate and cash reserve ratio to manage inflation."
    else:
        # Extract company names and dates if possible
        import re
        companies = re.findall(r'notifications for ([A-Za-z\s]+)', user_prompt)
        dates = re.findall(r'(\d{4}-\d{2}-\d{2})', user_prompt)
        
        if companies and dates:
            return f"{companies[0]} had a notification on {dates[0]}. The details of the notification are not specified in the database."
        elif dates:
            return f"On {dates[0]}, there were regulatory updates. Please check the official sources for detailed information."
        else:
            return "I found some notifications in the database. Please be more specific about the company or date you're interested in."

def format_notifications_for_mock(notifications: List) -> str:
    """
    Format notifications for mock LLM consumption
    """
    if not notifications:
        return "No relevant notifications found."
    
    formatted = ""
    for i, notification in enumerate(notifications, 1):
        # Handle different notification types - check if it's a dict or object
        if isinstance(notification, dict):
            # Handle dict objects
            if 'EntityName' in notification:
                # BSE notification
                formatted += f"[{i}] Entity: {notification.get('EntityName', 'Unknown')}\n"
                formatted += f"    Date: {notification.get('Date', 'Unknown')}\n"
                formatted += f"    Nature: {notification.get('Nature', 'Unknown')}\n"
                formatted += f"    Summary: {notification.get('Summary', 'No summary available')}\n"
                formatted += f"    Link: {notification.get('Link', 'No link available')}\n"
            elif 'date_key' in notification:
                # SEBI notification
                formatted += f"[{i}] Entity: SEBI Regulatory Update\n"
                formatted += f"    Date: {notification.get('date_key', 'Unknown')}\n"
                formatted += f"    Summary: {notification.get('summary', 'No summary available')}\n"
                formatted += f"    Link: {notification.get('pdf_link', 'No link available')}\n"
            elif 'run_date' in notification:
                # RBI notification
                formatted += f"[{i}] Entity: RBI Monetary Policy Update\n"
                formatted += f"    Date: {notification.get('run_date', 'Unknown')}\n"
                formatted += f"    Summary: {notification.get('summary', 'No summary available')}\n"
                formatted += f"    Link: {notification.get('pdf_link', 'No link available')}\n"
            else:
                # Generic notification
                formatted += f"[{i}] Entity: Unknown\n"
                formatted += f"    Summary: {str(notification)}\n"
        else:
            # Handle object attributes
            if hasattr(notification, 'EntityName'):
                # BSE notification
                formatted += f"[{i}] Entity: {notification.EntityName}\n"
                formatted += f"    Date: {notification.Date}\n"
                formatted += f"    Nature: {notification.Nature}\n"
                formatted += f"    Summary: {notification.Summary}\n"
                formatted += f"    Link: {notification.Link}\n"
            elif hasattr(notification, 'date_key'):
                # SEBI notification
                formatted += f"[{i}] Entity: SEBI Regulatory Update\n"
                formatted += f"    Date: {notification.date_key}\n"
                formatted += f"    Summary: {notification.summary}\n"
                formatted += f"    Link: {notification.pdf_link}\n"
            elif hasattr(notification, 'run_date'):
                # RBI notification
                formatted += f"[{i}] Entity: RBI Monetary Policy Update\n"
                formatted += f"    Date: {notification.run_date}\n"
                formatted += f"    Summary: {notification.summary}\n"
                formatted += f"    Link: {notification.pdf_link}\n"
            else:
                # Generic notification
                formatted += f"[{i}] Entity: Unknown\n"
                formatted += f"    Summary: {str(notification)}\n"
        formatted += "\n"
    
    return formatted