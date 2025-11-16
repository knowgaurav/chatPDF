"""
General helper utilities for the chatPDF system.

This module provides:
- File handling helpers
- Date/time formatting
- JSON serialization helpers
- Error formatting
- Response formatters
- General utility functions
"""

import json
import os
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import traceback
from decimal import Decimal


class DateTimeHelper:
    """
    Date and time formatting utilities.
    """

    @staticmethod
    def format_datetime(
        dt: datetime,
        format_type: str = "iso"
    ) -> str:
        """
        Format datetime object.

        Args:
            dt: Datetime object
            format_type: Format type ('iso', 'human', 'date', 'time')

        Returns:
            Formatted datetime string
        """
        if not dt:
            return ""

        if format_type == "iso":
            return dt.isoformat()
        elif format_type == "human":
            return dt.strftime("%B %d, %Y at %I:%M %p")
        elif format_type == "date":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "time":
            return dt.strftime("%H:%M:%S")
        elif format_type == "compact":
            return dt.strftime("%Y%m%d_%H%M%S")
        else:
            return dt.isoformat()

    @staticmethod
    def parse_datetime(date_string: str) -> Optional[datetime]:
        """
        Parse datetime string.

        Args:
            date_string: Date string in various formats

        Returns:
            Datetime object or None if parsing fails
        """
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def format_timedelta(td: timedelta) -> str:
        """
        Format timedelta in human-readable format.

        Args:
            td: Timedelta object

        Returns:
            Human-readable string
        """
        total_seconds = int(td.total_seconds())

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")

        return " ".join(parts)

    @staticmethod
    def get_time_ago(dt: datetime) -> str:
        """
        Get 'time ago' string (e.g., '2 hours ago').

        Args:
            dt: Datetime object

        Returns:
            Time ago string
        """
        now = datetime.now()
        diff = now - dt

        seconds = diff.total_seconds()

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif seconds < 31536000:
            months = int(seconds / 2592000)
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = int(seconds / 31536000)
            return f"{years} year{'s' if years != 1 else ''} ago"


class FileHelper:
    """
    File handling utilities.
    """

    @staticmethod
    def ensure_directory(directory: str) -> Path:
        """
        Ensure directory exists, create if not.

        Args:
            directory: Directory path

        Returns:
            Path object
        """
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = "sha256") -> str:
        """
        Calculate file hash.

        Args:
            file_path: Path to file
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256')

        Returns:
            Hash hex string
        """
        if algorithm == "md5":
            hasher = hashlib.md5()
        elif algorithm == "sha1":
            hasher = hashlib.sha1()
        else:
            hasher = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)

        return hasher.hexdigest()

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string (e.g., '1.5 MB')
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.2f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.2f} GB"

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        Get file extension without dot.

        Args:
            filename: Filename

        Returns:
            Extension (lowercase, without dot)
        """
        return Path(filename).suffix.lower().lstrip('.')

    @staticmethod
    def generate_unique_filename(
        original_filename: str,
        directory: Optional[str] = None
    ) -> str:
        """
        Generate unique filename to avoid collisions.

        Args:
            original_filename: Original filename
            directory: Directory to check for existing files

        Returns:
            Unique filename
        """
        name = Path(original_filename).stem
        ext = Path(original_filename).suffix

        # Add timestamp and random suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = uuid.uuid4().hex[:8]

        unique_name = f"{name}_{timestamp}_{random_suffix}{ext}"

        # If directory provided, ensure uniqueness
        if directory:
            counter = 1
            while os.path.exists(os.path.join(directory, unique_name)):
                unique_name = f"{name}_{timestamp}_{random_suffix}_{counter}{ext}"
                counter += 1

        return unique_name

    @staticmethod
    def safe_delete_file(file_path: str) -> bool:
        """
        Safely delete a file.

        Args:
            file_path: Path to file

        Returns:
            True if deleted, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception:
            pass

        return False

    @staticmethod
    def get_directory_size(directory: str) -> int:
        """
        Calculate total size of directory.

        Args:
            directory: Directory path

        Returns:
            Total size in bytes
        """
        total_size = 0

        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)

        return total_size


class JSONHelper:
    """
    JSON serialization utilities.
    """

    @staticmethod
    def safe_json_dumps(
        obj: Any,
        pretty: bool = False,
        default: Optional[callable] = None
    ) -> str:
        """
        Safely serialize object to JSON.

        Args:
            obj: Object to serialize
            pretty: Whether to pretty-print
            default: Default function for non-serializable objects

        Returns:
            JSON string
        """
        def default_handler(o):
            if default:
                try:
                    return default(o)
                except:
                    pass

            # Handle common non-serializable types
            if isinstance(o, datetime):
                return o.isoformat()
            elif isinstance(o, Decimal):
                return float(o)
            elif isinstance(o, bytes):
                return o.decode('utf-8', errors='ignore')
            elif hasattr(o, '__dict__'):
                return o.__dict__
            else:
                return str(o)

        try:
            if pretty:
                return json.dumps(obj, indent=2, default=default_handler)
            else:
                return json.dumps(obj, default=default_handler)
        except Exception as e:
            return json.dumps({'error': f'Serialization failed: {str(e)}'})

    @staticmethod
    def safe_json_loads(json_string: str, default: Any = None) -> Any:
        """
        Safely parse JSON string.

        Args:
            json_string: JSON string
            default: Default value if parsing fails

        Returns:
            Parsed object or default
        """
        try:
            return json.loads(json_string)
        except Exception:
            return default


class ErrorFormatter:
    """
    Error formatting utilities.
    """

    @staticmethod
    def format_error(
        error: Exception,
        include_traceback: bool = False
    ) -> Dict[str, Any]:
        """
        Format exception as dictionary.

        Args:
            error: Exception object
            include_traceback: Whether to include traceback

        Returns:
            Error dictionary
        """
        error_dict = {
            'error_type': type(error).__name__,
            'error_message': str(error),
        }

        if include_traceback:
            error_dict['traceback'] = traceback.format_exc()

        # Add custom fields if available
        if hasattr(error, 'field'):
            error_dict['field'] = error.field

        if hasattr(error, 'code'):
            error_dict['code'] = error.code

        return error_dict

    @staticmethod
    def format_error_message(error: Exception) -> str:
        """
        Format error as user-friendly message.

        Args:
            error: Exception object

        Returns:
            Error message string
        """
        error_type = type(error).__name__

        # Map common exceptions to friendly messages
        friendly_messages = {
            'FileNotFoundError': 'The requested file was not found.',
            'PermissionError': 'Permission denied to access the file.',
            'ValueError': 'Invalid value provided.',
            'KeyError': 'Required field is missing.',
            'TypeError': 'Invalid data type.',
            'ConnectionError': 'Failed to connect to the service.',
            'TimeoutError': 'The operation timed out.',
        }

        friendly_msg = friendly_messages.get(error_type)

        if friendly_msg:
            return f"{friendly_msg} ({str(error)})"
        else:
            return str(error)


class ResponseFormatter:
    """
    API response formatting utilities.
    """

    @staticmethod
    def success_response(
        data: Any,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format success response.

        Args:
            data: Response data
            message: Optional success message
            metadata: Optional metadata

        Returns:
            Response dictionary
        """
        response = {
            'success': True,
            'data': data
        }

        if message:
            response['message'] = message

        if metadata:
            response['metadata'] = metadata

        return response

    @staticmethod
    def error_response(
        error: Union[str, Exception],
        code: Optional[str] = None,
        status_code: int = 400
    ) -> Dict[str, Any]:
        """
        Format error response.

        Args:
            error: Error message or exception
            code: Error code
            status_code: HTTP status code

        Returns:
            Response dictionary
        """
        if isinstance(error, Exception):
            error_msg = ErrorFormatter.format_error_message(error)
            error_code = code or type(error).__name__
        else:
            error_msg = error
            error_code = code or 'ERROR'

        return {
            'success': False,
            'error': {
                'code': error_code,
                'message': error_msg,
                'status_code': status_code
            }
        }

    @staticmethod
    def paginated_response(
        items: List[Any],
        total: int,
        page: int,
        page_size: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format paginated response.

        Args:
            items: Items for current page
            total: Total number of items
            page: Current page number
            page_size: Items per page
            metadata: Optional metadata

        Returns:
            Response dictionary
        """
        total_pages = (total + page_size - 1) // page_size

        response = {
            'success': True,
            'data': {
                'items': items,
                'pagination': {
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
        }

        if metadata:
            response['metadata'] = metadata

        return response


class CostFormatter:
    """
    Cost formatting utilities.
    """

    @staticmethod
    def format_cost(cost: float, currency: str = "USD") -> str:
        """
        Format cost for display.

        Args:
            cost: Cost amount
            currency: Currency code

        Returns:
            Formatted cost string
        """
        if cost < 0.01:
            return f"${cost:.4f}"
        elif cost < 1.0:
            return f"${cost:.3f}"
        else:
            return f"${cost:.2f}"

    @staticmethod
    def format_tokens(tokens: int) -> str:
        """
        Format token count for display.

        Args:
            tokens: Number of tokens

        Returns:
            Formatted token string
        """
        if tokens < 1000:
            return f"{tokens} tokens"
        elif tokens < 1000000:
            return f"{tokens / 1000:.1f}K tokens"
        else:
            return f"{tokens / 1000000:.1f}M tokens"


class IDGenerator:
    """
    Unique ID generation utilities.
    """

    @staticmethod
    def generate_uuid() -> str:
        """
        Generate UUID v4.

        Returns:
            UUID string
        """
        return str(uuid.uuid4())

    @staticmethod
    def generate_short_id(length: int = 8) -> str:
        """
        Generate short random ID.

        Args:
            length: Length of ID

        Returns:
            Short ID string
        """
        return uuid.uuid4().hex[:length]

    @staticmethod
    def generate_timestamp_id() -> str:
        """
        Generate timestamp-based ID.

        Returns:
            Timestamp ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = uuid.uuid4().hex[:8]
        return f"{timestamp}_{random_suffix}"


# Convenience functions
def format_datetime(dt: datetime, format_type: str = "iso") -> str:
    """Convenience function for datetime formatting."""
    return DateTimeHelper.format_datetime(dt, format_type)


def format_file_size(size_bytes: int) -> str:
    """Convenience function for file size formatting."""
    return FileHelper.format_file_size(size_bytes)


def format_cost(cost: float) -> str:
    """Convenience function for cost formatting."""
    return CostFormatter.format_cost(cost)


def safe_json_dumps(obj: Any, pretty: bool = False) -> str:
    """Convenience function for JSON serialization."""
    return JSONHelper.safe_json_dumps(obj, pretty)


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Convenience function for JSON parsing."""
    return JSONHelper.safe_json_loads(json_string, default)


def format_error(error: Exception, include_traceback: bool = False) -> Dict[str, Any]:
    """Convenience function for error formatting."""
    return ErrorFormatter.format_error(error, include_traceback)


def ensure_directory(directory: str) -> Path:
    """Convenience function to ensure directory exists."""
    return FileHelper.ensure_directory(directory)


def generate_uuid() -> str:
    """Convenience function to generate UUID."""
    return IDGenerator.generate_uuid()


# Example usage
if __name__ == "__main__":
    # Test datetime formatting
    now = datetime.now()
    print(f"ISO format: {format_datetime(now, 'iso')}")
    print(f"Human format: {format_datetime(now, 'human')}")
    print(f"Time ago: {DateTimeHelper.get_time_ago(now - timedelta(hours=2))}")

    # Test file size formatting
    print(f"File size: {format_file_size(1536789)}")

    # Test cost formatting
    print(f"Cost: {format_cost(0.00123)}")

    # Test JSON serialization
    data = {
        'timestamp': now,
        'size': 1024,
        'name': 'test'
    }
    print(f"JSON: {safe_json_dumps(data, pretty=True)}")

    # Test response formatting
    success = ResponseFormatter.success_response(
        data={'message': 'Hello'},
        message='Operation completed'
    )
    print(f"Success response: {safe_json_dumps(success, pretty=True)}")

    error = ResponseFormatter.error_response(
        error='Something went wrong',
        code='INVALID_INPUT'
    )
    print(f"Error response: {safe_json_dumps(error, pretty=True)}")
