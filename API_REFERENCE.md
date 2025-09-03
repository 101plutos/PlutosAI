# PlutosAI API Reference

Complete API reference for the PlutosAI platform.

## Table of Contents

- [Authentication](#authentication)
- [Base URLs](#base-urls)
- [Rate Limits](#rate-limits)
- [Data Processing](#data-processing)
- [Batch Processing](#batch-processing)
- [Stream Processing](#stream-processing)
- [Models](#models)
- [Usage & Billing](#usage--billing)
- [Error Codes](#error-codes)

## Authentication

All API requests require authentication using an API key. Include your API key in the request headers:

```bash
Authorization: Bearer YOUR_API_KEY
```

### API Key Management

- **Get API Key**: Obtain from [PlutosAI Dashboard](https://dashboard.plutos-ai.com)
- **Key Permissions**: Each key has specific permissions and rate limits
- **Key Rotation**: Rotate keys regularly for security

## Base URLs

| Environment | URL |
|-------------|-----|
| Production | `https://api.plutos-ai.com/v1` |
| Staging | `https://staging-api.plutos-ai.com/v1` |
| Development | `http://localhost:3000/v1` |

## Rate Limits

| Plan | Requests per minute | Requests per hour | Concurrent requests |
|------|-------------------|------------------|-------------------|
| Free | 60 | 1,000 | 5 |
| Pro | 300 | 10,000 | 20 |
| Enterprise | 1,000 | 100,000 | 100 |

Rate limit headers are included in all responses:

```bash
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

## Data Processing

### POST /process

Process a single input with an AI model.

**Endpoint:** `POST /process`

**Headers:**
```bash
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "input": "string (required)",
  "model": "string (required)",
  "options": {
    "temperature": "number (optional, default: 0.7)",
    "maxTokens": "number (optional, default: 1000)",
    "topP": "number (optional, default: 1.0)",
    "frequencyPenalty": "number (optional, default: 0.0)",
    "presencePenalty": "number (optional, default: 0.0)",
    "systemPrompt": "string (optional)",
    "stop": ["string"] (optional)
  }
}
```

**Response (200 OK):**
```json
{
  "id": "string",
  "output": "string",
  "model": "string",
  "usage": {
    "promptTokens": "number",
    "completionTokens": "number",
    "totalTokens": "number"
  },
  "createdAt": "string (ISO 8601)",
  "processingTime": "number (milliseconds)"
}
```

**Example Request:**
```bash
curl -X POST https://api.plutos-ai.com/v1/process \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "What is the capital of France?",
    "model": "gpt-4",
    "options": {
      "temperature": 0.7,
      "maxTokens": 100,
      "systemPrompt": "You are a helpful assistant."
    }
  }'
```

**Example Response:**
```json
{
  "id": "proc_1234567890abcdef",
  "output": "The capital of France is Paris.",
  "model": "gpt-4",
  "usage": {
    "promptTokens": 15,
    "completionTokens": 8,
    "totalTokens": 23
  },
  "createdAt": "2024-01-01T12:00:00Z",
  "processingTime": 1250
}
```

### GET /process/{id}

Retrieve a specific processing result by ID.

**Endpoint:** `GET /process/{id}`

**Headers:**
```bash
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "id": "string",
  "input": "string",
  "output": "string",
  "model": "string",
  "options": "object",
  "usage": "object",
  "createdAt": "string",
  "processingTime": "number"
}
```

## Batch Processing

### POST /batch

Process multiple inputs in a single request.

**Endpoint:** `POST /batch`

**Headers:**
```bash
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "inputs": ["string (required, max 100 items)"],
  "model": "string (required)",
  "options": {
    "temperature": "number (optional, default: 0.7)",
    "maxTokens": "number (optional, default: 1000)",
    "topP": "number (optional, default: 1.0)",
    "systemPrompt": "string (optional)"
  }
}
```

**Response (200 OK):**
```json
{
  "id": "string",
  "results": [
    {
      "input": "string",
      "output": "string",
      "usage": {
        "promptTokens": "number",
        "completionTokens": "number",
        "totalTokens": "number"
      }
    }
  ],
  "totalUsage": {
    "promptTokens": "number",
    "completionTokens": "number",
    "totalTokens": "number"
  },
  "createdAt": "string",
  "processingTime": "number"
}
```

**Example Request:**
```bash
curl -X POST https://api.plutos-ai.com/v1/batch \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": [
      "What is the capital of France?",
      "What is the capital of Germany?",
      "What is the capital of Italy?"
    ],
    "model": "gpt-4",
    "options": {
      "temperature": 0.3,
      "maxTokens": 50
    }
  }'
```

## Stream Processing

### POST /stream

Stream data processing results in real-time using Server-Sent Events (SSE).

**Endpoint:** `POST /stream`

**Headers:**
```bash
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
Accept: text/event-stream
```

**Request Body:**
```json
{
  "input": "string (required)",
  "model": "string (required)",
  "options": {
    "temperature": "number (optional, default: 0.7)",
    "maxTokens": "number (optional, default: 1000)",
    "topP": "number (optional, default: 1.0)",
    "systemPrompt": "string (optional)"
  }
}
```

**Response (Server-Sent Events):**
```
event: chunk
data: {"chunk": "partial", "output": "Hello"}

event: chunk
data: {"chunk": "partial", "output": " world"}

event: chunk
data: {"chunk": "partial", "output": "!"}

event: complete
data: {"chunk": "final", "output": "Hello world!", "usage": {...}}
```

**JavaScript Example:**
```javascript
const response = await fetch('https://api.plutos-ai.com/v1/stream', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream'
  },
  body: JSON.stringify({
    input: 'Write a short story about a robot.',
    model: 'gpt-4'
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      if (data.chunk === 'partial') {
        process.stdout.write(data.output);
      } else if (data.chunk === 'final') {
        console.log('\nComplete!');
      }
    }
  }
}
```

## Models

### GET /models

List all available AI models.

**Endpoint:** `GET /models`

**Headers:**
```bash
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "models": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "maxTokens": "number",
      "supportsStreaming": "boolean",
      "pricing": {
        "inputTokens": "number (per 1K tokens)",
        "outputTokens": "number (per 1K tokens)"
      }
    }
  ]
}
```

**Example Response:**
```json
{
  "models": [
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "description": "Most capable GPT model for complex reasoning tasks",
      "maxTokens": 8192,
      "supportsStreaming": true,
      "pricing": {
        "inputTokens": 0.03,
        "outputTokens": 0.06
      }
    },
    {
      "id": "gpt-3.5-turbo",
      "name": "GPT-3.5 Turbo",
      "description": "Fast and efficient model for most tasks",
      "maxTokens": 4096,
      "supportsStreaming": true,
      "pricing": {
        "inputTokens": 0.0015,
        "outputTokens": 0.002
      }
    }
  ]
}
```

## Usage & Billing

### GET /usage

Get current usage statistics.

**Endpoint:** `GET /usage`

**Query Parameters:**
- `start_date` (optional): Start date in YYYY-MM-DD format
- `end_date` (optional): End date in YYYY-MM-DD format

**Headers:**
```bash
Authorization: Bearer YOUR_API_KEY
```

**Response (200 OK):**
```json
{
  "period": {
    "start": "string (ISO 8601)",
    "end": "string (ISO 8601)"
  },
  "usage": {
    "totalRequests": "number",
    "totalTokens": "number",
    "totalCost": "number (USD)",
    "requestsByModel": {
      "gpt-4": "number",
      "gpt-3.5-turbo": "number"
    }
  },
  "limits": {
    "requestsPerMinute": "number",
    "requestsPerHour": "number",
    "requestsPerDay": "number"
  }
}
```

## Error Codes

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 502 | Bad Gateway - Upstream service error |
| 503 | Service Unavailable - Service temporarily unavailable |

### Error Response Format

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object (optional)",
    "requestId": "string (optional)"
  }
}
```

### Common Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| `invalid_api_key` | API key is invalid or expired | Check your API key |
| `rate_limit_exceeded` | Rate limit exceeded | Wait or upgrade plan |
| `invalid_model` | Model not found or not available | Check available models |
| `input_too_long` | Input exceeds maximum length | Reduce input size |
| `invalid_parameters` | Invalid request parameters | Check parameter format |
| `insufficient_quota` | Account quota exceeded | Upgrade plan or wait |

**Example Error Response:**
```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Try again in 60 seconds.",
    "details": {
      "retryAfter": 60
    },
    "requestId": "req_1234567890abcdef"
  }
}
```

## SDK Examples

### JavaScript/TypeScript

```javascript
import { PlutosAI } from '@plutos-ai/sdk';

const client = new PlutosAI({
  apiKey: 'your-api-key',
  environment: 'production'
});

// Process data
try {
  const result = await client.processData({
    input: 'What is the capital of France?',
    model: 'gpt-4',
    options: {
      temperature: 0.7,
      maxTokens: 100
    }
  });
  
  console.log(result.output);
} catch (error) {
  console.error('Error:', error.message);
}
```

### Python

```python
from plutos_ai import PlutosAI

client = PlutosAI(
    api_key="your-api-key",
    environment="production"
)

try:
    result = client.process_data(
        input="What is the capital of France?",
        model="gpt-4",
        options={
            "temperature": 0.7,
            "max_tokens": 100
        }
    )
    
    print(result.output)
except Exception as e:
    print(f"Error: {e}")
```

### Go

```go
package main

import (
    "fmt"
    "log"
    
    "github.com/plutos-ai/go-sdk"
)

func main() {
    client := plutos.NewClient("your-api-key", "production")
    
    result, err := client.ProcessData(plutos.ProcessRequest{
        Input: "What is the capital of France?",
        Model: "gpt-4",
        Options: plutos.ProcessOptions{
            Temperature: 0.7,
            MaxTokens:   100,
        },
    })
    
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Println(result.Output)
}
```

## Webhooks

### POST /webhooks

Configure webhooks for real-time notifications.

**Endpoint:** `POST /webhooks`

**Request Body:**
```json
{
  "url": "string (required)",
  "events": ["string (required)"],
  "secret": "string (optional)"
}
```

**Available Events:**
- `processing.completed` - When processing completes
- `processing.failed` - When processing fails
- `usage.threshold` - When usage reaches threshold

**Webhook Payload:**
```json
{
  "event": "string",
  "timestamp": "string (ISO 8601)",
  "data": "object",
  "signature": "string (if secret provided)"
}
```

## Best Practices

### Performance

1. **Use appropriate models** for your use case
2. **Optimize input length** to minimize token usage
3. **Implement caching** for repeated requests
4. **Use batch processing** for multiple inputs
5. **Handle rate limits** gracefully

### Security

1. **Keep API keys secure** and rotate regularly
2. **Validate inputs** before sending to API
3. **Use HTTPS** for all requests
4. **Implement proper error handling**
5. **Monitor usage** and set up alerts

### Reliability

1. **Implement retry logic** with exponential backoff
2. **Handle timeouts** appropriately
3. **Use webhooks** for critical operations
4. **Monitor API status** and health
5. **Have fallback strategies** for outages
