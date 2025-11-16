"""
API cost tracking utilities for the chatPDF system.

This module provides:
- Token counting for different models
- Cost calculation for OpenAI and other providers
- Usage analytics and aggregation
- Cost aggregation by time period
- Export functionality to CSV/JSON
- Real-time cost display helpers
"""

import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import defaultdict
import sqlite3


@dataclass
class UsageRecord:
    """
    Represents a single API usage record.

    Attributes:
        timestamp: When the API call was made
        model: Model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
        provider: Provider name (e.g., 'openai', 'ollama')
        operation: Operation type (e.g., 'completion', 'embedding')
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        total_tokens: Total tokens used
        cost_usd: Cost in USD
        latency_ms: Latency in milliseconds
        metadata: Additional metadata
    """
    timestamp: datetime
    model: str
    provider: str
    operation: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    latency_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ModelPricing:
    """
    Pricing information for different models and providers.
    """

    # OpenAI pricing (per 1K tokens, as of 2024)
    OPENAI_PRICING = {
        # GPT-4 models
        'gpt-4': {
            'prompt': 0.03,
            'completion': 0.06
        },
        'gpt-4-32k': {
            'prompt': 0.06,
            'completion': 0.12
        },
        'gpt-4-turbo': {
            'prompt': 0.01,
            'completion': 0.03
        },
        'gpt-4-turbo-preview': {
            'prompt': 0.01,
            'completion': 0.03
        },
        # GPT-3.5 models
        'gpt-3.5-turbo': {
            'prompt': 0.0005,
            'completion': 0.0015
        },
        'gpt-3.5-turbo-16k': {
            'prompt': 0.003,
            'completion': 0.004
        },
        'gpt-3.5-turbo-instruct': {
            'prompt': 0.0015,
            'completion': 0.002
        },
        # Embeddings
        'text-embedding-ada-002': {
            'prompt': 0.0001,
            'completion': 0.0
        },
        'text-embedding-3-small': {
            'prompt': 0.00002,
            'completion': 0.0
        },
        'text-embedding-3-large': {
            'prompt': 0.00013,
            'completion': 0.0
        },
        # Legacy models
        'text-davinci-003': {
            'prompt': 0.02,
            'completion': 0.02
        },
        'text-davinci-002': {
            'prompt': 0.02,
            'completion': 0.02
        },
    }

    @classmethod
    def get_openai_cost(
        cls,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """
        Calculate cost for OpenAI API usage.

        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Cost in USD
        """
        # Normalize model name
        model_key = model.lower()

        # Handle model aliases
        if 'gpt-4-turbo' in model_key or 'gpt-4-1106' in model_key:
            model_key = 'gpt-4-turbo'
        elif 'gpt-4-32k' in model_key:
            model_key = 'gpt-4-32k'
        elif 'gpt-4' in model_key:
            model_key = 'gpt-4'
        elif 'gpt-3.5-turbo-16k' in model_key:
            model_key = 'gpt-3.5-turbo-16k'
        elif 'gpt-3.5-turbo' in model_key:
            model_key = 'gpt-3.5-turbo'

        pricing = cls.OPENAI_PRICING.get(model_key)

        if not pricing:
            # Unknown model, return 0 or use default
            return 0.0

        prompt_cost = (prompt_tokens / 1000) * pricing['prompt']
        completion_cost = (completion_tokens / 1000) * pricing['completion']

        return prompt_cost + completion_cost

    @classmethod
    def get_ollama_cost(cls, model: str, tokens: int) -> float:
        """
        Calculate cost for Ollama (local models = free).

        Args:
            model: Model name
            tokens: Number of tokens

        Returns:
            Cost in USD (always 0.0 for local models)
        """
        return 0.0

    @classmethod
    def get_huggingface_cost(
        cls,
        model: str,
        tokens: int,
        is_api: bool = False
    ) -> float:
        """
        Calculate cost for HuggingFace.

        Args:
            model: Model name
            tokens: Number of tokens
            is_api: Whether using HuggingFace API (vs local)

        Returns:
            Cost in USD
        """
        if not is_api:
            # Local HuggingFace models are free
            return 0.0

        # HuggingFace API pricing varies by model
        # Using average estimate: $0.0002 per 1K tokens
        return (tokens / 1000) * 0.0002


class CostTracker:
    """
    Track and analyze API usage costs.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize cost tracker.

        Args:
            db_path: Path to SQLite database for persistent storage
        """
        self.records: List[UsageRecord] = []
        self.db_path = db_path

        if db_path:
            self._init_database()

    def _init_database(self):
        """Initialize SQLite database for cost tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model TEXT NOT NULL,
                provider TEXT NOT NULL,
                operation TEXT NOT NULL,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                cost_usd REAL,
                latency_ms REAL,
                metadata TEXT
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON usage_records(timestamp)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_model
            ON usage_records(model)
        ''')

        conn.commit()
        conn.close()

    def record_usage(
        self,
        model: str,
        provider: str,
        operation: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UsageRecord:
        """
        Record API usage.

        Args:
            model: Model name
            provider: Provider name
            operation: Operation type
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            latency_ms: Latency in milliseconds
            metadata: Additional metadata

        Returns:
            UsageRecord instance
        """
        total_tokens = prompt_tokens + completion_tokens

        # Calculate cost based on provider
        if provider.lower() == 'openai':
            cost = ModelPricing.get_openai_cost(model, prompt_tokens, completion_tokens)
        elif provider.lower() == 'ollama':
            cost = ModelPricing.get_ollama_cost(model, total_tokens)
        elif provider.lower() == 'huggingface':
            is_api = metadata.get('is_api', False) if metadata else False
            cost = ModelPricing.get_huggingface_cost(model, total_tokens, is_api)
        else:
            cost = 0.0

        record = UsageRecord(
            timestamp=datetime.now(),
            model=model,
            provider=provider,
            operation=operation,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            metadata=metadata or {}
        )

        self.records.append(record)

        # Save to database if configured
        if self.db_path:
            self._save_record(record)

        return record

    def _save_record(self, record: UsageRecord):
        """Save record to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO usage_records (
                timestamp, model, provider, operation,
                prompt_tokens, completion_tokens, total_tokens,
                cost_usd, latency_ms, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.timestamp.isoformat(),
            record.model,
            record.provider,
            record.operation,
            record.prompt_tokens,
            record.completion_tokens,
            record.total_tokens,
            record.cost_usd,
            record.latency_ms,
            json.dumps(record.metadata)
        ))

        conn.commit()
        conn.close()

    def get_total_cost(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> float:
        """
        Get total cost for a time period.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            provider: Filter by provider
            model: Filter by model

        Returns:
            Total cost in USD
        """
        filtered_records = self._filter_records(start_date, end_date, provider, model)
        return sum(record.cost_usd for record in filtered_records)

    def get_total_tokens(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> int:
        """
        Get total tokens used.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            provider: Filter by provider
            model: Filter by model

        Returns:
            Total tokens
        """
        filtered_records = self._filter_records(start_date, end_date, provider, model)
        return sum(record.total_tokens for record in filtered_records)

    def get_usage_by_model(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get usage statistics grouped by model.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Dictionary with model statistics
        """
        filtered_records = self._filter_records(start_date, end_date)

        stats = defaultdict(lambda: {
            'total_tokens': 0,
            'total_cost': 0.0,
            'call_count': 0,
            'avg_latency_ms': 0.0
        })

        for record in filtered_records:
            model_stats = stats[record.model]
            model_stats['total_tokens'] += record.total_tokens
            model_stats['total_cost'] += record.cost_usd
            model_stats['call_count'] += 1
            model_stats['avg_latency_ms'] += record.latency_ms

        # Calculate averages
        for model_stats in stats.values():
            if model_stats['call_count'] > 0:
                model_stats['avg_latency_ms'] /= model_stats['call_count']

        return dict(stats)

    def get_usage_by_day(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get usage statistics grouped by day.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Dictionary with daily statistics
        """
        filtered_records = self._filter_records(start_date, end_date)

        stats = defaultdict(lambda: {
            'total_tokens': 0,
            'total_cost': 0.0,
            'call_count': 0
        })

        for record in filtered_records:
            day_key = record.timestamp.strftime('%Y-%m-%d')
            day_stats = stats[day_key]
            day_stats['total_tokens'] += record.total_tokens
            day_stats['total_cost'] += record.cost_usd
            day_stats['call_count'] += 1

        return dict(stats)

    def get_recent_usage(self, hours: int = 24) -> List[UsageRecord]:
        """
        Get usage records from the last N hours.

        Args:
            hours: Number of hours to look back

        Returns:
            List of usage records
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        return [r for r in self.records if r.timestamp >= cutoff]

    def _filter_records(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> List[UsageRecord]:
        """Filter records by criteria."""
        filtered = self.records

        if start_date:
            filtered = [r for r in filtered if r.timestamp >= start_date]

        if end_date:
            filtered = [r for r in filtered if r.timestamp <= end_date]

        if provider:
            filtered = [r for r in filtered if r.provider.lower() == provider.lower()]

        if model:
            filtered = [r for r in filtered if r.model.lower() == model.lower()]

        return filtered

    def export_to_csv(self, file_path: str):
        """
        Export usage records to CSV.

        Args:
            file_path: Output CSV file path
        """
        with open(file_path, 'w', newline='') as csvfile:
            fieldnames = [
                'timestamp', 'model', 'provider', 'operation',
                'prompt_tokens', 'completion_tokens', 'total_tokens',
                'cost_usd', 'latency_ms'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for record in self.records:
                row = record.to_dict()
                row.pop('metadata')  # Don't export metadata to CSV
                writer.writerow(row)

    def export_to_json(self, file_path: str):
        """
        Export usage records to JSON.

        Args:
            file_path: Output JSON file path
        """
        data = [record.to_dict() for record in self.records]

        with open(file_path, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=2)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get overall usage summary.

        Returns:
            Summary statistics
        """
        if not self.records:
            return {
                'total_cost': 0.0,
                'total_tokens': 0,
                'total_calls': 0,
                'avg_cost_per_call': 0.0,
                'avg_tokens_per_call': 0.0,
                'avg_latency_ms': 0.0,
                'models_used': [],
                'providers_used': []
            }

        total_cost = sum(r.cost_usd for r in self.records)
        total_tokens = sum(r.total_tokens for r in self.records)
        total_calls = len(self.records)
        avg_latency = sum(r.latency_ms for r in self.records) / total_calls

        models_used = list(set(r.model for r in self.records))
        providers_used = list(set(r.provider for r in self.records))

        return {
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'total_calls': total_calls,
            'avg_cost_per_call': total_cost / total_calls if total_calls > 0 else 0.0,
            'avg_tokens_per_call': total_tokens / total_calls if total_calls > 0 else 0.0,
            'avg_latency_ms': avg_latency,
            'models_used': models_used,
            'providers_used': providers_used
        }

    def format_cost_display(self, cost: float) -> str:
        """
        Format cost for display.

        Args:
            cost: Cost in USD

        Returns:
            Formatted cost string
        """
        if cost < 0.01:
            return f"${cost:.4f}"
        elif cost < 1.0:
            return f"${cost:.3f}"
        else:
            return f"${cost:.2f}"

    def get_cost_breakdown(self) -> Dict[str, Any]:
        """
        Get detailed cost breakdown.

        Returns:
            Cost breakdown by various dimensions
        """
        return {
            'by_model': self.get_usage_by_model(),
            'by_day': self.get_usage_by_day(),
            'summary': self.get_summary()
        }


# Example usage
if __name__ == "__main__":
    # Initialize tracker
    tracker = CostTracker()

    # Record some usage
    tracker.record_usage(
        model="gpt-4",
        provider="openai",
        operation="completion",
        prompt_tokens=100,
        completion_tokens=200,
        latency_ms=1500.0
    )

    tracker.record_usage(
        model="llama3:8b",
        provider="ollama",
        operation="completion",
        prompt_tokens=150,
        completion_tokens=250,
        latency_ms=2000.0
    )

    # Get summary
    summary = tracker.get_summary()
    print("Usage Summary:")
    print(json.dumps(summary, indent=2))

    # Get cost by model
    by_model = tracker.get_usage_by_model()
    print("\nUsage by Model:")
    print(json.dumps(by_model, indent=2))
