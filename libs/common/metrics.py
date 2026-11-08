
from prometheus_client import Counter, Histogram, Gauge


# Total HTTP requests received by the API.
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

# Time taken to process HTTP requests.
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request processing duration in seconds",
    ["method", "endpoint"],
)

# Total FNOL submissions rejected during validation.
FNOL_REJECTED = Counter(
    "fnol_rejected_total",
    "Total number of rejected FNOL submissions",
    ["reason"],
)

# Total claim runs started.
RUNS_STARTED = Counter(
    "runs_started_total",
    "Total number of claim runs started",
)

# Time taken to process a claim run.
RUN_DURATION = Histogram(
    "run_duration_seconds",
    "Claim run processing duration in seconds",
    ["status"],
)

# Total agent tasks executed.
AGENT_TASKS = Counter(
    "agent_tasks_total",
    "Total number of agent tasks executed",
    ["agent", "status"],
)

# Number of processing steps in each claim run.
STEPS_PER_RUN = Histogram(
    "steps_per_run",
    "Number of processing steps per claim run",
)

# Current number of items waiting in a queue.
QUEUE_DEPTH = Gauge(
    "queue_depth",
    "Current number of tasks waiting in a queue",
    ["queue"],
)

# Total cache hits and misses.
CACHE_REQUESTS = Counter(
    "cache_requests_total",
    "Total cache requests",
    ["result"],
)
