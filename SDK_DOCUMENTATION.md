# PlutosAI SDK Documentation

Complete documentation for PlutosAI SDKs across multiple programming languages.

## Table of Contents

- [JavaScript/TypeScript SDK](#javascripttypescript-sdk)
- [Python SDK](#python-sdk)
- [Go SDK](#go-sdk)
- [React SDK](#react-sdk)
- [Web Components](#web-components)
- [Common Patterns](#common-patterns)

## JavaScript/TypeScript SDK

### Installation

```bash
npm install @plutos-ai/sdk
# or
yarn add @plutos-ai/sdk
```

### Basic Usage

```typescript
import { PlutosAI } from '@plutos-ai/sdk';

const client = new PlutosAI({
  apiKey: 'your-api-key',
  environment: 'production' // 'production' | 'staging' | 'development'
});

// Process data
const result = await client.processData({
  input: 'What is the capital of France?',
  model: 'gpt-4',
  options: {
    temperature: 0.7,
    maxTokens: 1000
  }
});

console.log(result.output);
```

### Configuration Options

```typescript
interface PlutosAIConfig {
  apiKey: string;
  environment?: 'production' | 'staging' | 'development';
  timeout?: number; // Default: 30000ms
  retries?: number; // Default: 3
  baseURL?: string; // Override base URL
  headers?: Record<string, string>; // Additional headers
}
```

### Core Methods

#### processData()

Process a single input with an AI model.

```typescript
interface ProcessDataRequest {
  input: string;
  model: string;
  options?: {
    temperature?: number;
    maxTokens?: number;
    topP?: number;
    frequencyPenalty?: number;
    presencePenalty?: number;
    systemPrompt?: string;
    stop?: string[];
  };
}

interface ProcessDataResponse {
  id: string;
  output: string;
  model: string;
  usage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  createdAt: string;
  processingTime: number;
}

const result = await client.processData({
  input: 'Analyze this text for sentiment',
  model: 'gpt-4',
  options: {
    temperature: 0.3,
    maxTokens: 100,
    systemPrompt: 'You are a sentiment analysis expert.'
  }
});
```

#### batchProcess()

Process multiple inputs in a single request.

```typescript
interface BatchProcessRequest {
  inputs: string[];
  model: string;
  options?: {
    temperature?: number;
    maxTokens?: number;
    topP?: number;
    systemPrompt?: string;
  };
}

interface BatchProcessResponse {
  id: string;
  results: Array<{
    input: string;
    output: string;
    usage: {
      promptTokens: number;
      completionTokens: number;
      totalTokens: number;
    };
  }>;
  totalUsage: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  createdAt: string;
  processingTime: number;
}

const batchResult = await client.batchProcess({
  inputs: [
    'What is the capital of France?',
    'What is the capital of Germany?',
    'What is the capital of Italy?'
  ],
  model: 'gpt-4',
  options: {
    temperature: 0.3,
    maxTokens: 50
  }
});

batchResult.results.forEach((result, index) => {
  console.log(`Input ${index + 1}:`, result.output);
});
```

#### streamProcess()

Stream data processing results in real-time.

```typescript
interface StreamProcessRequest {
  input: string;
  model: string;
  options?: {
    temperature?: number;
    maxTokens?: number;
    topP?: number;
    systemPrompt?: string;
  };
}

interface StreamChunk {
  chunk: 'partial' | 'final';
  output: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

const stream = await client.streamProcess({
  input: 'Write a short story about a robot.',
  model: 'gpt-4'
});

for await (const chunk of stream) {
  if (chunk.chunk === 'partial') {
    process.stdout.write(chunk.output);
  } else if (chunk.chunk === 'final') {
    console.log('\nComplete!');
    console.log('Total tokens:', chunk.usage?.totalTokens);
  }
}
```

#### getModels()

Retrieve available AI models.

```typescript
interface Model {
  id: string;
  name: string;
  description: string;
  maxTokens: number;
  supportsStreaming: boolean;
  pricing: {
    inputTokens: number;
    outputTokens: number;
  };
}

const models = await client.getModels();
console.log('Available models:', models.map(m => m.name));
```

#### getUsage()

Get current usage statistics.

```typescript
interface UsageRequest {
  startDate?: string; // YYYY-MM-DD
  endDate?: string; // YYYY-MM-DD
}

interface UsageResponse {
  period: {
    start: string;
    end: string;
  };
  usage: {
    totalRequests: number;
    totalTokens: number;
    totalCost: number;
    requestsByModel: Record<string, number>;
  };
  limits: {
    requestsPerMinute: number;
    requestsPerHour: number;
    requestsPerDay: number;
  };
}

const usage = await client.getUsage({
  startDate: '2024-01-01',
  endDate: '2024-01-31'
});

console.log('Total cost:', usage.usage.totalCost);
```

### Error Handling

```typescript
import { PlutosAIError } from '@plutos-ai/sdk';

try {
  const result = await client.processData({
    input: 'Test input',
    model: 'gpt-4'
  });
} catch (error) {
  if (error instanceof PlutosAIError) {
    console.error('PlutosAI Error:', error.code, error.message);
    
    switch (error.code) {
      case 'rate_limit_exceeded':
        console.log('Retry after:', error.details?.retryAfter, 'seconds');
        break;
      case 'invalid_api_key':
        console.log('Check your API key');
        break;
      case 'insufficient_quota':
        console.log('Upgrade your plan');
        break;
    }
  } else {
    console.error('Unexpected error:', error);
  }
}
```

### Advanced Usage

#### Custom HTTP Client

```typescript
import { PlutosAI } from '@plutos-ai/sdk';
import axios from 'axios';

const customAxios = axios.create({
  timeout: 60000,
  headers: {
    'User-Agent': 'MyApp/1.0'
  }
});

const client = new PlutosAI({
  apiKey: 'your-api-key',
  httpClient: customAxios
});
```

#### Retry Logic

```typescript
const client = new PlutosAI({
  apiKey: 'your-api-key',
  retries: 5,
  retryDelay: 1000 // Base delay in ms
});

// Custom retry function
const processWithRetry = async (input: string) => {
  let lastError;
  
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      return await client.processData({ input, model: 'gpt-4' });
    } catch (error) {
      lastError = error;
      if (error.code === 'rate_limit_exceeded') {
        const delay = error.details?.retryAfter * 1000 || 60000;
        await new Promise(resolve => setTimeout(resolve, delay));
      } else if (attempt === 3) {
        throw error;
      } else {
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      }
    }
  }
  
  throw lastError;
};
```

## Python SDK

### Installation

```bash
pip install plutos-ai
# or
pip install plutos-ai[async]  # For async support
```

### Basic Usage

```python
from plutos_ai import PlutosAI

client = PlutosAI(
    api_key="your-api-key",
    environment="production"  # "production" | "staging" | "development"
)

# Process data
result = client.process_data(
    input="What is the capital of France?",
    model="gpt-4",
    options={
        "temperature": 0.7,
        "max_tokens": 1000
    }
)

print(result.output)
```

### Configuration Options

```python
from plutos_ai import PlutosAI

client = PlutosAI(
    api_key="your-api-key",
    environment="production",
    timeout=30,  # Default: 30 seconds
    retries=3,   # Default: 3
    base_url=None,  # Override base URL
    headers=None    # Additional headers
)
```

### Core Methods

#### process_data()

```python
result = client.process_data(
    input="Analyze this text for sentiment",
    model="gpt-4",
    options={
        "temperature": 0.3,
        "max_tokens": 100,
        "system_prompt": "You are a sentiment analysis expert."
    }
)

print(f"Output: {result.output}")
print(f"Tokens used: {result.usage.total_tokens}")
```

#### batch_process()

```python
batch_result = client.batch_process(
    inputs=[
        "What is the capital of France?",
        "What is the capital of Germany?",
        "What is the capital of Italy?"
    ],
    model="gpt-4",
    options={
        "temperature": 0.3,
        "max_tokens": 50
    }
)

for i, result in enumerate(batch_result.results):
    print(f"Input {i+1}: {result.output}")
```

#### stream_process()

```python
stream = client.stream_process(
    input="Write a short story about a robot.",
    model="gpt-4"
)

for chunk in stream:
    if chunk.chunk == "partial":
        print(chunk.output, end="", flush=True)
    elif chunk.chunk == "final":
        print(f"\nComplete! Tokens: {chunk.usage.total_tokens}")
```

### Async Usage

```python
import asyncio
from plutos_ai import AsyncPlutosAI

async def main():
    client = AsyncPlutosAI(api_key="your-api-key")
    
    # Async processing
    result = await client.process_data(
        input="What is the capital of France?",
        model="gpt-4"
    )
    
    print(result.output)

# Run async function
asyncio.run(main())
```

### Error Handling

```python
from plutos_ai import PlutosAIError

try:
    result = client.process_data(
        input="Test input",
        model="gpt-4"
    )
except PlutosAIError as e:
    print(f"PlutosAI Error: {e.code} - {e.message}")
    
    if e.code == "rate_limit_exceeded":
        print(f"Retry after: {e.details.get('retry_after')} seconds")
    elif e.code == "invalid_api_key":
        print("Check your API key")
    elif e.code == "insufficient_quota":
        print("Upgrade your plan")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Go SDK

### Installation

```bash
go get github.com/plutos-ai/go-sdk
```

### Basic Usage

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
            MaxTokens:   1000,
        },
    })
    
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Println(result.Output)
}
```

### Configuration Options

```go
client := plutos.NewClientWithConfig(plutos.Config{
    APIKey:      "your-api-key",
    Environment: "production",
    Timeout:     30 * time.Second,
    Retries:     3,
    BaseURL:     "", // Override base URL
    Headers:     map[string]string{}, // Additional headers
})
```

### Core Methods

#### ProcessData()

```go
result, err := client.ProcessData(plutos.ProcessRequest{
    Input: "Analyze this text for sentiment",
    Model: "gpt-4",
    Options: plutos.ProcessOptions{
        Temperature:   0.3,
        MaxTokens:     100,
        SystemPrompt:  "You are a sentiment analysis expert.",
    },
})

if err != nil {
    log.Fatal(err)
}

fmt.Printf("Output: %s\n", result.Output)
fmt.Printf("Tokens used: %d\n", result.Usage.TotalTokens)
```

#### BatchProcess()

```go
batchResult, err := client.BatchProcess(plutos.BatchRequest{
    Inputs: []string{
        "What is the capital of France?",
        "What is the capital of Germany?",
        "What is the capital of Italy?",
    },
    Model: "gpt-4",
    Options: plutos.ProcessOptions{
        Temperature: 0.3,
        MaxTokens:   50,
    },
})

if err != nil {
    log.Fatal(err)
}

for i, result := range batchResult.Results {
    fmt.Printf("Input %d: %s\n", i+1, result.Output)
}
```

#### StreamProcess()

```go
stream, err := client.StreamProcess(plutos.ProcessRequest{
    Input: "Write a short story about a robot.",
    Model: "gpt-4",
})

if err != nil {
    log.Fatal(err)
}

for chunk := range stream {
    if chunk.Chunk == "partial" {
        fmt.Print(chunk.Output)
    } else if chunk.Chunk == "final" {
        fmt.Printf("\nComplete! Tokens: %d\n", chunk.Usage.TotalTokens)
    }
}
```

### Error Handling

```go
result, err := client.ProcessData(plutos.ProcessRequest{
    Input: "Test input",
    Model: "gpt-4",
})

if err != nil {
    if plutosErr, ok := err.(*plutos.Error); ok {
        fmt.Printf("PlutosAI Error: %s - %s\n", plutosErr.Code, plutosErr.Message)
        
        switch plutosErr.Code {
        case "rate_limit_exceeded":
            fmt.Printf("Retry after: %v seconds\n", plutosErr.Details["retry_after"])
        case "invalid_api_key":
            fmt.Println("Check your API key")
        case "insufficient_quota":
            fmt.Println("Upgrade your plan")
        }
    } else {
        fmt.Printf("Unexpected error: %v\n", err)
    }
    return
}
```

## React SDK

### Installation

```bash
npm install @plutos-ai/react
# or
yarn add @plutos-ai/react
```

### Basic Usage

```jsx
import React from 'react';
import { usePlutosAI } from '@plutos-ai/react';

function MyComponent() {
  const { processData, isLoading, error, result } = usePlutosAI({
    apiKey: 'your-api-key',
    model: 'gpt-4'
  });

  const handleSubmit = async (input) => {
    await processData(input);
  };

  return (
    <div>
      {isLoading && <div>Processing...</div>}
      {error && <div>Error: {error.message}</div>}
      {result && <div>Result: {result.output}</div>}
    </div>
  );
}
```

### PlutosAIProvider

```jsx
import React from 'react';
import { PlutosAIProvider } from '@plutos-ai/react';

function App() {
  return (
    <PlutosAIProvider
      apiKey="your-api-key"
      environment="production"
      defaultModel="gpt-4"
    >
      <MyComponent />
    </PlutosAIProvider>
  );
}
```

### usePlutosAI Hook

```jsx
import { usePlutosAI } from '@plutos-ai/react';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const { processData, isLoading, error } = usePlutosAI({
    apiKey: 'your-api-key',
    model: 'gpt-4',
    options: {
      temperature: 0.7,
      maxTokens: 1000
    }
  });

  const sendMessage = async (text) => {
    const userMessage = { role: 'user', content: text };
    setMessages(prev => [...prev, userMessage]);

    try {
      const result = await processData(text);
      const aiMessage = { role: 'assistant', content: result.output };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div>
      {messages.map((msg, index) => (
        <div key={index} className={msg.role}>
          {msg.content}
        </div>
      ))}
      {isLoading && <div>AI is thinking...</div>}
      {error && <div>Error: {error.message}</div>}
    </div>
  );
}
```

### usePlutosAIStream Hook

```jsx
import { usePlutosAIStream } from '@plutos-ai/react';

function StreamingChat() {
  const [messages, setMessages] = useState([]);
  const { streamProcess, isStreaming } = usePlutosAIStream({
    apiKey: 'your-api-key',
    model: 'gpt-4'
  });

  const sendMessage = async (text) => {
    const userMessage = { role: 'user', content: text };
    setMessages(prev => [...prev, userMessage]);

    const aiMessage = { role: 'assistant', content: '' };
    setMessages(prev => [...prev, aiMessage]);

    try {
      for await (const chunk of streamProcess(text)) {
        if (chunk.chunk === 'partial') {
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1].content += chunk.output;
            return newMessages;
          });
        }
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div>
      {messages.map((msg, index) => (
        <div key={index} className={msg.role}>
          {msg.content}
        </div>
      ))}
      {isStreaming && <div>AI is thinking...</div>}
    </div>
  );
}
```

## Web Components

### Installation

```html
<script src="https://unpkg.com/@plutos-ai/components"></script>
```

### PlutosAIProcessor

```html
<plutos-ai-processor
  api-key="your-api-key"
  model="gpt-4"
  placeholder="Enter your text here..."
  temperature="0.7"
  max-tokens="1000"
  @result="handleResult"
  @error="handleError"
  @loading="handleLoading">
</plutos-ai-processor>

<script>
  function handleResult(event) {
    console.log('Result:', event.detail);
  }
  
  function handleError(event) {
    console.error('Error:', event.detail);
  }
  
  function handleLoading(event) {
    console.log('Loading:', event.detail);
  }
</script>
```

### PlutosAIStream

```html
<plutos-ai-stream
  api-key="your-api-key"
  model="gpt-4"
  auto-start="false"
  @chunk="handleChunk"
  @complete="handleComplete"
  @error="handleError">
</plutos-ai-stream>

<script>
  function handleChunk(event) {
    console.log('Chunk:', event.detail);
  }
  
  function handleComplete(event) {
    console.log('Complete:', event.detail);
  }
  
  function handleError(event) {
    console.error('Error:', event.detail);
  }
</script>
```

## Common Patterns

### Retry Logic

```typescript
async function processWithRetry(client: PlutosAI, input: string, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await client.processData({ input, model: 'gpt-4' });
    } catch (error) {
      if (error.code === 'rate_limit_exceeded') {
        const delay = error.details?.retryAfter * 1000 || 60000;
        await new Promise(resolve => setTimeout(resolve, delay));
      } else if (attempt === maxRetries) {
        throw error;
      } else {
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      }
    }
  }
}
```

### Caching

```typescript
class PlutosAICache {
  private cache = new Map<string, any>();
  private ttl = 3600000; // 1 hour

  async get(key: string): Promise<any | null> {
    const item = this.cache.get(key);
    if (item && Date.now() - item.timestamp < this.ttl) {
      return item.data;
    }
    return null;
  }

  set(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  async processWithCache(client: PlutosAI, input: string, model: string) {
    const cacheKey = `${model}:${Buffer.from(input).toString('base64')}`;
    
    const cached = await this.get(cacheKey);
    if (cached) {
      return cached;
    }

    const result = await client.processData({ input, model });
    this.set(cacheKey, result);
    return result;
  }
}
```

### Batch Processing with Progress

```typescript
async function processBatchWithProgress(
  client: PlutosAI,
  inputs: string[],
  model: string,
  onProgress?: (completed: number, total: number) => void
) {
  const batchSize = 10;
  const results = [];
  
  for (let i = 0; i < inputs.length; i += batchSize) {
    const batch = inputs.slice(i, i + batchSize);
    
    try {
      const batchResult = await client.batchProcess({
        inputs: batch,
        model
      });
      
      results.push(...batchResult.results);
      
      if (onProgress) {
        onProgress(Math.min(i + batchSize, inputs.length), inputs.length);
      }
    } catch (error) {
      console.error(`Batch ${i / batchSize + 1} failed:`, error);
      // Handle individual batch failure
    }
  }
  
  return results;
}
```

### Error Recovery

```typescript
class PlutosAIErrorHandler {
  private fallbackModel = 'gpt-3.5-turbo';
  
  async processWithFallback(
    client: PlutosAI,
    input: string,
    primaryModel: string
  ) {
    try {
      return await client.processData({ input, model: primaryModel });
    } catch (error) {
      if (error.code === 'invalid_model' || error.code === 'model_unavailable') {
        console.warn(`Primary model ${primaryModel} unavailable, using fallback`);
        return await client.processData({ input, model: this.fallbackModel });
      }
      throw error;
    }
  }
}
```

This comprehensive SDK documentation provides detailed examples and usage patterns for all supported programming languages and frameworks. Each SDK includes proper error handling, configuration options, and common patterns for production use.
