"""
Chart Generator - Intelligent chart configuration generation
Auto-detects chart type based on query intent and data characteristics
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import Counter


class ChartType(Enum):
    """Chart types"""
    LINE = "line"  # Temporal trends
    BAR = "bar"  # Comparisons
    CANDLESTICK = "candlestick"  # Stock data (OHLC)
    PIE = "pie"  # Composition/distribution
    AREA = "area"  # Cumulative trends
    SCATTER = "scatter"  # Correlation


@dataclass
class ChartConfig:
    """Chart configuration"""
    chart_type: ChartType
    title: str
    x_axis: str
    y_axis: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]


class ChartGenerator:
    """
    Intelligent chart generation
    Automatically selects chart type based on data and intent
    """
    
    def generate_chart(
        self,
        notifications: List[Any],
        query_intent: str,
        entity_name: Optional[str] = None
    ) -> ChartConfig:
        """
        Generate chart configuration based on data and intent
        
        Args:
            notifications: List of notification objects
            query_intent: Detected query intent
            entity_name: Entity name if filtered
            
        Returns:
            ChartConfig with chart type and data
        """
        # Detect if temporal data
        has_dates = self._has_temporal_data(notifications)
        
        # Detect if comparative data
        has_multiple_entities = self._has_multiple_entities(notifications)
        
        # Select chart type based on intent and data characteristics
        if "trend" in query_intent.lower() or "over time" in query_intent.lower():
            return self._generate_temporal_chart(notifications, entity_name)
        
        elif "compare" in query_intent.lower() or has_multiple_entities:
            return self._generate_comparative_chart(notifications, entity_name)
        
        elif "distribution" in query_intent.lower() or "composition" in query_intent.lower():
            return self._generate_distribution_chart(notifications, entity_name)
        
        elif has_dates:
            # Default to temporal chart if dates available
            return self._generate_temporal_chart(notifications, entity_name)
        
        else:
            # Default to bar chart
            return self._generate_comparative_chart(notifications, entity_name)
    
    def _generate_temporal_chart(
        self,
        notifications: List[Any],
        entity_name: Optional[str]
    ) -> ChartConfig:
        """Generate line/area chart for temporal trends"""
        # Group by date
        date_counts = Counter()
        
        for n in notifications:
            date = self._safe_get(n, ['Date', 'notice_date'], None)
            if date:
                date_str = str(date)
                date_counts[date_str] += 1
        
        # Sort by date
        sorted_dates = sorted(date_counts.items())
        
        labels = [date for date, _ in sorted_dates]
        values = [count for _, count in sorted_dates]
        
        title = f"Notification Trend - {entity_name}" if entity_name else "Notification Trend"
        
        return ChartConfig(
            chart_type=ChartType.LINE,
            title=title,
            x_axis="Date",
            y_axis="Count",
            data={
                "labels": labels,
                "values": values,
                "datasets": [{
                    "label": entity_name or "Notifications",
                    "data": values
                }]
            },
            metadata={
                "total_count": sum(values),
                "date_range": f"{labels[0]} to {labels[-1]}" if labels else "N/A"
            }
        )
    
    def _generate_comparative_chart(
        self,
        notifications: List[Any],
        entity_name: Optional[str]
    ) -> ChartConfig:
        """Generate bar chart for comparisons"""
        # Group by company
        company_counts = Counter()
        
        for n in notifications:
            company = self._safe_get(n, ['EntityName', 'entity_name'], 'Unknown')
            company_counts[company] += 1
        
        # Sort by count (descending)
        sorted_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Take top 10
        top_companies = sorted_companies[:10]
        
        labels = [company for company, _ in top_companies]
        values = [count for _, count in top_companies]
        
        title = "Notification Count by Company"
        
        return ChartConfig(
            chart_type=ChartType.BAR,
            title=title,
            x_axis="Company",
            y_axis="Count",
            data={
                "labels": labels,
                "values": values,
                "datasets": [{
                    "label": "Notifications",
                    "data": values
                }]
            },
            metadata={
                "total_companies": len(company_counts),
                "showing_top": len(top_companies)
            }
        )
    
    def _generate_distribution_chart(
        self,
        notifications: List[Any],
        entity_name: Optional[str]
    ) -> ChartConfig:
        """Generate pie chart for distribution"""
        # Group by type/nature
        type_counts = Counter()
        
        for n in notifications:
            notice_type = self._safe_get(n, ['Nature', 'notice_type', 'type'], 'Other')
            if notice_type and notice_type != "NIL":
                type_counts[notice_type] += 1
        
        # Sort by count
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Take top 8 (pie charts get cluttered with too many slices)
        top_types = sorted_types[:8]
        
        labels = [type_name for type_name, _ in top_types]
        values = [count for _, count in top_types]
        
        title = f"Notification Distribution - {entity_name}" if entity_name else "Notification Distribution"
        
        return ChartConfig(
            chart_type=ChartType.PIE,
            title=title,
            x_axis="Type",
            y_axis="Count",
            data={
                "labels": labels,
                "values": values,
                "datasets": [{
                    "label": "Distribution",
                    "data": values
                }]
            },
            metadata={
                "total_types": len(type_counts),
                "showing_top": len(top_types)
            }
        )
    
    def _has_temporal_data(self, notifications: List[Any]) -> bool:
        """Check if notifications have temporal data"""
        if not notifications:
            return False
        
        # Check first few notifications for date fields
        for n in notifications[:5]:
            date = self._safe_get(n, ['Date', 'notice_date'], None)
            if date:
                return True
        
        return False
    
    def _has_multiple_entities(self, notifications: List[Any]) -> bool:
        """Check if notifications span multiple entities"""
        if not notifications:
            return False
        
        entities = set()
        for n in notifications:
            entity = self._safe_get(n, ['EntityName', 'entity_name'], None)
            if entity:
                entities.add(entity)
        
        return len(entities) > 1
    
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


# Global instance
_chart_generator = None

def get_chart_generator() -> ChartGenerator:
    """Get singleton instance of ChartGenerator"""
    global _chart_generator
    if _chart_generator is None:
        _chart_generator = ChartGenerator()
    return _chart_generator
