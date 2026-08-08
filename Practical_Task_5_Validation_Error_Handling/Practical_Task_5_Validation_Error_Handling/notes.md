# Task 5 — Validation & Error Handling

## Challenge 1 — Validate User Input Before API Call

### Validation Rules

**Destination Field:**
- Cannot be empty or whitespace-only
- Cannot be only digits (e.g., "12345")
- Must be at least 2 characters long

**Number of Days Field:**
- Must be a valid integer (not a string like "abc")
- Must be at least 1 day
- Must not exceed 21 days (prevents excessive token usage and API cost)

### Implementation

The `get_user_input()` function uses two `while True` loops — one for destination, one for days. Each loop validates and re-prompts if invalid. Only returns when both inputs pass all checks.

### Before This Challenge

Without validation, typing "abc" for days caused:
The program crashed immediately.

### After This Challenge

Same bad input re-prompts with a clear message: "Please enter a valid number for days."

---

## Challenge 2 — Validate the Response Before Trusting It

### Approach

A manual validation function `validate_itinerary(data)` checks that the parsed JSON response matches the expected schema. Manual validation was chosen because the schema is simple (five fields) and adding a library dependency (like pydantic or jsonschema) is overkill for this size.

### Validation Rules

Each field is checked for:

**destination**
- Must exist
- Must be a string

**number_of_days**
- Must exist
- Must be an integer

**daily_activities**
- Must exist
- Must be a list
- Cannot be empty
- Each item must be a dictionary with "day" (integer) and "activities" (list of strings)

**estimated_budget**
- Must exist
- Must be a number (int or float)

**travel_tips**
- Must exist
- Must be a list
- Cannot be empty
- Each item must be a string

### Testing

A broken test case is included at the bottom (commented out):

```python
bad_test = {
    "destination": "Cairo",
    "number_of_days": "three",  # Wrong type: string instead of int
    "daily_activities": [],  # Wrong: empty list
    "estimated_budget": "around $800",  # Wrong type: string instead of number
    "travel_tips": ["Stay hydrated"]  # This one is correct
}
```

Uncommenting `test_broken_itinerary()` and running it correctly catches all errors:
- "Invalid type: 'number_of_days' should be an integer"
- "'daily_activities' list cannot be empty"
- "'estimated_budget' should be a number"

The function raises `ValueError` with a clear message on the first validation failure it encounters.

---

## Challenge 3 — Handle API Errors Gracefully

### Why Different Exceptions Need Different Responses

Not all failures are equal. Some are permanent (invalid API key), some are temporary (rate limit), and some are transient network blips. The retry strategy depends on the type.

### Exception Handling

**AuthenticationError**

- **Triggered by:** Invalid or expired API key in .env
- **Retry:** No
- **Response:** Clear message asking user to check their API key
- **Before:** Unhandled exception, raw traceback
- **After:** User-friendly error message, graceful exit

**RateLimitError**

- **Triggered by:** Too many requests to OpenAI API
- **Retry:** Yes, up to 3 attempts
- **Backoff:** Exponential (2s, 4s, 6s)
- **Response:** Shows "Rate limit hit. Waiting X seconds before retry..." between attempts
- **Before:** Unhandled exception
- **After:** Automatic retry with user feedback, then clear message if all retries exhaust

**APIConnectionError**

- **Triggered by:** Network timeout, DNS failure, connection refused
- **Retry:** Yes, up to 3 attempts
- **Backoff:** 1 second between retries
- **Response:** Shows "Connection error. Retrying..." between attempts
- **Before:** Unhandled exception
- **After:** Automatic retry with user feedback, then message to check internet connection

**BadRequestError**

- **Triggered by:** Malformed request (shouldn't happen with valid schema, but caught for safety)
- **Retry:** No
- **Response:** Show the error details
- **Before:** Unhandled exception
- **After:** User-friendly message explaining the request was invalid

**Generic Exception**

- **Triggered by:** Anything else unexpected
- **Retry:** No
- **Response:** Show the error message
- **Before:** Unhandled exception
- **After:** Caught and displayed, doesn't crash

### Retry Loop Location

Retry logic lives in `main()`, not in `call_openai()`. This keeps `call_openai()` simple and makes the retry strategy visible at the call site. Each attempt:

1. Tries to call OpenAI
2. On specific exceptions, decides whether to retry or fail
3. On success, breaks out of the loop
4. On permanent failure, returns early with a message

---

## Challenge 4 — Retry Policy

### Policy Summary

| Error Type | Auto Retry | Max Attempts | Backoff | Action if All Fail |
| --- | --- | --- | --- | --- |
| AuthenticationError | No | — | — | Show "Check your API key" |
| RateLimitError | Yes | 3 | 2s, 4s, 6s | Show "Rate limit exceeded, try later" |
| APIConnectionError | Yes | 3 | 1s each | Show "Check your internet connection" |
| BadRequestError | No | — | — | Show error details |
| Invalid User Input | No (loop locally) | ∞ | — | Re-prompt user until valid |
| Invalid JSON Response | No | — | — | Show "Invalid JSON" + finish_reason |
| Schema Validation Failure | No | — | — | Show validation error message |

### Rationale

**Retry on transient errors:** Rate limits and connection issues often succeed on retry because they're temporary.

**Don't retry on permanent errors:** Authentication and bad requests won't fix themselves by trying again.

**Validate early:** Input validation happens before any API call, saving time and tokens.

**Validate late:** Response validation happens before displaying data to the user, preventing bad data from leaking through.

### Adjusting the Policy

**If users report "the app hangs, retrying forever":**
- Reduce the max retry count from 3 to 2
- Reduce backoff wait times

**If users report "it gives up too fast":**
- Increase the max retry count from 3 to 5
- Increase backoff wait times

**If cost becomes an issue:**
- Validate input more strictly to prevent wasted API calls
- Reduce max_tokens in `call_openai()` if responses are still complete

---

## Summary

Task 5 wraps the Task 4 travel planner with four layers of defense:

1. **Input validation** — only valid destination and days reach the API
2. **Response validation** — parsed JSON is checked against the schema before display
3. **Error handling** — specific exceptions are caught and handled appropriately
4. **Retry policy** — transient failures retry; permanent ones fail quickly

The result is a robust CLI tool that never crashes with a raw traceback, clearly communicates what went wrong, and recovers gracefully from temporary issues.