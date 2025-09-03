# PlutosAI Component Documentation

Complete documentation for all PlutosAI UI components, web components, and React components.

## Table of Contents

- [Web Components](#web-components)
- [React Components](#react-components)
- [Vue Components](#vue-components)
- [Angular Components](#angular-components)
- [Styling and Theming](#styling-and-theming)
- [Component Examples](#component-examples)
- [Advanced Usage](#advanced-usage)

## Web Components

PlutosAI provides a set of reusable web components that can be used in any web application.

### Installation

```html
<!-- Include the component library -->
<script src="https://unpkg.com/@plutos-ai/components"></script>

<!-- Or use ES modules -->
<script type="module">
  import '@plutos-ai/components';
</script>
```

### PlutosAIProcessor

A component for processing data with AI models.

#### Basic Usage

```html
<plutos-ai-processor
  api-key="your-api-key"
  model="gpt-4"
  placeholder="Enter your text here..."
  @result="handleResult"
  @error="handleError">
</plutos-ai-processor>
```

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `api-key` | string | - | Your PlutosAI API key |
| `model` | string | 'gpt-4' | AI model to use |
| `placeholder` | string | 'Enter text...' | Input placeholder text |
| `temperature` | number | 0.7 | Model temperature (0-1) |
| `max-tokens` | number | 1000 | Maximum tokens to generate |
| `top-p` | number | 1.0 | Top-p sampling parameter |
| `system-prompt` | string | - | System prompt for the model |
| `disabled` | boolean | false | Whether the component is disabled |
| `loading` | boolean | false | Show loading state |
| `theme` | string | 'light' | Theme: 'light' or 'dark' |

#### Events

| Event | Detail | Description |
|-------|--------|-------------|
| `result` | `{output, usage, model}` | Fired when processing completes |
| `error` | `{message, code, details}` | Fired when an error occurs |
| `loading` | `{loading}` | Fired when loading state changes |
| `input` | `{value}` | Fired when input changes |

#### Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `process()` | - | Manually trigger processing |
| `clear()` | - | Clear the input and results |
| `setInput(value)` | `string` | Set the input value programmatically |

#### Examples

**Basic Text Processing**

```html
<plutos-ai-processor
  api-key="your-api-key"
  model="gpt-4"
  placeholder="Ask me anything..."
  @result="handleResult">
</plutos-ai-processor>

<script>
  function handleResult(event) {
    console.log('Result:', event.detail.output);
    console.log('Tokens used:', event.detail.usage.totalTokens);
  }
</script>
```

**Custom Configuration**

```html
<plutos-ai-processor
  api-key="your-api-key"
  model="gpt-4"
  temperature="0.3"
  max-tokens="500"
  system-prompt="You are a helpful assistant specialized in coding."
  placeholder="Ask me about programming..."
  theme="dark"
  @result="handleResult"
  @error="handleError">
</plutos-ai-processor>

<script>
  function handleResult(event) {
    const result = event.detail;
    document.getElementById('output').textContent = result.output;
  }
  
  function handleError(event) {
    console.error('Error:', event.detail.message);
    alert('Processing failed: ' + event.detail.message);
  }
</script>
```

**Programmatic Control**

```html
<plutos-ai-processor
  id="processor"
  api-key="your-api-key"
  model="gpt-4"
  @result="handleResult">
</plutos-ai-processor>

<button onclick="processText()">Process</button>
<button onclick="clearProcessor()">Clear</button>

<script>
  const processor = document.getElementById('processor');
  
  function processText() {
    processor.setInput('What is the capital of France?');
    processor.process();
  }
  
  function clearProcessor() {
    processor.clear();
  }
  
  function handleResult(event) {
    console.log('Result:', event.detail.output);
  }
</script>
```

### PlutosAIStream

A component for real-time streaming AI responses.

#### Basic Usage

```html
<plutos-ai-stream
  api-key="your-api-key"
  model="gpt-4"
  @chunk="handleChunk"
  @complete="handleComplete">
</plutos-ai-stream>
```

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `api-key` | string | - | Your PlutosAI API key |
| `model` | string | 'gpt-4' | AI model to use |
| `auto-start` | boolean | false | Start streaming automatically |
| `temperature` | number | 0.7 | Model temperature (0-1) |
| `max-tokens` | number | 1000 | Maximum tokens to generate |
| `system-prompt` | string | - | System prompt for the model |
| `disabled` | boolean | false | Whether the component is disabled |
| `theme` | string | 'light' | Theme: 'light' or 'dark' |

#### Events

| Event | Detail | Description |
|-------|--------|-------------|
| `chunk` | `{chunk, output, usage}` | Fired for each stream chunk |
| `complete` | `{output, usage, model}` | Fired when streaming completes |
| `error` | `{message, code, details}` | Fired when an error occurs |
| `start` | - | Fired when streaming starts |
| `stop` | - | Fired when streaming stops |

#### Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `start(input)` | `string` | Start streaming with input |
| `stop()` | - | Stop streaming |
| `clear()` | - | Clear the output |

#### Examples

**Basic Streaming**

```html
<plutos-ai-stream
  api-key="your-api-key"
  model="gpt-4"
  @chunk="handleChunk"
  @complete="handleComplete">
</plutos-ai-stream>

<button onclick="startStream()">Start Stream</button>

<script>
  const stream = document.querySelector('plutos-ai-stream');
  
  function startStream() {
    stream.start('Tell me a story about a robot learning to paint.');
  }
  
  function handleChunk(event) {
    const chunk = event.detail;
    if (chunk.chunk === 'partial') {
      document.getElementById('output').textContent += chunk.output;
    }
  }
  
  function handleComplete(event) {
    console.log('Streaming complete:', event.detail.output);
  }
</script>
```

**Auto-start Streaming**

```html
<plutos-ai-stream
  api-key="your-api-key"
  model="gpt-4"
  auto-start="true"
  system-prompt="You are a creative storyteller."
  @chunk="handleChunk"
  @complete="handleComplete">
</plutos-ai-stream>

<script>
  function handleChunk(event) {
    const chunk = event.detail;
    if (chunk.chunk === 'partial') {
      // Append to a container
      const container = document.getElementById('stream-output');
      container.textContent += chunk.output;
      container.scrollTop = container.scrollHeight;
    }
  }
  
  function handleComplete(event) {
    console.log('Final result:', event.detail.output);
  }
</script>
```

### PlutosAIBatch

A component for batch processing multiple inputs.

#### Basic Usage

```html
<plutos-ai-batch
  api-key="your-api-key"
  model="gpt-4"
  @results="handleResults"
  @progress="handleProgress">
</plutos-ai-batch>
```

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `api-key` | string | - | Your PlutosAI API key |
| `model` | string | 'gpt-4' | AI model to use |
| `batch-size` | number | 10 | Number of inputs to process per batch |
| `temperature` | number | 0.7 | Model temperature (0-1) |
| `max-tokens` | number | 1000 | Maximum tokens to generate |
| `system-prompt` | string | - | System prompt for the model |
| `disabled` | boolean | false | Whether the component is disabled |
| `theme` | string | 'light' | Theme: 'light' or 'dark' |

#### Events

| Event | Detail | Description |
|-------|--------|-------------|
| `results` | `{results, totalUsage}` | Fired when all processing completes |
| `progress` | `{completed, total, current}` | Fired for progress updates |
| `error` | `{message, code, details}` | Fired when an error occurs |

#### Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `process(inputs)` | `string[]` | Process an array of inputs |
| `stop()` | - | Stop batch processing |
| `clear()` | - | Clear results |

#### Examples

**Batch Processing**

```html
<plutos-ai-batch
  api-key="your-api-key"
  model="gpt-4"
  batch-size="5"
  @results="handleResults"
  @progress="handleProgress">
</plutos-ai-batch>

<button onclick="processBatch()">Process Batch</button>
<div id="progress"></div>

<script>
  const batch = document.querySelector('plutos-ai-batch');
  
  function processBatch() {
    const inputs = [
      'What is the capital of France?',
      'What is the capital of Germany?',
      'What is the capital of Italy?',
      'What is the capital of Spain?',
      'What is the capital of Portugal?'
    ];
    
    batch.process(inputs);
  }
  
  function handleProgress(event) {
    const progress = event.detail;
    document.getElementById('progress').textContent = 
      `Processing: ${progress.completed}/${progress.total}`;
  }
  
  function handleResults(event) {
    const results = event.detail;
    console.log('All results:', results.results);
    console.log('Total tokens:', results.totalUsage.totalTokens);
  }
</script>
```

### PlutosAIChat

A complete chat interface component.

#### Basic Usage

```html
<plutos-ai-chat
  api-key="your-api-key"
  model="gpt-4"
  @message="handleMessage">
</plutos-ai-chat>
```

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `api-key` | string | - | Your PlutosAI API key |
| `model` | string | 'gpt-4' | AI model to use |
| `placeholder` | string | 'Type your message...' | Input placeholder |
| `temperature` | number | 0.7 | Model temperature (0-1) |
| `max-tokens` | number | 1000 | Maximum tokens to generate |
| `system-prompt` | string | - | System prompt for the model |
| `streaming` | boolean | false | Enable streaming responses |
| `theme` | string | 'light' | Theme: 'light' or 'dark' |
| `height` | string | '400px' | Chat container height |

#### Events

| Event | Detail | Description |
|-------|--------|-------------|
| `message` | `{role, content, timestamp}` | Fired when a message is sent/received |
| `error` | `{message, code, details}` | Fired when an error occurs |

#### Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `sendMessage(content)` | `string` | Send a message programmatically |
| `clear()` | - | Clear chat history |
| `export()` | - | Export chat history as JSON |

#### Examples

**Basic Chat**

```html
<plutos-ai-chat
  api-key="your-api-key"
  model="gpt-4"
  placeholder="Ask me anything..."
  @message="handleMessage">
</plutos-ai-chat>

<script>
  function handleMessage(event) {
    const message = event.detail;
    console.log(`${message.role}: ${message.content}`);
  }
</script>
```

**Streaming Chat**

```html
<plutos-ai-chat
  api-key="your-api-key"
  model="gpt-4"
  streaming="true"
  system-prompt="You are a helpful AI assistant."
  theme="dark"
  height="600px"
  @message="handleMessage">
</plutos-ai-chat>

<script>
  function handleMessage(event) {
    const message = event.detail;
    if (message.role === 'assistant') {
      // Handle AI response
      console.log('AI:', message.content);
    }
  }
</script>
```

## React Components

### Installation

```bash
npm install @plutos-ai/react
# or
yarn add @plutos-ai/react
```

### PlutosAIProvider

A React context provider for PlutosAI configuration.

```jsx
import React from 'react';
import { PlutosAIProvider } from '@plutos-ai/react';

function App() {
  return (
    <PlutosAIProvider
      apiKey="your-api-key"
      environment="production"
      defaultModel="gpt-4"
      defaultOptions={{
        temperature: 0.7,
        maxTokens: 1000
      }}
    >
      <MyComponent />
    </PlutosAIProvider>
  );
}
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `apiKey` | string | - | Your PlutosAI API key |
| `environment` | string | 'production' | Environment: 'production', 'staging', 'development' |
| `defaultModel` | string | 'gpt-4' | Default model for all requests |
| `defaultOptions` | object | {} | Default options for all requests |
| `children` | ReactNode | - | Child components |

### usePlutosAI Hook

A React hook for integrating PlutosAI functionality.

```jsx
import { usePlutosAI } from '@plutos-ai/react';

function MyComponent() {
  const { processData, isLoading, error, result } = usePlutosAI({
    model: 'gpt-4',
    options: {
      temperature: 0.7,
      maxTokens: 1000
    }
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

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | - | AI model to use |
| `options` | object | {} | Processing options |

#### Return Value

| Property | Type | Description |
|----------|------|-------------|
| `processData` | function | Function to process data |
| `isLoading` | boolean | Loading state |
| `error` | Error | Error state |
| `result` | object | Processing result |
| `clear` | function | Clear result and error |

### usePlutosAIStream Hook

A React hook for streaming AI responses.

```jsx
import { usePlutosAIStream } from '@plutos-ai/react';

function StreamingComponent() {
  const { streamProcess, isStreaming, error } = usePlutosAIStream({
    model: 'gpt-4'
  });

  const handleStream = async (input) => {
    for await (const chunk of streamProcess(input)) {
      if (chunk.chunk === 'partial') {
        console.log(chunk.output);
      }
    }
  };

  return (
    <div>
      {isStreaming && <div>Streaming...</div>}
      {error && <div>Error: {error.message}</div>}
    </div>
  );
}
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | - | AI model to use |
| `options` | object | {} | Processing options |

#### Return Value

| Property | Type | Description |
|----------|------|-------------|
| `streamProcess` | function | Function to start streaming |
| `isStreaming` | boolean | Streaming state |
| `error` | Error | Error state |

### PlutosAIProcessor Component

A React component for processing data with AI models.

```jsx
import { PlutosAIProcessor } from '@plutos-ai/react';

function MyComponent() {
  const handleResult = (result) => {
    console.log('Result:', result.output);
  };

  const handleError = (error) => {
    console.error('Error:', error.message);
  };

  return (
    <PlutosAIProcessor
      apiKey="your-api-key"
      model="gpt-4"
      placeholder="Enter your text here..."
      temperature={0.7}
      maxTokens={1000}
      onResult={handleResult}
      onError={handleError}
    />
  );
}
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `apiKey` | string | - | Your PlutosAI API key |
| `model` | string | 'gpt-4' | AI model to use |
| `placeholder` | string | 'Enter text...' | Input placeholder |
| `temperature` | number | 0.7 | Model temperature |
| `maxTokens` | number | 1000 | Maximum tokens |
| `systemPrompt` | string | - | System prompt |
| `disabled` | boolean | false | Disabled state |
| `theme` | string | 'light' | Theme |
| `onResult` | function | - | Result callback |
| `onError` | function | - | Error callback |
| `onLoading` | function | - | Loading callback |

### PlutosAIChat Component

A complete React chat component.

```jsx
import { PlutosAIChat } from '@plutos-ai/react';

function ChatApp() {
  const handleMessage = (message) => {
    console.log(`${message.role}: ${message.content}`);
  };

  return (
    <PlutosAIChat
      apiKey="your-api-key"
      model="gpt-4"
      placeholder="Type your message..."
      streaming={true}
      theme="dark"
      height="600px"
      onMessage={handleMessage}
    />
  );
}
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `apiKey` | string | - | Your PlutosAI API key |
| `model` | string | 'gpt-4' | AI model to use |
| `placeholder` | string | 'Type your message...' | Input placeholder |
| `streaming` | boolean | false | Enable streaming |
| `theme` | string | 'light' | Theme |
| `height` | string | '400px' | Container height |
| `onMessage` | function | - | Message callback |
| `onError` | function | - | Error callback |

## Vue Components

### Installation

```bash
npm install @plutos-ai/vue
# or
yarn add @plutos-ai/vue
```

### Vue Plugin Setup

```javascript
import { createApp } from 'vue';
import PlutosAI from '@plutos-ai/vue';
import App from './App.vue';

const app = createApp(App);
app.use(PlutosAI, {
  apiKey: 'your-api-key',
  environment: 'production'
});
app.mount('#app');
```

### PlutosAIProcessor Component

```vue
<template>
  <PlutosAIProcessor
    :api-key="apiKey"
    model="gpt-4"
    placeholder="Enter your text here..."
    :temperature="0.7"
    :max-tokens="1000"
    @result="handleResult"
    @error="handleError"
  />
</template>

<script>
import { PlutosAIProcessor } from '@plutos-ai/vue';

export default {
  components: {
    PlutosAIProcessor
  },
  data() {
    return {
      apiKey: 'your-api-key'
    };
  },
  methods: {
    handleResult(result) {
      console.log('Result:', result.output);
    },
    handleError(error) {
      console.error('Error:', error.message);
    }
  }
};
</script>
```

### usePlutosAI Composable

```vue
<template>
  <div>
    <textarea v-model="input" placeholder="Enter text..."></textarea>
    <button @click="process" :disabled="isLoading">
      {{ isLoading ? 'Processing...' : 'Process' }}
    </button>
    <div v-if="error" class="error">{{ error.message }}</div>
    <div v-if="result" class="result">{{ result.output }}</div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { usePlutosAI } from '@plutos-ai/vue';

export default {
  setup() {
    const input = ref('');
    const { processData, isLoading, error, result } = usePlutosAI({
      model: 'gpt-4'
    });

    const process = async () => {
      await processData(input.value);
    };

    return {
      input,
      process,
      isLoading,
      error,
      result
    };
  }
};
</script>
```

## Angular Components

### Installation

```bash
npm install @plutos-ai/angular
# or
yarn add @plutos-ai/angular
```

### Module Setup

```typescript
import { NgModule } from '@angular/core';
import { PlutosAIModule } from '@plutos-ai/angular';

@NgModule({
  imports: [
    PlutosAIModule.forRoot({
      apiKey: 'your-api-key',
      environment: 'production'
    })
  ]
})
export class AppModule { }
```

### PlutosAIProcessor Component

```typescript
import { Component } from '@angular/core';

@Component({
  selector: 'app-processor',
  template: `
    <plutos-ai-processor
      [apiKey]="apiKey"
      model="gpt-4"
      placeholder="Enter your text here..."
      [temperature]="0.7"
      [maxTokens]="1000"
      (result)="handleResult($event)"
      (error)="handleError($event)">
    </plutos-ai-processor>
  `
})
export class ProcessorComponent {
  apiKey = 'your-api-key';

  handleResult(result: any) {
    console.log('Result:', result.output);
  }

  handleError(error: any) {
    console.error('Error:', error.message);
  }
}
```

### PlutosAI Service

```typescript
import { Injectable } from '@angular/core';
import { PlutosAIService } from '@plutos-ai/angular';

@Injectable({
  providedIn: 'root'
})
export class MyService {
  constructor(private plutosAI: PlutosAIService) {}

  async processText(input: string) {
    try {
      const result = await this.plutosAI.processData({
        input,
        model: 'gpt-4',
        options: {
          temperature: 0.7,
          maxTokens: 1000
        }
      });
      
      return result.output;
    } catch (error) {
      console.error('Processing failed:', error);
      throw error;
    }
  }
}
```

## Styling and Theming

### CSS Custom Properties

All components support CSS custom properties for theming:

```css
/* Light theme (default) */
:root {
  --plutos-primary-color: #007bff;
  --plutos-secondary-color: #6c757d;
  --plutos-success-color: #28a745;
  --plutos-danger-color: #dc3545;
  --plutos-warning-color: #ffc107;
  --plutos-info-color: #17a2b8;
  
  --plutos-bg-color: #ffffff;
  --plutos-text-color: #212529;
  --plutos-border-color: #dee2e6;
  --plutos-input-bg: #ffffff;
  --plutos-input-border: #ced4da;
  
  --plutos-border-radius: 0.375rem;
  --plutos-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --plutos-font-size: 1rem;
  --plutos-line-height: 1.5;
}

/* Dark theme */
[data-theme="dark"] {
  --plutos-bg-color: #212529;
  --plutos-text-color: #f8f9fa;
  --plutos-border-color: #495057;
  --plutos-input-bg: #343a40;
  --plutos-input-border: #6c757d;
}
```

### Custom Styling

```css
/* Custom styles for PlutosAI components */
plutos-ai-processor {
  --plutos-primary-color: #your-brand-color;
  --plutos-border-radius: 8px;
  --plutos-font-family: 'Your Font', sans-serif;
}

/* Custom component styles */
.my-custom-processor {
  border: 2px solid #your-color;
  border-radius: 12px;
  padding: 20px;
  background: linear-gradient(135deg, #your-gradient);
}

/* Responsive design */
@media (max-width: 768px) {
  plutos-ai-chat {
    --plutos-font-size: 0.875rem;
    height: 300px !important;
  }
}
```

### Theme Switching

```javascript
// Switch themes programmatically
function switchTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  
  // Update component themes
  const components = document.querySelectorAll('[data-theme]');
  components.forEach(component => {
    component.setAttribute('data-theme', theme);
  });
}

// Example usage
switchTheme('dark');
```

## Component Examples

### Advanced Chat Interface

```jsx
import React, { useState, useRef, useEffect } from 'react';
import { usePlutosAI } from '@plutos-ai/react';

function AdvancedChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [model, setModel] = useState('gpt-4');
  const [temperature, setTemperature] = useState(0.7);
  const messagesEndRef = useRef(null);
  
  const { processData, isLoading, error } = usePlutosAI({
    apiKey: process.env.REACT_APP_PLUTOS_API_KEY,
    model,
    options: {
      temperature,
      maxTokens: 1000
    }
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { 
      role: 'user', 
      content: input, 
      timestamp: new Date(),
      id: Date.now()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const result = await processData(input);
      const aiMessage = { 
        role: 'assistant', 
        content: result.output, 
        timestamp: new Date(),
        id: Date.now() + 1,
        usage: result.usage
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const exportChat = () => {
    const chatData = {
      messages,
      settings: { model, temperature },
      exportDate: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(chatData, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-export-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const clearChat = () => {
    setMessages([]);
  };

  return (
    <div className="advanced-chat">
      <div className="chat-header">
        <h2>AI Chat Assistant</h2>
        <div className="controls">
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
          </select>
          <label>
            Temperature:
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
            />
            {temperature}
          </label>
          <button onClick={exportChat}>Export</button>
          <button onClick={clearChat}>Clear</button>
        </div>
      </div>
      
      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="message-header">
              <span className="role">{message.role}</span>
              <span className="timestamp">
                {message.timestamp.toLocaleTimeString()}
              </span>
            </div>
            <div className="content">{message.content}</div>
            {message.usage && (
              <div className="usage">
                Tokens: {message.usage.totalTokens}
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="message assistant">
            <div className="content">Thinking...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      {error && (
        <div className="error">
          Error: {error.message}
        </div>
      )}
      
      <div className="input-container">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <button onClick={sendMessage} disabled={isLoading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

export default AdvancedChat;
```

### Multi-Model Processor

```jsx
import React, { useState } from 'react';
import { usePlutosAI } from '@plutos-ai/react';

function MultiModelProcessor() {
  const [input, setInput] = useState('');
  const [results, setResults] = useState({});
  const [processing, setProcessing] = useState({});
  
  const models = [
    { id: 'gpt-4', name: 'GPT-4', description: 'Most capable model' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'Fast and efficient' }
  ];

  const processWithModel = async (modelId) => {
    const { processData } = usePlutosAI({
      apiKey: process.env.REACT_APP_PLUTOS_API_KEY,
      model: modelId
    });

    setProcessing(prev => ({ ...prev, [modelId]: true }));
    
    try {
      const result = await processData(input);
      setResults(prev => ({ ...prev, [modelId]: result }));
    } catch (error) {
      setResults(prev => ({ 
        ...prev, 
        [modelId]: { error: error.message } 
      }));
    } finally {
      setProcessing(prev => ({ ...prev, [modelId]: false }));
    }
  };

  const processAll = async () => {
    for (const model of models) {
      await processWithModel(model.id);
    }
  };

  return (
    <div className="multi-model-processor">
      <div className="input-section">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter text to process with multiple models..."
          rows={4}
        />
        <div className="buttons">
          <button onClick={processAll} disabled={!input.trim()}>
            Process with All Models
          </button>
        </div>
      </div>
      
      <div className="results-section">
        {models.map(model => (
          <div key={model.id} className="model-result">
            <div className="model-header">
              <h3>{model.name}</h3>
              <p>{model.description}</p>
              <button
                onClick={() => processWithModel(model.id)}
                disabled={processing[model.id] || !input.trim()}
              >
                {processing[model.id] ? 'Processing...' : 'Process'}
              </button>
            </div>
            
            <div className="result-content">
              {results[model.id] && (
                results[model.id].error ? (
                  <div className="error">{results[model.id].error}</div>
                ) : (
                  <div>
                    <div className="output">{results[model.id].output}</div>
                    <div className="usage">
                      Tokens: {results[model.id].usage.totalTokens}
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default MultiModelProcessor;
```

This comprehensive component documentation provides detailed information about all PlutosAI components, their properties, events, methods, and usage examples across different frameworks.
