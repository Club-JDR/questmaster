from api.utils.exceptions import RateLimited


def test_rateLimited():
    is_global = False
    message = "You are being rate limited."
    retry_after = 64.57
    headers = {
        "HTTP/1.1 429": "TOO MANY REQUESTS",
        "Content-Type": "application/json",
        "Retry-After": retry_after,
        "X-RateLimit-Limit": 10,
        "X-RateLimit-Remaining": 0,
        "X-RateLimit-Reset": 1470173023.123,
        "X-RateLimit-Reset-After": retry_after,
        "X-RateLimit-Bucket": "abcd1234",
        "X-RateLimit-Scope": "user",
    }
    json = {"message": message, "retry_after": retry_after, "global": is_global}
    error = RateLimited(json, headers)
    assert error.json == json
    assert error.headers == headers
    assert error.is_global == is_global
    assert error.message == message
    assert error.retry_after == retry_after
