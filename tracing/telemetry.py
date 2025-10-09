"""
OpenTelemetry Distributed Tracing Implementation
Complete observability with traces, metrics, and logs
"""

import os
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from contextlib import contextmanager
import structlog

# OpenTelemetry imports
from opentelemetry import trace, metrics, baggage
from opentelemetry.context import attach, detach
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.propagate import inject, extract
from opentelemetry.sdk.metrics import MeterProvider, Counter, Histogram, UpDownCounter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.metrics import get_meter_provider, set_meter_provider
from prometheus_client import start_http_server

logger = structlog.get_logger()


class TelemetryConfig:
    """Configuration for OpenTelemetry."""
    
    def __init__(self):
        self.service_name = os.getenv("SERVICE_NAME", "qwen-messaging-agent")
        self.service_version = os.getenv("SERVICE_VERSION", "1.0.0")
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Exporter configurations
        self.otlp_endpoint = os.getenv("OTLP_ENDPOINT", "localhost:4317")
        self.jaeger_endpoint = os.getenv("JAEGER_ENDPOINT", "localhost:14250")
        self.prometheus_port = int(os.getenv("PROMETHEUS_PORT", "9090"))
        
        # Sampling configuration
        self.sampling_rate = float(os.getenv("SAMPLING_RATE", "1.0"))  # 1.0 = 100%
        
        # Feature flags
        self.enable_console_export = os.getenv("ENABLE_CONSOLE_EXPORT", "false").lower() == "true"
        self.enable_jaeger = os.getenv("ENABLE_JAEGER", "true").lower() == "true"
        self.enable_otlp = os.getenv("ENABLE_OTLP", "false").lower() == "true"
        self.enable_prometheus = os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true"


class TelemetryManager:
    """Manages OpenTelemetry setup and instrumentation."""
    
    def __init__(self, config: Optional[TelemetryConfig] = None):
        self.config = config or TelemetryConfig()
        self.tracer_provider = None
        self.meter_provider = None
        self.tracer = None
        self.meter = None
        
        # Metrics
        self.request_counter = None
        self.request_duration = None
        self.active_requests = None
        self.error_counter = None
        self.cache_hits = None
        self.cache_misses = None
        
        self._initialize()
    
    def _initialize(self):
        """Initialize OpenTelemetry providers and exporters."""
        # Create resource
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: self.config.service_name,
            ResourceAttributes.SERVICE_VERSION: self.config.service_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.config.environment,
            ResourceAttributes.HOST_NAME: os.uname().nodename,
        })
        
        # Initialize tracing
        self._init_tracing(resource)
        
        # Initialize metrics
        self._init_metrics(resource)
        
        # Auto-instrument libraries
        self._auto_instrument()
        
        logger.info("Telemetry initialized", 
                   service=self.config.service_name,
                   environment=self.config.environment)
    
    def _init_tracing(self, resource: Resource):
        """Initialize tracing with configured exporters."""
        self.tracer_provider = TracerProvider(resource=resource)
        
        # Add exporters
        if self.config.enable_console_export:
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )
        
        if self.config.enable_jaeger:
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.config.jaeger_endpoint.split(":")[0],
                agent_port=int(self.config.jaeger_endpoint.split(":")[1]),
                max_tag_value_length=256
            )
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
        
        if self.config.enable_otlp:
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.config.otlp_endpoint,
                insecure=True
            )
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
        
        # Set global tracer provider
        trace.set_tracer_provider(self.tracer_provider)
        self.tracer = trace.get_tracer(self.config.service_name)
    
    def _init_metrics(self, resource: Resource):
        """Initialize metrics with configured exporters."""
        readers = []
        
        if self.config.enable_prometheus:
            # Start Prometheus metrics server
            start_http_server(self.config.prometheus_port)
            readers.append(PrometheusMetricReader())
        
        if self.config.enable_otlp:
            readers.append(
                OTLPMetricExporter(
                    endpoint=self.config.otlp_endpoint,
                    insecure=True
                )
            )
        
        self.meter_provider = MeterProvider(resource=resource, metric_readers=readers)
        set_meter_provider(self.meter_provider)
        self.meter = get_meter_provider().get_meter(self.config.service_name)
        
        # Create metrics
        self._create_metrics()
    
    def _create_metrics(self):
        """Create application metrics."""
        self.request_counter = self.meter.create_counter(
            name="http_requests_total",
            description="Total number of HTTP requests",
            unit="1"
        )
        
        self.request_duration = self.meter.create_histogram(
            name="http_request_duration_seconds",
            description="HTTP request duration in seconds",
            unit="s"
        )
        
        self.active_requests = self.meter.create_up_down_counter(
            name="http_requests_active",
            description="Number of active HTTP requests",
            unit="1"
        )
        
        self.error_counter = self.meter.create_counter(
            name="errors_total",
            description="Total number of errors",
            unit="1"
        )
        
        self.cache_hits = self.meter.create_counter(
            name="cache_hits_total",
            description="Total number of cache hits",
            unit="1"
        )
        
        self.cache_misses = self.meter.create_counter(
            name="cache_misses_total",
            description="Total number of cache misses",
            unit="1"
        )
    
    def _auto_instrument(self):
        """Auto-instrument common libraries."""
        # Instrument Redis
        RedisInstrumentor().instrument()
        
        # Instrument Requests
        RequestsInstrumentor().instrument()
        
        # Instrument Logging
        LoggingInstrumentor().instrument()
    
    def instrument_fastapi(self, app):
        """Instrument FastAPI application."""
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented")
    
    def create_span(self, name: str, kind: SpanKind = SpanKind.INTERNAL) -> trace.Span:
        """Create a new span."""
        return self.tracer.start_span(name, kind=kind)
    
    @contextmanager
    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Context manager for creating spans."""
        with self.tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
    
    def traced(self, name: Optional[str] = None, kind: SpanKind = SpanKind.INTERNAL):
        """Decorator for tracing functions."""
        def decorator(func):
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.span(span_name) as span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    finally:
                        duration = time.time() - start_time
                        span.set_attribute("duration_ms", duration * 1000)
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.span(span_name) as span:
                    span.set_attribute("function.name", func.__name__)
                    span.set_attribute("function.module", func.__module__)
                    
                    start_time = time.time()
                    try:
                        result = await func(*args, **kwargs)
                        span.set_status(Status(StatusCode.OK))
                        return result
                    finally:
                        duration = time.time() - start_time
                        span.set_attribute("duration_ms", duration * 1000)
            
            import asyncio
            return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper
        
        return decorator
    
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        labels = {
            "method": method,
            "path": path,
            "status": str(status_code)
        }
        
        self.request_counter.add(1, labels)
        self.request_duration.record(duration, labels)
        
        if status_code >= 400:
            self.error_counter.add(1, {"type": "http", "status": str(status_code)})
    
    def record_cache_hit(self):
        """Record cache hit."""
        self.cache_hits.add(1)
    
    def record_cache_miss(self):
        """Record cache miss."""
        self.cache_misses.add(1)
    
    def add_baggage(self, key: str, value: str):
        """Add baggage to current context."""
        token = attach(baggage.set_baggage(key, value))
        return token
    
    def get_baggage(self, key: str) -> Optional[str]:
        """Get baggage from current context."""
        return baggage.get_baggage(key)
    
    def inject_context(self, carrier: Dict[str, str]):
        """Inject trace context into carrier for propagation."""
        inject(carrier)
    
    def extract_context(self, carrier: Dict[str, str]):
        """Extract trace context from carrier."""
        return extract(carrier)


# Global telemetry instance
_telemetry_instance: Optional[TelemetryManager] = None


def get_telemetry() -> TelemetryManager:
    """Get or create global telemetry instance."""
    global _telemetry_instance
    
    if _telemetry_instance is None:
        _telemetry_instance = TelemetryManager()
    
    return _telemetry_instance


class TracedCache:
    """Cache wrapper with tracing."""
    
    def __init__(self, cache, telemetry: TelemetryManager):
        self.cache = cache
        self.telemetry = telemetry
    
    def get(self, key: str) -> Optional[Any]:
        """Get with tracing."""
        with self.telemetry.span("cache.get", {"cache.key": key}) as span:
            value = self.cache.get(key)
            
            if value is not None:
                span.set_attribute("cache.hit", True)
                self.telemetry.record_cache_hit()
            else:
                span.set_attribute("cache.hit", False)
                self.telemetry.record_cache_miss()
            
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set with tracing."""
        with self.telemetry.span("cache.set", {"cache.key": key, "cache.ttl": ttl}):
            return self.cache.set(key, value, ttl)


class TracedEndpoint:
    """ML endpoint wrapper with tracing."""
    
    def __init__(self, endpoint, telemetry: TelemetryManager):
        self.endpoint = endpoint
        self.telemetry = telemetry
    
    def predict(self, instances: list) -> Any:
        """Predict with tracing."""
        with self.telemetry.span("model.predict") as span:
            span.set_attribute("model.input_size", len(str(instances)))
            span.set_attribute("model.instance_count", len(instances))
            
            start_time = time.time()
            result = self.endpoint.predict(instances)
            duration = time.time() - start_time
            
            span.set_attribute("model.prediction_time_ms", duration * 1000)
            span.set_attribute("model.output_size", len(str(result)))
            
            return result


# Middleware for FastAPI
class TelemetryMiddleware:
    """FastAPI middleware for telemetry."""
    
    def __init__(self, app, telemetry: TelemetryManager):
        self.app = app
        self.telemetry = telemetry
    
    async def __call__(self, request, call_next):
        # Start span
        span_name = f"{request.method} {request.url.path}"
        
        with self.telemetry.span(span_name, {
            SpanAttributes.HTTP_METHOD: request.method,
            SpanAttributes.HTTP_URL: str(request.url),
            SpanAttributes.HTTP_SCHEME: request.url.scheme,
            SpanAttributes.HTTP_HOST: request.url.hostname,
            SpanAttributes.HTTP_TARGET: request.url.path,
        }) as span:
            
            # Track active requests
            self.telemetry.active_requests.add(1)
            
            try:
                # Process request
                start_time = time.time()
                response = await call_next(request)
                duration = time.time() - start_time
                
                # Set response attributes
                span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, response.status_code)
                
                # Record metrics
                self.telemetry.record_request(
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration=duration
                )
                
                return response
                
            finally:
                self.telemetry.active_requests.add(-1)
