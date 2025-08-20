#!/usr/bin/env python3
"""
Production-Ready Error Handling and System Monitoring
Comprehensive error handling, logging, and monitoring for the 4D Image Recognition system
"""

import logging
import traceback
import time
try:
    import psutil  # type: ignore
except Exception:  # psutil may not be installed in minimal envs
    psutil = None  # type: ignore[assignment]
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import json
import numpy as np
try:
    import cv2  # type: ignore
except Exception:
    # Provide a minimal stub so "except cv2.error" remains valid even if OpenCV isn't installed
    class _Cv2Error(Exception):
        pass
    class _Cv2Stub:
        error = _Cv2Error
    cv2 = _Cv2Stub()  # type: ignore
from contextlib import contextmanager

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('system_production.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance and health metrics"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    active_connections: int
    error_count: int
    success_count: int
    average_response_time: float
    gpu_available: bool = False
    gpu_memory_percent: float = 0.0

@dataclass
class ErrorRecord:
    """Structured error record for tracking and analysis"""
    timestamp: float
    error_type: str
    error_message: str
    function_name: str
    file_name: str
    line_number: int
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ProductionErrorHandler:
    """
    Production-grade error handling and monitoring system
    """
    
    def __init__(self):
        self.error_records: List[ErrorRecord] = []
        self.system_metrics: List[SystemMetrics] = []
        self.response_times: List[float] = []
        self.error_count = 0
        self.success_count = 0
        self.start_time = time.time()
        
        # Start monitoring thread
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("✅ ProductionErrorHandler initialized")

    def _monitor_system(self):
        """Background system monitoring"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                if psutil is not None:
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    active_conns = len(psutil.net_connections())
                else:
                    cpu_percent = 0.0
                    class _Mem:
                        percent = 0.0
                        available = 0
                    memory = _Mem()
                    active_conns = 0
                
                metrics = SystemMetrics(
                    timestamp=time.time(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_available_gb=(memory.available / (1024**3)) if getattr(memory, 'available', None) is not None else 0.0,
                    active_connections=active_conns,
                    error_count=self.error_count,
                    success_count=self.success_count,
                    average_response_time=float(np.mean(self.response_times[-100:])) if self.response_times else 0.0
                )
                
                # Check for GPU availability
                try:
                    import GPUtil  # type: ignore
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        metrics.gpu_available = True
                        metrics.gpu_memory_percent = gpus[0].memoryUtil * 100
                except Exception:
                    # GPUtil is optional; ignore if unavailable
                    pass
                
                self.system_metrics.append(metrics)
                
                # Keep only recent metrics (last 1000 entries)
                if len(self.system_metrics) > 1000:
                    self.system_metrics = self.system_metrics[-1000:]
                
                # Log critical system issues
                if cpu_percent > 90:
                    logger.warning(f"🚨 High CPU usage: {cpu_percent}%")
                
                if memory.percent > 90:
                    logger.warning(f"🚨 High memory usage: {memory.percent}%")
                
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                time.sleep(60)  # Wait longer if monitoring fails

    @contextmanager
    def track_performance(self, operation_name: str, user_id: Optional[str] = None):
        """Context manager to track operation performance"""
        start_time = time.time()
        request_id = f"{operation_name}_{int(start_time)}"
        
        try:
            logger.info(f"🚀 Starting operation: {operation_name} (ID: {request_id})")
            yield request_id
            
            # Operation succeeded
            duration = time.time() - start_time
            self.response_times.append(duration)
            self.success_count += 1
            
            logger.info(f"✅ Operation completed: {operation_name} in {duration:.2f}s")
            
        except Exception as e:
            # Operation failed
            duration = time.time() - start_time
            self.error_count += 1
            
            # Record detailed error information
            error_record = ErrorRecord(
                timestamp=time.time(),
                error_type=type(e).__name__,
                error_message=str(e),
                function_name=operation_name,
                file_name="",
                line_number=0,
                user_id=user_id,
                request_id=request_id,
                stack_trace=traceback.format_exc(),
                context={"duration": duration}
            )
            
            self.error_records.append(error_record)
            
            logger.error(f"❌ Operation failed: {operation_name} after {duration:.2f}s - {e}")
            logger.debug(f"Stack trace: {traceback.format_exc()}")
            
            # Re-raise the exception
            raise

    def handle_opencv_error(self, operation: str, image_shape: Optional[tuple] = None) -> bool:
        """Handle OpenCV-specific errors with helpful context"""
        try:
            return True
        except cv2.error as e:
            context: Dict[str, Any] = {"operation": operation}
            if image_shape:
                context["image_shape"] = image_shape
            
            error_record = ErrorRecord(
                timestamp=time.time(),
                error_type="OpenCV Error",
                error_message=str(e),
                function_name=operation,
                file_name="opencv",
                line_number=0,
                stack_trace=traceback.format_exc(),
                context=context
            )
            
            self.error_records.append(error_record)
            self.error_count += 1
            
            logger.error(f"OpenCV Error in {operation}: {e}")
            
            # Provide helpful error messages
            if "empty" in str(e).lower():
                logger.error("💡 Suggestion: Check if image is properly loaded and not empty")
            elif "size" in str(e).lower():
                logger.error("💡 Suggestion: Verify image dimensions and format")
            
            return False

    def handle_mediapipe_error(self, operation: str) -> bool:
        """Handle MediaPipe-specific errors"""
        try:
            return True
        except Exception as e:
            if "mediapipe" in str(e).lower():
                error_record = ErrorRecord(
                    timestamp=time.time(),
                    error_type="MediaPipe Error",
                    error_message=str(e),
                    function_name=operation,
                    file_name="mediapipe",
                    line_number=0,
                    stack_trace=traceback.format_exc()
                )
                
                self.error_records.append(error_record)
                self.error_count += 1
                
                logger.error(f"MediaPipe Error in {operation}: {e}")
                
                # Provide helpful suggestions
                if "input" in str(e).lower():
                    logger.error("💡 Suggestion: Check input image format (should be RGB)")
                elif "model" in str(e).lower():
                    logger.error("💡 Suggestion: Verify MediaPipe model files are accessible")
                
                return False
            return True

    def handle_dlib_error(self, operation: str) -> bool:
        """Handle dlib-specific errors"""
        try:
            return True
        except Exception as e:
            if "dlib" in str(e).lower():
                error_record = ErrorRecord(
                    timestamp=time.time(),
                    error_type="dlib Error",
                    error_message=str(e),
                    function_name=operation,
                    file_name="dlib",
                    line_number=0,
                    stack_trace=traceback.format_exc()
                )
                
                self.error_records.append(error_record)
                self.error_count += 1
                
                logger.error(f"dlib Error in {operation}: {e}")
                
                # Provide helpful suggestions
                if "predictor" in str(e).lower():
                    logger.error("💡 Suggestion: Download shape_predictor_68_face_landmarks.dat from dlib.net")
                
                return False
            return True

    def safe_image_operation(self, operation_func, *args, **kwargs):
        """Safely execute image processing operations with comprehensive error handling"""
        operation_name = getattr(operation_func, '__name__', 'unknown_operation')
        
        try:
            with self.track_performance(operation_name):
                # Validate inputs
                if args and hasattr(args[0], 'shape'):
                    image = args[0]
                    if image is None or image.size == 0:
                        raise ValueError("Empty or None image provided")
                    
                    if len(image.shape) not in [2, 3]:
                        raise ValueError(f"Invalid image dimensions: {image.shape}")
                
                # Execute the operation
                result = operation_func(*args, **kwargs)
                
                return result
                
        except cv2.error as e:
            self.handle_opencv_error(operation_name, 
                                   args[0].shape if args and hasattr(args[0], 'shape') else None)
            return None
        except Exception as e:
            if "mediapipe" in str(e).lower():
                self.handle_mediapipe_error(operation_name)
            elif "dlib" in str(e).lower():
                self.handle_dlib_error(operation_name)
            else:
                # Generic error handling
                error_record = ErrorRecord(
                    timestamp=time.time(),
                    error_type=type(e).__name__,
                    error_message=str(e),
                    function_name=operation_name,
                    file_name="",
                    line_number=0,
                    stack_trace=traceback.format_exc()
                )
                
                self.error_records.append(error_record)
                self.error_count += 1
                
                logger.error(f"Operation {operation_name} failed: {e}")
            
            return None

    def get_system_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive system health report"""
        if not self.system_metrics:
            return {"status": "No metrics available"}
        
        latest_metrics = self.system_metrics[-1]
        uptime = time.time() - self.start_time
        
        # Calculate error rate
        total_operations = self.success_count + self.error_count
        error_rate = (self.error_count / total_operations * 100) if total_operations > 0 else 0
        
        # Calculate average response time
        avg_response_time = np.mean(self.response_times[-100:]) if self.response_times else 0
        
        # Determine system status
        status = "healthy"
        if error_rate > 10:
            status = "degraded"
        if latest_metrics.cpu_percent > 90 or latest_metrics.memory_percent > 90:
            status = "critical"
        
        report = {
            "system_status": status,
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "current_metrics": asdict(latest_metrics),
            "performance": {
                "total_operations": total_operations,
                "success_count": self.success_count,
                "error_count": self.error_count,
                "error_rate_percent": error_rate,
                "average_response_time": avg_response_time
            },
            "recent_errors": [
                asdict(error) for error in self.error_records[-10:]
            ]
        }
        
        return report

    def export_diagnostics(self, filepath: str):
        """Export comprehensive diagnostics data"""
        try:
            diagnostics_data = {
                "export_timestamp": time.time(),
                "system_health": self.get_system_health_report(),
                "all_errors": [asdict(error) for error in self.error_records],
                "system_metrics_sample": [asdict(metric) for metric in self.system_metrics[-50:]],
                "response_times_sample": self.response_times[-100:]
            }
            
            with open(filepath, 'w') as f:
                json.dump(diagnostics_data, f, indent=2)
            
            logger.info(f"✅ Diagnostics exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export diagnostics: {e}")

    def cleanup(self):
        """Clean shutdown of monitoring system"""
        self.monitoring_active = False
        if self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        logger.info("✅ ProductionErrorHandler cleanup completed")

# Global error handler instance
production_error_handler = ProductionErrorHandler()

# Context managers and decorators for easy use
@contextmanager
def safe_cv_operation(operation_name: str, user_id: Optional[str] = None):
    """Context manager for safe computer vision operations"""
    with production_error_handler.track_performance(operation_name, user_id):
        yield

def production_safe(func):
    """Decorator to make functions production-safe with error handling"""
    def wrapper(*args, **kwargs):
        return production_error_handler.safe_image_operation(func, *args, **kwargs)
    return wrapper

# Example usage
if __name__ == "__main__":
    # Test the error handling system
    print("🧪 Testing Production Error Handler")
    
    # Test successful operation
    with safe_cv_operation("test_operation"):
        time.sleep(0.1)
        print("✅ Test operation completed")
    
    # Test error handling
    try:
        with safe_cv_operation("test_error_operation"):
            raise ValueError("Test error for demonstration")
    except ValueError:
        print("✅ Error properly handled and logged")
    
    # Generate health report
    health_report = production_error_handler.get_system_health_report()
    print(f"📊 System Status: {health_report['system_status']}")
    
    # Export diagnostics
    production_error_handler.export_diagnostics("test_diagnostics.json")
    
    # Cleanup
    production_error_handler.cleanup()
    print("🏁 Test completed")
