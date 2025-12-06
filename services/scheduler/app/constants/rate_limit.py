"""
Rate limiting constants for webhook execution and resource creation.

Rate limits:
- Free plan: 100 executions per day per webhook
- Pro plan: 10 executions per day per webhook
"""

# Rate limits per plan (executions per day per webhook)
RATE_LIMITS = {
    "free": 100,
    "pro": 1000,
}

# Creation limits per plan
# Free plan: 10 URLs, 10 jobs/schedules
# Pro plan: 10 URLs, 100 jobs/schedules
URL_CREATION_LIMITS = {
    "free": 10,  # None means unlimited
    "pro": 100,
}

JOB_CREATION_LIMITS = {
    "free": 10,
    "pro": 100,
}

# Redis key expiration time (24 hours in seconds)
REDIS_TTL = 24 * 60 * 60  # 86400 seconds
