"""
Natural Language Query Parser for Maya Analytics
Converts user questions into structured analytics queries
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.modules.shared.llm_assistant import llm_assistant
from app.modules.shared.sessions import Session


class QueryParser:
    """Parse natural language analytics queries into structured format"""
    
    # Supported metrics
    METRICS = {
        "revenue": ["revenue", "income", "sales", "earnings", "ገቢ", "galii"],
        "customers": ["customers", "clients", "users", "ደንበኞች", "maamiltota"],
        "transactions": ["transactions", "payments", "transfers", "ግብይቶች", "daldaltoota"],
        "loans": ["loans", "credit", "lending", "ብድር", "liqeessaa"],
        "deposits": ["deposits", "savings", "ተቀማጭ", "kuusaa"],
        "accounts": ["accounts", "መለያዎች", "herregaa"]
    }
    
    # Chart types
    CHART_TYPES = {
        "bar": ["bar", "bars", "column", "columns", "በር", "ulee"],
        "line": ["line", "trend", "time series", "መስመር", "sarara"],
        "pie": ["pie", "donut", "circle", "ፓይ", "paayii"],
        "table": ["table", "list", "grid", "ሰንጠረዥ", "gabatee"],
        "area": ["area", "filled", "ቦታ", "bakka"]
    }
    
    # Time periods
    TIME_PERIODS = {
        "today": 0,
        "yesterday": 1,
        "last_week": 7,
        "last_month": 30,
        "last_quarter": 90,
        "last_year": 365,
        "this_week": 7,
        "this_month": 30,
        "this_quarter": 90,
        "this_year": 365
    }
    
    # Aggregation types
    AGGREGATIONS = {
        "sum": ["total", "sum", "ጠቅላላ", "ida'ama"],
        "average": ["average", "mean", "avg", "አማካይ", "giddu-galeessa"],
        "count": ["count", "number", "ብዛት", "baay'ina"],
        "max": ["maximum", "max", "highest", "ከፍተኛ", "guddaa"],
        "min": ["minimum", "min", "lowest", "ዝቅተኛ", "xiqqaa"]
    }
    
    # Group by options
    GROUP_BY = {
        "branch": ["branch", "branches", "location", "ቅርንጫፍ", "damee"],
        "date": ["date", "day", "daily", "ቀን", "guyyaa"],
        "month": ["month", "monthly", "ወር", "ji'a"],
        "quarter": ["quarter", "quarterly", "ሩብ", "kurmaana"],
        "year": ["year", "yearly", "annual", "ዓመት", "waggaa"],
        "product": ["product", "service", "ምርት", "oomisha"],
        "customer_type": ["customer type", "segment", "የደንበኛ ዓይነት", "gosa maamiltootaa"]
    }
    
    def __init__(self):
        self.llm = llm_assistant
    
    async def parse_query(self, query: str, language: str = "en", bank_id: str = "dashen") -> Dict[str, Any]:
        """
        Parse natural language query into structured format
        
        Args:
            query: Natural language question
            language: User's language
            bank_id: Bank identifier
            
        Returns:
            Structured query parameters
        """
        # First, try rule-based parsing for common patterns
        rule_based_result = self._rule_based_parse(query, language)
        
        # If rule-based parsing is incomplete, use LLM
        if not rule_based_result.get("metrics") or not rule_based_result.get("chart_type"):
            llm_result = await self._llm_parse(query, language)
            # Merge results, preferring LLM for missing fields
            for key, value in llm_result.items():
                if not rule_based_result.get(key):
                    rule_based_result[key] = value
        
        # Validate and normalize the result
        result = self._normalize_query(rule_based_result)
        
        return result
    
    def _rule_based_parse(self, query: str, language: str) -> Dict[str, Any]:
        """Fast rule-based parsing for common patterns"""
        query_lower = query.lower()
        result = {
            "original_query": query,
            "language": language,
            "metrics": [],
            "chart_type": None,
            "date_range": None,
            "branches": [],
            "group_by": None,
            "aggregation": "sum",
            "filters": {}
        }
        
        # Extract metrics
        for metric, keywords in self.METRICS.items():
            if any(keyword in query_lower for keyword in keywords):
                result["metrics"].append(metric)
        
        # Extract chart type
        for chart_type, keywords in self.CHART_TYPES.items():
            if any(keyword in query_lower for keyword in keywords):
                result["chart_type"] = chart_type
                break
        
        # Extract time period
        result["date_range"] = self._extract_date_range(query_lower)
        
        # Extract branches/locations
        result["branches"] = self._extract_branches(query_lower)
        
        # Extract grouping
        for group, keywords in self.GROUP_BY.items():
            if any(keyword in query_lower for keyword in keywords):
                result["group_by"] = group
                break
        
        # Extract aggregation
        for agg, keywords in self.AGGREGATIONS.items():
            if any(keyword in query_lower for keyword in keywords):
                result["aggregation"] = agg
                break
        
        return result
    
    def _extract_date_range(self, query: str) -> Dict[str, str]:
        """Extract date range from query"""
        today = datetime.now()
        
        # Check for predefined periods
        for period, days in self.TIME_PERIODS.items():
            if period.replace("_", " ") in query:
                start_date = today - timedelta(days=days)
                return {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": today.strftime("%Y-%m-%d"),
                    "label": period.replace("_", " ").title()
                }
        
        # Check for "last X months/days/years"
        last_pattern = r"last (\d+) (day|week|month|quarter|year)s?"
        match = re.search(last_pattern, query)
        if match:
            count = int(match.group(1))
            unit = match.group(2)
            
            if unit == "day":
                days = count
            elif unit == "week":
                days = count * 7
            elif unit == "month":
                days = count * 30
            elif unit == "quarter":
                days = count * 90
            elif unit == "year":
                days = count * 365
            
            start_date = today - timedelta(days=days)
            return {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": today.strftime("%Y-%m-%d"),
                "label": f"Last {count} {unit}{'s' if count > 1 else ''}"
            }
        
        # Default to last 30 days
        return {
            "start": (today - timedelta(days=30)).strftime("%Y-%m-%d"),
            "end": today.strftime("%Y-%m-%d"),
            "label": "Last 30 Days"
        }
    
    def _extract_branches(self, query: str) -> List[str]:
        """Extract branch names/cities from query"""
        # Ethiopian cities
        cities = [
            "addis ababa", "bahir dar", "mekelle", "hawassa", "gondar",
            "dire dawa", "adama", "jimma", "dessie", "shashamane",
            "አዲስ አበባ", "ባህር ዳር", "መቀሌ", "ሀዋሳ", "ጎንደር"
        ]
        
        branches = []
        for city in cities:
            if city in query:
                # Normalize to English
                city_map = {
                    "አዲስ አበባ": "addis ababa",
                    "ባህር ዳር": "bahir dar",
                    "መቀሌ": "mekelle",
                    "ሀዋሳ": "hawassa",
                    "ጎንደር": "gondar"
                }
                normalized_city = city_map.get(city, city)
                branches.append(normalized_city.title())
        
        return branches
    
    async def _llm_parse(self, query: str, language: str) -> Dict[str, Any]:
        """Use LLM to parse complex queries"""
        prompt = f"""
You are an analytics query parser. Parse this banking analytics question into structured JSON.

Question: "{query}"
Language: {language}

Extract and return ONLY valid JSON with these fields:
{{
    "metrics": ["revenue", "customers", "transactions", "loans", "deposits", "accounts"],
    "chart_type": "bar|line|pie|table|area",
    "group_by": "branch|date|month|quarter|year|product|customer_type",
    "aggregation": "sum|average|count|max|min",
    "branches": ["City Name"],
    "comparison": true/false,
    "top_n": number or null,
    "filters": {{}}
}}

Rules:
- metrics: What to measure (can be multiple)
- chart_type: Best visualization for this query
- group_by: How to group the data
- aggregation: How to aggregate (sum, average, etc.)
- branches: Specific locations mentioned
- comparison: Is this comparing multiple things?
- top_n: If asking for "top 5", "bottom 10", etc.

Return ONLY the JSON, no explanation.
"""
        
        try:
            dummy_session = Session(id="maya-query-parse")
            result = await self.llm.generate_reply(
                session=dummy_session, language=language, message=prompt
            )
            response = result.get("reply", "")
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {}
        except Exception as e:
            print(f"LLM parsing error: {e}")
            return {}
    
    def _normalize_query(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate query parameters"""
        # Ensure metrics is a list
        if not query_params.get("metrics"):
            query_params["metrics"] = ["revenue"]  # Default metric
        
        # Ensure chart_type is set
        if not query_params.get("chart_type"):
            # Auto-select based on query type
            if query_params.get("group_by") in ["branch", "product"]:
                query_params["chart_type"] = "bar"
            elif query_params.get("group_by") in ["date", "month", "year"]:
                query_params["chart_type"] = "line"
            else:
                query_params["chart_type"] = "bar"
        
        # Ensure date_range is set
        if not query_params.get("date_range"):
            query_params["date_range"] = self._extract_date_range("last month")
        
        # Ensure aggregation is set
        if not query_params.get("aggregation"):
            query_params["aggregation"] = "sum"
        
        return query_params
    
    def generate_sql_query(self, parsed_query: Dict[str, Any], bank_id: str) -> str:
        """Generate SQL query from parsed parameters"""
        # This will be implemented in the service layer
        # Just a placeholder to show the concept
        pass


# Global instance
query_parser = QueryParser()
