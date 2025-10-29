import logging
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import traceback
import sys
import config

class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Log category enumeration."""
    SYSTEM = "system"
    AUTH = "auth"
    REGISTRATION = "registration"
    TRAINING = "training"
    INFERENCE = "inference"
    API = "api"
    DATABASE = "database"
    FILE = "file"
    WEBSOCKET = "websocket"

class LoggingService:
    """Centralized logging service for SmartCAPI application."""
    
    def __init__(self):
        self.logs_dir = config.LOGS_DIR
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize loggers
        self.system_logger = self._setup_logger('system', config.LOG_FILE)
        self.json_logs = {}
        self.csv_logs = {}
        
        # Setup specialized logs
        self._setup_specialized_logs()
    
    def _setup_logger(self, name: str, log_file: Path) -> logging.Logger:
        """
        Setup a logger with file and console handlers.
        
        Args:
            name: Logger name
            log_file: Path to log file
        
        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _setup_specialized_logs(self):
        """Setup specialized log files for different categories."""
        # JSON logs
        self.json_logs = {
            'inference': config.INFERENCE_LOG,
            'api_requests': self.logs_dir / 'api_requests.json',
            'errors': self.logs_dir / 'errors.json',
            'websocket': self.logs_dir / 'websocket.json'
        }
        
        # CSV logs
        self.csv_logs = {
            'registration': config.REGISTRATION_LOG,
            'retrain': config.RETRAIN_HISTORY_LOG,
            'progress': config.PROGRESS_REPORT_LOG,
            'auth': self.logs_dir / 'auth_log.csv',
            'performance': self.logs_dir / 'performance_log.csv'
        }
        
        # Initialize CSV files with headers if they don't exist
        self._initialize_csv_logs()
    
    def _initialize_csv_logs(self):
        """Initialize CSV log files with headers."""
        csv_headers = {
            'auth': ['timestamp', 'user_id', 'username', 'action', 'success', 'ip_address', 'user_agent'],
            'performance': ['timestamp', 'endpoint', 'method', 'duration_ms', 'status_code', 'user_id'],
            'registration': ['timestamp', 'user_id', 'username', 'speaker_id', 'num_segments', 'status'],
            'retrain': ['timestamp', 'status', 'train_accuracy', 'test_accuracy', 'n_classes', 'n_samples', 'duration_seconds', 'error_message'],
            'progress': ['timestamp', 'task_id', 'task_type', 'status', 'progress_percent', 'message']
        }
        
        for log_type, headers in csv_headers.items():
            log_file = self.csv_logs.get(log_type)
            if log_file and not log_file.exists():
                with open(log_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
    
    # ==================== GENERAL LOGGING ====================
    
    def log(self, level: LogLevel, message: str, category: LogCategory = LogCategory.SYSTEM,
            extra_data: Optional[Dict] = None):
        """
        General purpose logging method.
        
        Args:
            level: Log level
            message: Log message
            category: Log category
            extra_data: Additional data to log
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'category': category.value,
            'message': message
        }
        
        if extra_data:
            log_entry['data'] = extra_data
        
        # Log to system logger
        log_method = getattr(self.system_logger, level.value.lower())
        log_method(f"[{category.value.upper()}] {message}")
        
        # Log to category-specific file if available
        self._log_to_category_file(category, log_entry)
    
    def debug(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log debug message."""
        self.log(LogLevel.DEBUG, message, category, kwargs if kwargs else None)
    
    def info(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log info message."""
        self.log(LogLevel.INFO, message, category, kwargs if kwargs else None)
    
    def warning(self, message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
        """Log warning message."""
        self.log(LogLevel.WARNING, message, category, kwargs if kwargs else None)
    
    def error(self, message: str, category: LogCategory = LogCategory.SYSTEM, 
              exception: Optional[Exception] = None, **kwargs):
        """
        Log error message with optional exception.
        
        Args:
            message: Error message
            category: Log category
            exception: Exception object if available
            **kwargs: Additional data
        """
        extra_data = kwargs.copy()
        
        if exception:
            extra_data['exception_type'] = type(exception).__name__
            extra_data['exception_message'] = str(exception)
            extra_data['traceback'] = traceback.format_exc()
        
        self.log(LogLevel.ERROR, message, category, extra_data)
        
        # Also log to errors JSON
        self._log_error_to_json(message, category, exception, extra_data)
    
    def critical(self, message: str, category: LogCategory = LogCategory.SYSTEM, 
                 exception: Optional[Exception] = None, **kwargs):
        """Log critical message."""
        extra_data = kwargs.copy()
        
        if exception:
            extra_data['exception_type'] = type(exception).__name__
            extra_data['exception_message'] = str(exception)
            extra_data['traceback'] = traceback.format_exc()
        
        self.log(LogLevel.CRITICAL, message, category, extra_data)
    
    def _log_to_category_file(self, category: LogCategory, log_entry: Dict):
        """Log entry to category-specific file."""
        category_files = {
            LogCategory.INFERENCE: self.json_logs.get('inference'),
            LogCategory.API: self.json_logs.get('api_requests'),
            LogCategory.WEBSOCKET: self.json_logs.get('websocket')
        }
        
        log_file = category_files.get(category)
        if log_file:
            self._append_to_json_log(log_file, log_entry)
    
    def _log_error_to_json(self, message: str, category: LogCategory,
                           exception: Optional[Exception], extra_data: Dict):
        """Log error to errors.json file."""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'category': category.value,
            'message': message,
            'data': extra_data
        }
        
        self._append_to_json_log(self.json_logs['errors'], error_entry)
    
    # ==================== SPECIALIZED LOGGING ====================
    
    def log_auth(self, user_id: Optional[int], username: str, action: str,
                 success: bool, ip_address: str = None, user_agent: str = None):
        """
        Log authentication events.
        
        Args:
            user_id: User ID
            username: Username
            action: Action (login, logout, register, etc.)
            success: Whether action was successful
            ip_address: Client IP address
            user_agent: Client user agent
        """
        log_data = [
            datetime.now().isoformat(),
            user_id if user_id else '',
            username,
            action,
            success,
            ip_address if ip_address else '',
            user_agent if user_agent else ''
        ]
        
        self._append_to_csv_log(self.csv_logs['auth'], log_data)
        
        # Also log to system
        status = "SUCCESS" if success else "FAILED"
        self.info(f"Auth {action}: {username} - {status}", LogCategory.AUTH,
                 user_id=user_id, ip_address=ip_address)
    
    def log_registration(self, user_id: int, username: str, speaker_id: str,
                        num_segments: int, status: str):
        """
        Log voice registration events.
        
        Args:
            user_id: User ID
            username: Username
            speaker_id: Speaker ID
            num_segments: Number of audio segments
            status: Registration status
        """
        log_data = [
            datetime.now().isoformat(),
            user_id,
            username,
            speaker_id,
            num_segments,
            status
        ]
        
        self._append_to_csv_log(self.csv_logs['registration'], log_data)
        
        self.info(f"Voice registration: {username} - {status}", LogCategory.REGISTRATION,
                 user_id=user_id, speaker_id=speaker_id, segments=num_segments)
    
    def log_inference(self, interview_id: int, segments_count: int,
                     status: str, duration_ms: Optional[float] = None,
                     error: Optional[str] = None):
        """
        Log inference/interview processing events.
        
        Args:
            interview_id: Interview ID
            segments_count: Number of segments processed
            status: Processing status
            duration_ms: Processing duration in milliseconds
            error: Error message if failed
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'interview_id': interview_id,
            'segments_count': segments_count,
            'status': status,
            'duration_ms': duration_ms,
            'error': error
        }
        
        self._append_to_json_log(self.json_logs['inference'], log_entry)
        
        self.info(f"Inference: Interview {interview_id} - {status}", LogCategory.INFERENCE,
                 segments=segments_count, duration_ms=duration_ms)
    
    def log_api_request(self, endpoint: str, method: str, user_id: Optional[int],
                       status_code: int, duration_ms: float, request_data: Optional[Dict] = None):
        """
        Log API requests.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            user_id: User ID if authenticated
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            request_data: Optional request data
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'user_id': user_id,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'request_data': request_data
        }
        
        self._append_to_json_log(self.json_logs['api_requests'], log_entry)
        
        # Also log to performance CSV
        perf_data = [
            datetime.now().isoformat(),
            endpoint,
            method,
            duration_ms,
            status_code,
            user_id if user_id else ''
        ]
        self._append_to_csv_log(self.csv_logs['performance'], perf_data)
    
    def log_training(self, status: str, train_accuracy: float, test_accuracy: float,
                    n_classes: int, n_samples: int, duration_seconds: float,
                    error_message: Optional[str] = None):
        """
        Log model training events.
        
        Args:
            status: Training status
            train_accuracy: Training accuracy
            test_accuracy: Test accuracy
            n_classes: Number of classes
            n_samples: Number of training samples
            duration_seconds: Training duration
            error_message: Error message if failed
        """
        log_data = [
            datetime.now().isoformat(),
            status,
            train_accuracy,
            test_accuracy,
            n_classes,
            n_samples,
            duration_seconds,
            error_message if error_message else ''
        ]
        
        self._append_to_csv_log(self.csv_logs['retrain'], log_data)
        
        self.info(f"Training: {status} - Acc: {test_accuracy:.4f}", LogCategory.TRAINING,
                 classes=n_classes, samples=n_samples, duration=duration_seconds)
    
    def log_progress(self, task_id: str, task_type: str, status: str,
                    progress_percent: float, message: str):
        """
        Log task progress.
        
        Args:
            task_id: Task ID
            task_type: Type of task
            status: Current status
            progress_percent: Progress percentage (0-100)
            message: Progress message
        """
        log_data = [
            datetime.now().isoformat(),
            task_id,
            task_type,
            status,
            progress_percent,
            message
        ]
        
        self._append_to_csv_log(self.csv_logs['progress'], log_data)
    
    def log_websocket(self, connection_id: str, event: str, data: Optional[Dict] = None):
        """
        Log WebSocket events.
        
        Args:
            connection_id: WebSocket connection ID
            event: Event type (connect, disconnect, message, error)
            data: Event data
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'connection_id': connection_id,
            'event': event,
            'data': data
        }
        
        self._append_to_json_log(self.json_logs['websocket'], log_entry)
        
        self.info(f"WebSocket {event}: {connection_id}", LogCategory.WEBSOCKET, data=data)
    
    # ==================== FILE OPERATIONS ====================
    
    def _append_to_json_log(self, log_file: Path, entry: Dict):
        """Append entry to JSON log file."""
        try:
            # Load existing logs
            logs = []
            if log_file.exists():
                try:
                    with open(log_file, 'r') as f:
                        logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
            
            # Append new entry
            logs.append(entry)
            
            # Keep only last 1000 entries
            logs = logs[-1000:]
            
            # Save logs
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        
        except Exception as e:
            self.system_logger.error(f"Error writing to JSON log {log_file}: {e}")
    
    def _append_to_csv_log(self, log_file: Path, row: List[Any]):
        """Append row to CSV log file."""
        try:
            with open(log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)
        
        except Exception as e:
            self.system_logger.error(f"Error writing to CSV log {log_file}: {e}")
    
    # ==================== LOG RETRIEVAL ====================
    
    def get_logs(self, log_type: str, limit: int = 100, 
                 filter_by: Optional[Dict] = None) -> List[Dict]:
        """
        Retrieve logs from JSON log files.
        
        Args:
            log_type: Type of log (inference, api_requests, errors, websocket)
            limit: Maximum number of logs to retrieve
            filter_by: Optional filter criteria
        
        Returns:
            List of log entries
        """
        log_file = self.json_logs.get(log_type)
        if not log_file or not log_file.exists():
            return []
        
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
            
            # Apply filters
            if filter_by:
                logs = self._filter_logs(logs, filter_by)
            
            # Return latest logs
            return logs[-limit:]
        
        except Exception as e:
            self.system_logger.error(f"Error reading logs: {e}")
            return []
    
    def _filter_logs(self, logs: List[Dict], filter_by: Dict) -> List[Dict]:
        """Filter logs by criteria."""
        filtered = []
        
        for log in logs:
            match = True
            for key, value in filter_by.items():
                if log.get(key) != value:
                    match = False
                    break
            
            if match:
                filtered.append(log)
        
        return filtered
    
    def get_csv_logs(self, log_type: str, limit: int = 100) -> List[Dict]:
        """
        Retrieve logs from CSV log files.
        
        Args:
            log_type: Type of log
            limit: Maximum number of logs
        
        Returns:
            List of log dictionaries
        """
        log_file = self.csv_logs.get(log_type)
        if not log_file or not log_file.exists():
            return []
        
        try:
            import pandas as pd
            df = pd.read_csv(log_file)
            df = df.tail(limit)
            return df.to_dict('records')
        
        except Exception as e:
            self.system_logger.error(f"Error reading CSV logs: {e}")
            return []
    
    def get_error_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent error logs."""
        return self.get_logs('errors', limit)
    
    def get_recent_api_requests(self, limit: int = 100) -> List[Dict]:
        """Get recent API request logs."""
        return self.get_logs('api_requests', limit)
    
    # ==================== STATISTICS ====================
    
    def get_log_statistics(self) -> Dict:
        """Get logging statistics."""
        stats = {
            'json_logs': {},
            'csv_logs': {},
            'total_size_mb': 0
        }
        
        # Count JSON logs
        for log_type, log_file in self.json_logs.items():
            if log_file.exists():
                with open(log_file, 'r') as f:
                    try:
                        logs = json.load(f)
                        stats['json_logs'][log_type] = len(logs)
                    except:
                        stats['json_logs'][log_type] = 0
        
        # Count CSV logs
        for log_type, log_file in self.csv_logs.items():
            if log_file.exists():
                try:
                    import pandas as pd
                    df = pd.read_csv(log_file)
                    stats['csv_logs'][log_type] = len(df)
                except:
                    stats['csv_logs'][log_type] = 0
        
        # Calculate total size
        for file_dict in [self.json_logs, self.csv_logs]:
            for log_file in file_dict.values():
                if log_file.exists():
                    stats['total_size_mb'] += log_file.stat().st_size / (1024 * 1024)
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        
        return stats
    
    # ==================== CLEANUP ====================
    
    def cleanup_old_logs(self, days: int = 30):
        """
        Clean up logs older than specified days.
        
        Args:
            days: Number of days to keep
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        self.info(f"Cleaning up logs older than {days} days", LogCategory.SYSTEM)
        
        # Clean JSON logs
        for log_file in self.json_logs.values():
            if log_file.exists():
                self._cleanup_json_log(log_file, cutoff_date)
        
        self.info("Log cleanup completed", LogCategory.SYSTEM)
    
    def _cleanup_json_log(self, log_file: Path, cutoff_timestamp: float):
        """Clean up old entries from JSON log file."""
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
            
            # Filter logs
            filtered_logs = [
                log for log in logs
                if datetime.fromisoformat(log['timestamp']).timestamp() > cutoff_timestamp
            ]
            
            # Save filtered logs
            with open(log_file, 'w') as f:
                json.dump(filtered_logs, f, indent=2)
            
            removed = len(logs) - len(filtered_logs)
            if removed > 0:
                self.info(f"Removed {removed} old entries from {log_file.name}", LogCategory.SYSTEM)
        
        except Exception as e:
            self.error(f"Error cleaning up {log_file.name}", LogCategory.SYSTEM, exception=e)


# Global logging service instance
_logging_service = None

def get_logger() -> LoggingService:
    """Get global logging service instance."""
    global _logging_service
    if _logging_service is None:
        _logging_service = LoggingService()
    return _logging_service


# Convenience functions
def log_info(message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
    """Quick info logging."""
    get_logger().info(message, category, **kwargs)

def log_error(message: str, category: LogCategory = LogCategory.SYSTEM, 
              exception: Optional[Exception] = None, **kwargs):
    """Quick error logging."""
    get_logger().error(message, category, exception, **kwargs)

def log_warning(message: str, category: LogCategory = LogCategory.SYSTEM, **kwargs):
    """Quick warning logging."""
    get_logger().warning(message, category, **kwargs)


if __name__ == "__main__":
    # Test logging service
    logger = LoggingService()
    
    print("Testing logging service...")
    
    # Test general logging
    logger.info("System started", LogCategory.SYSTEM)
    logger.warning("This is a warning", LogCategory.SYSTEM, detail="test warning")
    
    # Test specialized logging
    logger.log_auth(1, "test_user", "login", True, "127.0.0.1", "Mozilla/5.0")
    logger.log_registration(1, "test_user", "enum_1", 20, "success")
    logger.log_inference(1, 10, "completed", 1500.5)
    
    # Test error logging
    try:
        raise ValueError("Test error")
    except ValueError as e:
        logger.error("Test error occurred", LogCategory.SYSTEM, exception=e)
    
    # Get statistics
    stats = logger.get_log_statistics()
    print("\nLog Statistics:")
    print(json.dumps(stats, indent=2))
    
    print("\nLogging service test completed!")