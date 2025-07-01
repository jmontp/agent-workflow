/**
 * Centralized Error Management System
 * 
 * Provides unified error handling, logging, categorization, and recovery
 * strategies across the entire visualizer application.
 */

class ErrorManager {
    constructor() {
        this.errorCodes = {
            // Network/API Errors
            NETWORK_CONNECTION: 'NET_001',
            API_ENDPOINT_FAILED: 'NET_002',
            WEBSOCKET_ERROR: 'NET_003',
            TIMEOUT_ERROR: 'NET_004',
            
            // Storage Errors
            LOCALSTORAGE_FAILED: 'STO_001',
            DATA_CORRUPTION: 'STO_002',
            QUOTA_EXCEEDED: 'STO_003',
            
            // Initialization Errors
            COMPONENT_INIT_FAILED: 'INIT_001',
            DEPENDENCY_MISSING: 'INIT_002',
            CONFIG_INVALID: 'INIT_003',
            
            // Validation Errors
            INPUT_VALIDATION: 'VAL_001',
            SCHEMA_VALIDATION: 'VAL_002',
            SECURITY_VALIDATION: 'VAL_003',
            
            // Permission Errors
            ACCESS_DENIED: 'PERM_001',
            AUTHENTICATION_FAILED: 'PERM_002',
            AUTHORIZATION_FAILED: 'PERM_003',
            
            // UI Errors
            ELEMENT_NOT_FOUND: 'UI_001',
            RENDER_FAILED: 'UI_002',
            EVENT_HANDLER_FAILED: 'UI_003',
            
            // System Errors
            MEMORY_ERROR: 'SYS_001',
            RESOURCE_EXHAUSTED: 'SYS_002',
            UNKNOWN_ERROR: 'SYS_999'
        };
        
        this.severityLevels = {
            CRITICAL: 'critical',  // System unusable
            ERROR: 'error',        // Feature broken
            WARNING: 'warning',    // Degraded functionality
            INFO: 'info'          // Informational only
        };
        
        this.recoveryStrategies = {
            RETRY: 'retry',
            FALLBACK: 'fallback',
            DEGRADE: 'degrade',
            USER_ACTION: 'user_action',
            RESTART: 'restart',
            IGNORE: 'ignore'
        };
        
        // Error context and recovery state
        this.errorHistory = [];
        this.recoveryAttempts = new Map();
        this.maxRetryAttempts = 3;
        this.retryDelays = [1000, 2000, 5000]; // Exponential backoff
        
        this.initializeErrorHandling();
    }
    
    /**
     * Initialize global error handling
     */
    initializeErrorHandling() {
        // Global error handler for uncaught errors
        window.addEventListener('error', (event) => {
            this.handleError(event.error, {
                type: 'uncaught_exception',
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });
        
        // Global handler for unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError(event.reason, {
                type: 'unhandled_promise_rejection',
                promise: event.promise
            });
        });
        
        console.log('ErrorManager initialized with global error handling');
    }
    
    /**
     * Main error handling method
     */
    handleError(error, context = {}) {
        const errorInfo = this.categorizeError(error, context);
        const errorId = this.generateErrorId();
        
        // Create comprehensive error record
        const errorRecord = {
            id: errorId,
            timestamp: new Date().toISOString(),
            ...errorInfo,
            context: {
                url: window.location.href,
                userAgent: navigator.userAgent,
                sessionId: this.getSessionId(),
                ...context
            }
        };
        
        // Log the error
        this.logError(errorRecord);
        
        // Add to error history
        this.errorHistory.push(errorRecord);
        this.trimErrorHistory();
        
        // Attempt recovery
        const recoveryResult = this.attemptRecovery(errorRecord);
        
        // Notify user if necessary
        if (errorRecord.severity !== this.severityLevels.INFO) {
            this.notifyUser(errorRecord, recoveryResult);
        }
        
        // Emit error event for other components
        this.emitErrorEvent(errorRecord, recoveryResult);
        
        return {
            errorId,
            errorRecord,
            recoveryResult
        };
    }
    
    /**
     * Categorize error and determine handling strategy
     */
    categorizeError(error, context) {
        let errorCode = this.errorCodes.UNKNOWN_ERROR;
        let severity = this.severityLevels.ERROR;
        let recoveryStrategy = this.recoveryStrategies.IGNORE;
        let userMessage = 'An unexpected error occurred';
        let technicalMessage = error?.message || 'Unknown error';
        
        // Categorize based on error type and context
        if (error instanceof TypeError) {
            if (error.message.includes('fetch')) {
                errorCode = this.errorCodes.API_ENDPOINT_FAILED;
                severity = this.severityLevels.ERROR;
                recoveryStrategy = this.recoveryStrategies.RETRY;
                userMessage = 'Unable to connect to server. Retrying...';
            } else if (error.message.includes('undefined')) {
                errorCode = this.errorCodes.COMPONENT_INIT_FAILED;
                severity = this.severityLevels.ERROR;
                recoveryStrategy = this.recoveryStrategies.FALLBACK;
                userMessage = 'Component failed to load. Using fallback...';
            }
        } else if (error instanceof ReferenceError) {
            errorCode = this.errorCodes.DEPENDENCY_MISSING;
            severity = this.severityLevels.CRITICAL;
            recoveryStrategy = this.recoveryStrategies.USER_ACTION;
            userMessage = 'Required component missing. Please refresh the page.';
        } else if (error instanceof DOMException) {
            if (error.name === 'QuotaExceededError') {
                errorCode = this.errorCodes.QUOTA_EXCEEDED;
                severity = this.severityLevels.WARNING;
                recoveryStrategy = this.recoveryStrategies.DEGRADE;
                userMessage = 'Storage quota exceeded. Some features may be limited.';
            } else {
                errorCode = this.errorCodes.LOCALSTORAGE_FAILED;
                severity = this.severityLevels.WARNING;
                recoveryStrategy = this.recoveryStrategies.FALLBACK;
                userMessage = 'Storage error. Using temporary storage.';
            }
        }
        
        // Context-based categorization
        if (context.type === 'websocket') {
            errorCode = this.errorCodes.WEBSOCKET_ERROR;
            severity = this.severityLevels.ERROR;
            recoveryStrategy = this.recoveryStrategies.RETRY;
            userMessage = 'Connection lost. Reconnecting...';
        } else if (context.type === 'validation') {
            errorCode = this.errorCodes.INPUT_VALIDATION;
            severity = this.severityLevels.WARNING;
            recoveryStrategy = this.recoveryStrategies.USER_ACTION;
            userMessage = 'Invalid input. Please check your data.';
        } else if (context.component) {
            // Component-specific handling
            if (context.component === 'ProjectManager') {
                severity = this.severityLevels.ERROR;
                recoveryStrategy = this.recoveryStrategies.FALLBACK;
            } else if (context.component === 'DiscordChat') {
                severity = this.severityLevels.WARNING;
                recoveryStrategy = this.recoveryStrategies.DEGRADE;
            }
        }
        
        return {
            errorCode,
            severity,
            recoveryStrategy,
            userMessage,
            technicalMessage,
            originalError: error
        };
    }
    
    /**
     * Attempt error recovery
     */
    attemptRecovery(errorRecord) {
        const recoveryKey = `${errorRecord.errorCode}_${errorRecord.context.component || 'global'}`;
        const attemptCount = (this.recoveryAttempts.get(recoveryKey) || 0) + 1;
        
        this.recoveryAttempts.set(recoveryKey, attemptCount);
        
        const recovery = {
            strategy: errorRecord.recoveryStrategy,
            attempted: true,
            successful: false,
            attemptNumber: attemptCount,
            message: ''
        };
        
        try {
            switch (errorRecord.recoveryStrategy) {
                case this.recoveryStrategies.RETRY:
                    recovery.successful = this.attemptRetry(errorRecord, attemptCount);
                    recovery.message = recovery.successful ? 
                        'Retry successful' : 
                        `Retry ${attemptCount}/${this.maxRetryAttempts} failed`;
                    break;
                    
                case this.recoveryStrategies.FALLBACK:
                    recovery.successful = this.attemptFallback(errorRecord);
                    recovery.message = recovery.successful ? 
                        'Fallback activated' : 
                        'Fallback failed';
                    break;
                    
                case this.recoveryStrategies.DEGRADE:
                    recovery.successful = this.attemptGracefulDegradation(errorRecord);
                    recovery.message = recovery.successful ? 
                        'Graceful degradation applied' : 
                        'Degradation failed';
                    break;
                    
                case this.recoveryStrategies.RESTART:
                    recovery.successful = this.attemptRestart(errorRecord);
                    recovery.message = recovery.successful ? 
                        'Component restarted' : 
                        'Restart failed';
                    break;
                    
                case this.recoveryStrategies.USER_ACTION:
                    recovery.successful = false; // Requires user intervention
                    recovery.message = 'User action required';
                    break;
                    
                default:
                    recovery.attempted = false;
                    recovery.message = 'No recovery strategy available';
            }
        } catch (recoveryError) {
            recovery.successful = false;
            recovery.message = `Recovery failed: ${recoveryError.message}`;
            
            // Log recovery failure
            this.logError({
                errorCode: this.errorCodes.UNKNOWN_ERROR,
                severity: this.severityLevels.ERROR,
                technicalMessage: `Recovery failure for ${errorRecord.errorCode}`,
                originalError: recoveryError
            });
        }
        
        return recovery;
    }
    
    /**
     * Attempt retry with exponential backoff
     */
    attemptRetry(errorRecord, attemptNumber) {
        if (attemptNumber > this.maxRetryAttempts) {
            return false;
        }
        
        const delay = this.retryDelays[Math.min(attemptNumber - 1, this.retryDelays.length - 1)];
        
        // Schedule retry
        setTimeout(() => {
            // Emit retry event for components to handle
            this.emitRetryEvent(errorRecord, attemptNumber);
        }, delay);
        
        return true;
    }
    
    /**
     * Attempt fallback strategy
     */
    attemptFallback(errorRecord) {
        // Emit fallback event for components to handle
        this.emitFallbackEvent(errorRecord);
        return true;
    }
    
    /**
     * Attempt graceful degradation
     */
    attemptGracefulDegradation(errorRecord) {
        // Emit degradation event for components to handle
        this.emitDegradationEvent(errorRecord);
        return true;
    }
    
    /**
     * Attempt component restart
     */
    attemptRestart(errorRecord) {
        // Emit restart event for components to handle
        this.emitRestartEvent(errorRecord);
        return true;
    }
    
    /**
     * Log error with structured format
     */
    logError(errorRecord) {
        const logLevel = this.getLogLevel(errorRecord.severity);
        const logMessage = this.formatLogMessage(errorRecord);
        
        // Log to console with appropriate level
        console[logLevel](logMessage, errorRecord);
        
        // Send to external logging service if configured
        this.sendToExternalLogger(errorRecord);
    }
    
    /**
     * Get appropriate console log level
     */
    getLogLevel(severity) {
        switch (severity) {
            case this.severityLevels.CRITICAL:
            case this.severityLevels.ERROR:
                return 'error';
            case this.severityLevels.WARNING:
                return 'warn';
            case this.severityLevels.INFO:
                return 'info';
            default:
                return 'log';
        }
    }
    
    /**
     * Format log message
     */
    formatLogMessage(errorRecord) {
        const emoji = this.getSeverityEmoji(errorRecord.severity);
        return `${emoji} [${errorRecord.errorCode}] ${errorRecord.technicalMessage}`;
    }
    
    /**
     * Get emoji for severity level
     */
    getSeverityEmoji(severity) {
        switch (severity) {
            case this.severityLevels.CRITICAL:
                return '🔴';
            case this.severityLevels.ERROR:
                return '❌';
            case this.severityLevels.WARNING:
                return '⚠️';
            case this.severityLevels.INFO:
                return 'ℹ️';
            default:
                return '❓';
        }
    }
    
    /**
     * Notify user of error
     */
    notifyUser(errorRecord, recoveryResult) {
        // Emit notification event for UI components
        const notificationEvent = new CustomEvent('errorNotification', {
            detail: {
                errorRecord,
                recoveryResult,
                displayInfo: {
                    title: this.getErrorTitle(errorRecord),
                    message: errorRecord.userMessage,
                    severity: errorRecord.severity,
                    actions: this.getRecoveryActions(errorRecord, recoveryResult)
                }
            }
        });
        
        window.dispatchEvent(notificationEvent);
    }
    
    /**
     * Get user-friendly error title
     */
    getErrorTitle(errorRecord) {
        switch (errorRecord.severity) {
            case this.severityLevels.CRITICAL:
                return 'Critical Error';
            case this.severityLevels.ERROR:
                return 'Error';
            case this.severityLevels.WARNING:
                return 'Warning';
            case this.severityLevels.INFO:
                return 'Information';
            default:
                return 'Notice';
        }
    }
    
    /**
     * Get available recovery actions for user
     */
    getRecoveryActions(errorRecord, recoveryResult) {
        const actions = [];
        
        if (errorRecord.recoveryStrategy === this.recoveryStrategies.USER_ACTION) {
            actions.push({
                label: 'Refresh Page',
                action: () => window.location.reload(),
                primary: true
            });
        }
        
        if (!recoveryResult.successful && errorRecord.recoveryStrategy === this.recoveryStrategies.RETRY) {
            actions.push({
                label: 'Retry',
                action: () => this.emitRetryEvent(errorRecord, 1),
                primary: true
            });
        }
        
        actions.push({
            label: 'Dismiss',
            action: () => {}, // Handled by notification system
            primary: false
        });
        
        return actions;
    }
    
    /**
     * Emit error event for other components
     */
    emitErrorEvent(errorRecord, recoveryResult) {
        const event = new CustomEvent('errorOccurred', {
            detail: { errorRecord, recoveryResult }
        });
        window.dispatchEvent(event);
    }
    
    /**
     * Emit retry event
     */
    emitRetryEvent(errorRecord, attemptNumber) {
        const event = new CustomEvent('errorRetry', {
            detail: { errorRecord, attemptNumber }
        });
        window.dispatchEvent(event);
    }
    
    /**
     * Emit fallback event
     */
    emitFallbackEvent(errorRecord) {
        const event = new CustomEvent('errorFallback', {
            detail: { errorRecord }
        });
        window.dispatchEvent(event);
    }
    
    /**
     * Emit degradation event
     */
    emitDegradationEvent(errorRecord) {
        const event = new CustomEvent('errorDegrade', {
            detail: { errorRecord }
        });
        window.dispatchEvent(event);
    }
    
    /**
     * Emit restart event
     */
    emitRestartEvent(errorRecord) {
        const event = new CustomEvent('errorRestart', {
            detail: { errorRecord }
        });
        window.dispatchEvent(event);
    }
    
    /**
     * Send error to external logging service
     */
    sendToExternalLogger(errorRecord) {
        // TODO: Implement external logging service integration
        // This could send to services like Sentry, LogRocket, etc.
    }
    
    /**
     * Generate unique error ID
     */
    generateErrorId() {
        return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Get session ID
     */
    getSessionId() {
        let sessionId = sessionStorage.getItem('error_manager_session_id');
        if (!sessionId) {
            sessionId = `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            sessionStorage.setItem('error_manager_session_id', sessionId);
        }
        return sessionId;
    }
    
    /**
     * Trim error history to prevent memory bloat
     */
    trimErrorHistory() {
        const maxHistorySize = 100;
        if (this.errorHistory.length > maxHistorySize) {
            this.errorHistory = this.errorHistory.slice(-maxHistorySize);
        }
    }
    
    /**
     * Get error statistics
     */
    getErrorStats() {
        const stats = {
            totalErrors: this.errorHistory.length,
            severityBreakdown: {},
            errorCodeBreakdown: {},
            recentErrors: this.errorHistory.slice(-10)
        };
        
        // Calculate severity breakdown
        for (const severity of Object.values(this.severityLevels)) {
            stats.severityBreakdown[severity] = this.errorHistory.filter(
                error => error.severity === severity
            ).length;
        }
        
        // Calculate error code breakdown
        for (const error of this.errorHistory) {
            stats.errorCodeBreakdown[error.errorCode] = 
                (stats.errorCodeBreakdown[error.errorCode] || 0) + 1;
        }
        
        return stats;
    }
    
    /**
     * Clear error history
     */
    clearErrorHistory() {
        this.errorHistory = [];
        this.recoveryAttempts.clear();
    }
}

// Global error manager instance
window.ErrorManager = window.ErrorManager || new ErrorManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorManager;
}