#!/usr/bin/env python3
"""
Centralized Error Management System for Python Components

Provides unified error handling, logging, categorization, and recovery
strategies across the entire visualizer backend.
"""

import logging
import sys
import traceback
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standardized error codes"""
    # Network/API Errors
    NETWORK_CONNECTION = 'NET_001'
    API_ENDPOINT_FAILED = 'NET_002'
    WEBSOCKET_ERROR = 'NET_003'
    TIMEOUT_ERROR = 'NET_004'
    
    # Storage Errors
    FILE_SYSTEM_ERROR = 'STO_001'
    DATABASE_ERROR = 'STO_002'
    PERMISSION_DENIED = 'STO_003'
    DISK_FULL = 'STO_004'
    
    # Initialization Errors
    COMPONENT_INIT_FAILED = 'INIT_001'
    DEPENDENCY_MISSING = 'INIT_002'
    CONFIG_INVALID = 'INIT_003'
    IMPORT_ERROR = 'INIT_004'
    
    # Validation Errors
    INPUT_VALIDATION = 'VAL_001'
    SCHEMA_VALIDATION = 'VAL_002'
    SECURITY_VALIDATION = 'VAL_003'
    TYPE_VALIDATION = 'VAL_004'
    
    # Permission Errors
    ACCESS_DENIED = 'PERM_001'
    AUTHENTICATION_FAILED = 'PERM_002'
    AUTHORIZATION_FAILED = 'PERM_003'
    TOKEN_EXPIRED = 'PERM_004'
    
    # Processing Errors
    PROCESSING_FAILED = 'PROC_001'
    MEMORY_ERROR = 'PROC_002'
    TIMEOUT_PROCESSING = 'PROC_003'
    RESOURCE_EXHAUSTED = 'PROC_004'
    
    # System Errors
    SYSTEM_ERROR = 'SYS_001'
    CONFIGURATION_ERROR = 'SYS_002'
    UNKNOWN_ERROR = 'SYS_999'


class SeverityLevel(Enum):
    """Error severity levels"""
    CRITICAL = 'critical'  # System unusable
    ERROR = 'error'        # Feature broken
    WARNING = 'warning'    # Degraded functionality
    INFO = 'info'          # Informational only


class RecoveryStrategy(Enum):
    """Error recovery strategies"""
    RETRY = 'retry'
    FALLBACK = 'fallback'
    DEGRADE = 'degrade'
    USER_ACTION = 'user_action'
    RESTART = 'restart'
    IGNORE = 'ignore'


@dataclass
class ErrorContext:
    """Context information for error handling"""
    component: str = 'unknown'
    operation: str = 'unknown'
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryResult:
    """Result of error recovery attempt"""
    strategy: RecoveryStrategy
    attempted: bool = False
    successful: bool = False
    attempt_number: int = 1
    message: str = ''
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorRecord:
    """Comprehensive error record"""
    id: str
    timestamp: datetime
    error_code: ErrorCode
    severity: SeverityLevel
    recovery_strategy: RecoveryStrategy
    user_message: str
    technical_message: str
    context: ErrorContext
    original_exception: Optional[Exception] = None
    stack_trace: Optional[str] = None
    recovery_result: Optional[RecoveryResult] = None


class ErrorManager:
    """
    Centralized error management system for Python components.
    
    Provides consistent error handling, logging, categorization,
    and recovery across the entire application.
    """
    
    def __init__(self, component_name: str = 'unknown'):
        self.component_name = component_name
        self.error_history: List[ErrorRecord] = []
        self.recovery_attempts: Dict[str, int] = {}
        self.max_retry_attempts = 3
        self.retry_delays = [1.0, 2.0, 5.0]  # Exponential backoff in seconds
        self.max_history_size = 1000
        
        # Recovery strategy handlers
        self.recovery_handlers: Dict[RecoveryStrategy, Callable] = {
            RecoveryStrategy.RETRY: self._attempt_retry,
            RecoveryStrategy.FALLBACK: self._attempt_fallback,
            RecoveryStrategy.DEGRADE: self._attempt_graceful_degradation,
            RecoveryStrategy.RESTART: self._attempt_restart,
            RecoveryStrategy.USER_ACTION: self._require_user_action,
            RecoveryStrategy.IGNORE: self._ignore_error
        }
        
        # External handlers for recovery strategies
        self.external_handlers: Dict[RecoveryStrategy, List[Callable]] = {
            strategy: [] for strategy in RecoveryStrategy
        }
        
        logger.info(f"ErrorManager initialized for component: {component_name}")
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        user_message: Optional[str] = None
    ) -> ErrorRecord:
        """
        Main error handling method.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            user_message: Custom user-friendly message
            
        Returns:
            ErrorRecord: Comprehensive error record
        """
        # Generate error ID
        error_id = self._generate_error_id()
        
        # Set default context
        if context is None:
            context = ErrorContext(component=self.component_name)
        elif context.component == 'unknown':
            context.component = self.component_name
        
        # Categorize error
        error_info = self._categorize_error(error, context)
        
        # Create error record
        error_record = ErrorRecord(
            id=error_id,
            timestamp=datetime.now(timezone.utc),
            error_code=error_info['error_code'],
            severity=error_info['severity'],
            recovery_strategy=error_info['recovery_strategy'],
            user_message=user_message or error_info['user_message'],
            technical_message=error_info['technical_message'],
            context=context,
            original_exception=error,
            stack_trace=traceback.format_exc() if error else None
        )
        
        # Log the error
        self._log_error(error_record)
        
        # Add to history
        self.error_history.append(error_record)
        self._trim_error_history()
        
        # Attempt recovery
        recovery_result = self._attempt_recovery(error_record)
        error_record.recovery_result = recovery_result
        
        # Notify external systems
        self._notify_external_systems(error_record)
        
        return error_record
    
    def _categorize_error(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Categorize error and determine handling strategy"""
        error_code = ErrorCode.UNKNOWN_ERROR
        severity = SeverityLevel.ERROR
        recovery_strategy = RecoveryStrategy.IGNORE
        user_message = 'An unexpected error occurred'
        technical_message = str(error) if error else 'Unknown error'
        
        # Categorize based on exception type
        if isinstance(error, ImportError):
            error_code = ErrorCode.IMPORT_ERROR
            severity = SeverityLevel.ERROR
            recovery_strategy = RecoveryStrategy.FALLBACK
            user_message = 'Required component unavailable. Using fallback mode.'
            
        elif isinstance(error, ConnectionError):
            error_code = ErrorCode.NETWORK_CONNECTION
            severity = SeverityLevel.ERROR
            recovery_strategy = RecoveryStrategy.RETRY
            user_message = 'Connection failed. Retrying...'
            
        elif isinstance(error, TimeoutError):
            error_code = ErrorCode.TIMEOUT_ERROR
            severity = SeverityLevel.WARNING
            recovery_strategy = RecoveryStrategy.RETRY
            user_message = 'Operation timed out. Retrying...'
            
        elif isinstance(error, PermissionError):
            error_code = ErrorCode.PERMISSION_DENIED
            severity = SeverityLevel.ERROR
            recovery_strategy = RecoveryStrategy.USER_ACTION
            user_message = 'Permission denied. Please check file permissions.'
            
        elif isinstance(error, FileNotFoundError):
            error_code = ErrorCode.FILE_SYSTEM_ERROR
            severity = SeverityLevel.ERROR
            recovery_strategy = RecoveryStrategy.FALLBACK
            user_message = 'Required file not found. Using fallback.'
            
        elif isinstance(error, MemoryError):
            error_code = ErrorCode.MEMORY_ERROR
            severity = SeverityLevel.CRITICAL
            recovery_strategy = RecoveryStrategy.RESTART
            user_message = 'Out of memory. Restarting component.'
            
        elif isinstance(error, ValueError):
            error_code = ErrorCode.INPUT_VALIDATION
            severity = SeverityLevel.WARNING
            recovery_strategy = RecoveryStrategy.USER_ACTION
            user_message = 'Invalid input provided. Please check your data.'
            
        elif isinstance(error, TypeError):
            error_code = ErrorCode.TYPE_VALIDATION
            severity = SeverityLevel.ERROR
            recovery_strategy = RecoveryStrategy.FALLBACK
            user_message = 'Data type error. Using fallback processing.'
            
        elif isinstance(error, KeyError):
            error_code = ErrorCode.PROCESSING_FAILED
            severity = SeverityLevel.WARNING
            recovery_strategy = RecoveryStrategy.DEGRADE
            user_message = 'Missing data field. Continuing with reduced functionality.'
            
        # Context-based adjustments
        if context.operation in ['initialization', 'startup']:
            if severity == SeverityLevel.ERROR:
                severity = SeverityLevel.CRITICAL
            recovery_strategy = RecoveryStrategy.RESTART
            
        elif context.operation in ['api_call', 'network_request']:
            if error_code == ErrorCode.UNKNOWN_ERROR:
                error_code = ErrorCode.API_ENDPOINT_FAILED
            recovery_strategy = RecoveryStrategy.RETRY
            
        elif context.operation in ['file_operation', 'storage']:
            if error_code == ErrorCode.UNKNOWN_ERROR:
                error_code = ErrorCode.FILE_SYSTEM_ERROR
            recovery_strategy = RecoveryStrategy.FALLBACK
        
        return {
            'error_code': error_code,
            'severity': severity,
            'recovery_strategy': recovery_strategy,
            'user_message': user_message,
            'technical_message': technical_message
        }
    
    def _attempt_recovery(self, error_record: ErrorRecord) -> RecoveryResult:
        """Attempt to recover from error using appropriate strategy"""
        recovery_key = f"{error_record.error_code.value}_{error_record.context.component}"
        attempt_count = self.recovery_attempts.get(recovery_key, 0) + 1
        self.recovery_attempts[recovery_key] = attempt_count
        
        recovery_result = RecoveryResult(
            strategy=error_record.recovery_strategy,
            attempt_number=attempt_count
        )
        
        try:
            handler = self.recovery_handlers.get(error_record.recovery_strategy)
            if handler:
                recovery_result.attempted = True
                recovery_result.successful = handler(error_record, attempt_count)
                recovery_result.message = self._get_recovery_message(
                    error_record.recovery_strategy,
                    recovery_result.successful,
                    attempt_count
                )
            else:
                recovery_result.message = 'No recovery handler available'
                
        except Exception as recovery_error:
            recovery_result.successful = False
            recovery_result.message = f'Recovery failed: {recovery_error}'
            logger.error(f"Recovery attempt failed: {recovery_error}")
        
        return recovery_result
    
    def _attempt_retry(self, error_record: ErrorRecord, attempt_count: int) -> bool:
        """Attempt retry with exponential backoff"""
        if attempt_count > self.max_retry_attempts:
            return False
        
        # Schedule retry for external handlers
        delay = self.retry_delays[min(attempt_count - 1, len(self.retry_delays) - 1)]
        
        # Notify external handlers
        for handler in self.external_handlers[RecoveryStrategy.RETRY]:
            try:
                handler(error_record, attempt_count, delay)
            except Exception as e:
                logger.error(f"External retry handler failed: {e}")
        
        return True
    
    def _attempt_fallback(self, error_record: ErrorRecord, attempt_count: int) -> bool:
        """Attempt fallback strategy"""
        # Notify external handlers
        for handler in self.external_handlers[RecoveryStrategy.FALLBACK]:
            try:
                if handler(error_record):
                    return True
            except Exception as e:
                logger.error(f"External fallback handler failed: {e}")
        
        # Default fallback is to continue with degraded functionality
        return True
    
    def _attempt_graceful_degradation(self, error_record: ErrorRecord, attempt_count: int) -> bool:
        """Attempt graceful degradation"""
        # Notify external handlers
        for handler in self.external_handlers[RecoveryStrategy.DEGRADE]:
            try:
                if handler(error_record):
                    return True
            except Exception as e:
                logger.error(f"External degradation handler failed: {e}")
        
        return True
    
    def _attempt_restart(self, error_record: ErrorRecord, attempt_count: int) -> bool:
        """Attempt component restart"""
        # Notify external handlers
        for handler in self.external_handlers[RecoveryStrategy.RESTART]:
            try:
                if handler(error_record):
                    return True
            except Exception as e:
                logger.error(f"External restart handler failed: {e}")
        
        return False
    
    def _require_user_action(self, error_record: ErrorRecord, attempt_count: int) -> bool:
        """Require user action - cannot auto-recover"""
        # Notify external handlers
        for handler in self.external_handlers[RecoveryStrategy.USER_ACTION]:
            try:
                handler(error_record)
            except Exception as e:
                logger.error(f"External user action handler failed: {e}")
        
        return False
    
    def _ignore_error(self, error_record: ErrorRecord, attempt_count: int) -> bool:
        """Ignore error - no action needed"""
        return True
    
    def _get_recovery_message(self, strategy: RecoveryStrategy, successful: bool, attempt_count: int) -> str:
        """Get appropriate recovery message"""
        if strategy == RecoveryStrategy.RETRY:
            if successful:
                return f'Retry scheduled (attempt {attempt_count}/{self.max_retry_attempts})'
            else:
                return f'Max retry attempts ({self.max_retry_attempts}) exceeded'
                
        elif strategy == RecoveryStrategy.FALLBACK:
            return 'Fallback activated' if successful else 'Fallback failed'
            
        elif strategy == RecoveryStrategy.DEGRADE:
            return 'Graceful degradation applied' if successful else 'Degradation failed'
            
        elif strategy == RecoveryStrategy.RESTART:
            return 'Component restart initiated' if successful else 'Restart failed'
            
        elif strategy == RecoveryStrategy.USER_ACTION:
            return 'User action required'
            
        elif strategy == RecoveryStrategy.IGNORE:
            return 'Error ignored'
            
        return 'Unknown recovery strategy'
    
    def _log_error(self, error_record: ErrorRecord):
        """Log error with structured format"""
        log_level = self._get_log_level(error_record.severity)
        log_message = self._format_log_message(error_record)
        
        # Log with appropriate level
        getattr(logger, log_level)(log_message, extra={
            'error_id': error_record.id,
            'error_code': error_record.error_code.value,
            'severity': error_record.severity.value,
            'component': error_record.context.component,
            'operation': error_record.context.operation,
            'user_id': error_record.context.user_id,
            'session_id': error_record.context.session_id
        })
        
        # Log stack trace for errors and critical issues
        if error_record.severity in [SeverityLevel.ERROR, SeverityLevel.CRITICAL]:
            if error_record.stack_trace:
                logger.error(f"Stack trace for {error_record.id}:\n{error_record.stack_trace}")
    
    def _get_log_level(self, severity: SeverityLevel) -> str:
        """Get appropriate log level for severity"""
        if severity == SeverityLevel.CRITICAL:
            return 'critical' if hasattr(logger, 'critical') else 'error'
        elif severity == SeverityLevel.ERROR:
            return 'error'
        elif severity == SeverityLevel.WARNING:
            return 'warning'
        elif severity == SeverityLevel.INFO:
            return 'info'
        return 'debug'
    
    def _format_log_message(self, error_record: ErrorRecord) -> str:
        """Format log message with emoji and context"""
        emoji = self._get_severity_emoji(error_record.severity)
        return (f"{emoji} [{error_record.error_code.value}] "
                f"{error_record.technical_message} "
                f"(Component: {error_record.context.component}, "
                f"Operation: {error_record.context.operation})")
    
    def _get_severity_emoji(self, severity: SeverityLevel) -> str:
        """Get emoji for severity level"""
        emoji_map = {
            SeverityLevel.CRITICAL: '🔴',
            SeverityLevel.ERROR: '❌',
            SeverityLevel.WARNING: '⚠️',
            SeverityLevel.INFO: 'ℹ️'
        }
        return emoji_map.get(severity, '❓')
    
    def _notify_external_systems(self, error_record: ErrorRecord):
        """Notify external systems about error"""
        # TODO: Implement external notification systems
        # - Send to monitoring systems (Prometheus, Grafana)
        # - Send to alerting systems (PagerDuty, Slack)
        # - Send to error tracking services (Sentry)
        pass
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        return f"err_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    def _trim_error_history(self):
        """Trim error history to prevent memory bloat"""
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def register_recovery_handler(self, strategy: RecoveryStrategy, handler: Callable):
        """Register external recovery handler"""
        self.external_handlers[strategy].append(handler)
        logger.info(f"Registered recovery handler for {strategy.value}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.error_history:
            return {
                'total_errors': 0,
                'severity_breakdown': {},
                'error_code_breakdown': {},
                'recent_errors': []
            }
        
        stats = {
            'total_errors': len(self.error_history),
            'severity_breakdown': {},
            'error_code_breakdown': {},
            'recovery_success_rate': 0,
            'recent_errors': []
        }
        
        # Calculate severity breakdown
        for severity in SeverityLevel:
            count = sum(1 for error in self.error_history if error.severity == severity)
            stats['severity_breakdown'][severity.value] = count
        
        # Calculate error code breakdown
        for error in self.error_history:
            code = error.error_code.value
            stats['error_code_breakdown'][code] = stats['error_code_breakdown'].get(code, 0) + 1
        
        # Calculate recovery success rate
        recovery_attempted = [e for e in self.error_history if e.recovery_result and e.recovery_result.attempted]
        if recovery_attempted:
            successful = sum(1 for e in recovery_attempted if e.recovery_result.successful)
            stats['recovery_success_rate'] = (successful / len(recovery_attempted)) * 100
        
        # Get recent errors
        stats['recent_errors'] = [
            {
                'id': error.id,
                'timestamp': error.timestamp.isoformat(),
                'error_code': error.error_code.value,
                'severity': error.severity.value,
                'user_message': error.user_message,
                'recovery_successful': error.recovery_result.successful if error.recovery_result else None
            }
            for error in self.error_history[-10:]
        ]
        
        return stats
    
    def clear_error_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.recovery_attempts.clear()
        logger.info("Error history cleared")
    
    def export_error_history(self, filepath: Union[str, Path]) -> bool:
        """Export error history to JSON file"""
        try:
            filepath = Path(filepath)
            
            # Convert error history to serializable format
            serializable_history = []
            for error in self.error_history:
                error_data = {
                    'id': error.id,
                    'timestamp': error.timestamp.isoformat(),
                    'error_code': error.error_code.value,
                    'severity': error.severity.value,
                    'recovery_strategy': error.recovery_strategy.value,
                    'user_message': error.user_message,
                    'technical_message': error.technical_message,
                    'context': {
                        'component': error.context.component,
                        'operation': error.context.operation,
                        'user_id': error.context.user_id,
                        'session_id': error.context.session_id,
                        'additional_data': error.context.additional_data
                    },
                    'recovery_result': {
                        'strategy': error.recovery_result.strategy.value,
                        'attempted': error.recovery_result.attempted,
                        'successful': error.recovery_result.successful,
                        'attempt_number': error.recovery_result.attempt_number,
                        'message': error.recovery_result.message
                    } if error.recovery_result else None,
                    'stack_trace': error.stack_trace
                }
                serializable_history.append(error_data)
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump({
                    'component': self.component_name,
                    'export_timestamp': datetime.now(timezone.utc).isoformat(),
                    'error_count': len(serializable_history),
                    'errors': serializable_history
                }, f, indent=2)
            
            logger.info(f"Error history exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export error history: {e}")
            return False


# Global error manager factory
_error_managers: Dict[str, ErrorManager] = {}


def get_error_manager(component_name: str = 'default') -> ErrorManager:
    """Get or create error manager for component"""
    if component_name not in _error_managers:
        _error_managers[component_name] = ErrorManager(component_name)
    return _error_managers[component_name]


# Context manager for error handling
class ErrorHandler:
    """Context manager for standardized error handling"""
    
    def __init__(
        self,
        component_name: str,
        operation: str,
        user_message: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None
    ):
        self.error_manager = get_error_manager(component_name)
        self.context = ErrorContext(
            component=component_name,
            operation=operation,
            additional_data=context_data or {}
        )
        self.user_message = user_message
        self.error_record: Optional[ErrorRecord] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.error_record = self.error_manager.handle_error(
                exc_val,
                self.context,
                self.user_message
            )
            # Return False to re-raise the exception
            return False
        return True
    
    def get_error_record(self) -> Optional[ErrorRecord]:
        """Get the error record if an error occurred"""
        return self.error_record


# Decorator for automatic error handling
def handle_errors(
    component_name: str,
    operation: Optional[str] = None,
    user_message: Optional[str] = None
):
    """Decorator for automatic error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            with ErrorHandler(component_name, op_name, user_message) as handler:
                return func(*args, **kwargs)
        return wrapper
    return decorator