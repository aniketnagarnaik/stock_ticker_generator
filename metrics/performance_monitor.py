"""
Performance Monitor - Production-Ready Monitoring System
Comprehensive metrics tracking for stock data processing and stress testing
"""

import time
import psutil
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class PerformanceMetrics:
    """Data class for storing performance metrics"""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    memory_before: float
    memory_after: float
    memory_delta: float
    peak_memory: float
    api_calls: int
    success_count: int
    failure_count: int
    data_processed: int
    error_messages: List[str]
    metadata: Dict[str, Any]


class PerformanceMonitor:
    """
    Production-ready performance monitoring system
    Tracks timing, memory, API calls, and processing metrics
    """
    
    def __init__(self, enable_memory_monitoring: bool = True):
        self.enable_memory_monitoring = enable_memory_monitoring
        self.metrics_history: List[PerformanceMetrics] = []
        self.current_operation: Optional[PerformanceMetrics] = None
        self.session_start_time = time.time()
        self.session_peak_memory = 0
        self.total_api_calls = 0
        self.total_successes = 0
        self.total_failures = 0
        
        # Initialize baseline memory
        if self.enable_memory_monitoring:
            self.baseline_memory = self._get_memory_usage()
            self.session_peak_memory = self.baseline_memory
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except Exception:
            return 0.0
    
    def _update_session_peak_memory(self):
        """Update session peak memory usage"""
        if self.enable_memory_monitoring:
            current_memory = self._get_memory_usage()
            if current_memory > self.session_peak_memory:
                self.session_peak_memory = current_memory
    
    @contextmanager
    def monitor_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for monitoring operations
        Usage:
            with monitor.monitor_operation("fetch_stock_data", {"symbol": "AAPL"}):
                # Your operation here
                pass
        """
        if metadata is None:
            metadata = {}
        
        # Start monitoring
        start_time = time.time()
        memory_before = self._get_memory_usage()
        peak_memory = memory_before
        
        self.current_operation = PerformanceMetrics(
            operation_name=operation_name,
            start_time=start_time,
            end_time=0,
            duration=0,
            memory_before=memory_before,
            memory_after=0,
            memory_delta=0,
            peak_memory=peak_memory,
            api_calls=0,
            success_count=0,
            failure_count=0,
            data_processed=0,
            error_messages=[],
            metadata=metadata.copy()
        )
        
        try:
            yield self.current_operation
        except Exception as e:
            self.current_operation.error_messages.append(str(e))
            self.current_operation.failure_count += 1
            self.total_failures += 1
            raise
        finally:
            # End monitoring
            end_time = time.time()
            memory_after = self._get_memory_usage()
            
            self.current_operation.end_time = end_time
            self.current_operation.duration = end_time - start_time
            self.current_operation.memory_after = memory_after
            self.current_operation.memory_delta = memory_after - memory_before
            self.current_operation.peak_memory = max(peak_memory, memory_after)
            
            # Update session totals
            self.total_api_calls += self.current_operation.api_calls
            self.total_successes += self.current_operation.success_count
            
            # Store metrics
            self.metrics_history.append(self.current_operation)
            self._update_session_peak_memory()
            
            # Reset current operation
            self.current_operation = None
    
    def record_api_call(self, success: bool = True, response_time: Optional[float] = None):
        """Record an API call"""
        if self.current_operation:
            self.current_operation.api_calls += 1
            if success:
                self.current_operation.success_count += 1
            else:
                self.current_operation.failure_count += 1
            
            if response_time:
                if 'api_response_times' not in self.current_operation.metadata:
                    self.current_operation.metadata['api_response_times'] = []
                self.current_operation.metadata['api_response_times'].append(response_time)
    
    def record_data_processed(self, count: int):
        """Record amount of data processed"""
        if self.current_operation:
            self.current_operation.data_processed += count
    
    def record_error(self, error_message: str):
        """Record an error message"""
        if self.current_operation:
            self.current_operation.error_messages.append(error_message)
            self.current_operation.failure_count += 1
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        session_duration = time.time() - self.session_start_time
        
        # Calculate totals
        total_operations = len(self.metrics_history)
        total_duration = sum(m.duration for m in self.metrics_history)
        total_memory_delta = sum(m.memory_delta for m in self.metrics_history)
        
        # Calculate averages
        avg_operation_time = total_duration / total_operations if total_operations > 0 else 0
        avg_memory_delta = total_memory_delta / total_operations if total_operations > 0 else 0
        
        # Find slowest operation
        slowest_operation = max(self.metrics_history, key=lambda m: m.duration) if self.metrics_history else None
        
        # Find highest memory usage
        highest_memory = max(self.metrics_history, key=lambda m: m.peak_memory) if self.metrics_history else None
        
        return {
            'session_info': {
                'start_time': datetime.fromtimestamp(self.session_start_time).isoformat(),
                'duration_seconds': round(session_duration, 2),
                'total_operations': total_operations
            },
            'performance_summary': {
                'total_duration': round(total_duration, 2),
                'average_operation_time': round(avg_operation_time, 2),
                'slowest_operation': {
                    'name': slowest_operation.operation_name,
                    'duration': round(slowest_operation.duration, 2)
                } if slowest_operation else None
            },
            'memory_summary': {
                'baseline_memory_mb': round(self.baseline_memory, 2),
                'peak_memory_mb': round(self.session_peak_memory, 2),
                'total_memory_delta_mb': round(total_memory_delta, 2),
                'average_memory_delta_mb': round(avg_memory_delta, 2),
                'highest_memory_operation': {
                    'name': highest_memory.operation_name,
                    'peak_memory_mb': round(highest_memory.peak_memory, 2)
                } if highest_memory else None
            },
            'api_summary': {
                'total_api_calls': self.total_api_calls,
                'total_successes': self.total_successes,
                'total_failures': self.total_failures,
                'success_rate': round((self.total_successes / self.total_api_calls * 100), 2) if self.total_api_calls > 0 else 0
            },
            'data_processing': {
                'total_data_processed': sum(m.data_processed for m in self.metrics_history),
                'operations_per_second': round(total_operations / session_duration, 2) if session_duration > 0 else 0
            }
        }
    
    def get_operation_breakdown(self) -> List[Dict[str, Any]]:
        """Get detailed breakdown of all operations"""
        return [
            {
                'operation': m.operation_name,
                'duration_seconds': round(m.duration, 2),
                'memory_delta_mb': round(m.memory_delta, 2),
                'peak_memory_mb': round(m.peak_memory, 2),
                'api_calls': m.api_calls,
                'success_count': m.success_count,
                'failure_count': m.failure_count,
                'data_processed': m.data_processed,
                'error_count': len(m.error_messages),
                'metadata': m.metadata
            }
            for m in self.metrics_history
        ]
    
    def export_metrics(self, filename: Optional[str] = None) -> str:
        """Export metrics to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"performance_metrics_{timestamp}.json"
        
        export_data = {
            'session_summary': self.get_session_summary(),
            'operation_breakdown': self.get_operation_breakdown(),
            'raw_metrics': [asdict(m) for m in self.metrics_history]
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return filename
    
    def print_summary(self):
        """Print a formatted summary to console"""
        summary = self.get_session_summary()
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE MONITOR SUMMARY")
        print("="*60)
        
        # Session Info
        print(f"⏱️  Session Duration: {summary['session_info']['duration_seconds']}s")
        print(f"🔄 Total Operations: {summary['session_info']['total_operations']}")
        
        # Performance
        print(f"\n⚡ Performance:")
        print(f"   Total Time: {summary['performance_summary']['total_duration']}s")
        print(f"   Average per Operation: {summary['performance_summary']['average_operation_time']}s")
        if summary['performance_summary']['slowest_operation']:
            slowest = summary['performance_summary']['slowest_operation']
            print(f"   Slowest: {slowest['name']} ({slowest['duration']}s)")
        
        # Memory
        print(f"\n🧠 Memory:")
        print(f"   Baseline: {summary['memory_summary']['baseline_memory_mb']} MB")
        print(f"   Peak: {summary['memory_summary']['peak_memory_mb']} MB")
        print(f"   Total Delta: {summary['memory_summary']['total_memory_delta_mb']} MB")
        if summary['memory_summary']['highest_memory_operation']:
            highest = summary['memory_summary']['highest_memory_operation']
            print(f"   Highest: {highest['name']} ({highest['peak_memory_mb']} MB)")
        
        # API
        print(f"\n🌐 API Calls:")
        print(f"   Total: {summary['api_summary']['total_api_calls']}")
        print(f"   Success Rate: {summary['api_summary']['success_rate']}%")
        print(f"   Failures: {summary['api_summary']['total_failures']}")
        
        # Data Processing
        print(f"\n📈 Data Processing:")
        print(f"   Total Processed: {summary['data_processing']['total_data_processed']}")
        print(f"   Operations/sec: {summary['data_processing']['operations_per_second']}")
        
        print("="*60)


# Global instance for easy access
_global_monitor = None

def get_global_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor

def reset_global_monitor():
    """Reset the global performance monitor"""
    global _global_monitor
    _global_monitor = None


# Example usage
if __name__ == "__main__":
    # Example usage
    monitor = PerformanceMonitor()
    
    with monitor.monitor_operation("test_operation", {"test": True}):
        time.sleep(0.1)  # Simulate work
        monitor.record_api_call(success=True, response_time=0.05)
        monitor.record_data_processed(100)
    
    monitor.print_summary()
    monitor.export_metrics("test_metrics.json")
