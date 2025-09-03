# PlutosAI Examples and Tutorials

Comprehensive examples and tutorials for using PlutosAI in real-world scenarios.

## Table of Contents

- [Getting Started](#getting-started)
- [Text Processing Examples](#text-processing-examples)
- [Chat Applications](#chat-applications)
- [Content Generation](#content-generation)
- [Data Analysis](#data-analysis)
- [Integration Examples](#integration-examples)
- [Advanced Patterns](#advanced-patterns)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Quick Start Tutorial

This tutorial will guide you through creating your first PlutosAI application.

#### Step 1: Setup

```bash
# Create a new project
mkdir my-plutos-app
cd my-plutos-app

# Initialize package.json
npm init -y

# Install PlutosAI SDK
npm install @plutos-ai/sdk
```

#### Step 2: Basic Implementation

Create `index.js`:

```javascript
import { PlutosAI } from '@plutos-ai/sdk';

const client = new PlutosAI({
  apiKey: process.env.PLUTOS_API_KEY,
  environment: 'production'
});

async function main() {
  try {
    const result = await client.processData({
      input: 'What is the capital of France?',
      model: 'gpt-4',
      options: {
        temperature: 0.7,
        maxTokens: 100
      }
    });
    
    console.log('Answer:', result.output);
    console.log('Tokens used:', result.usage.totalTokens);
  } catch (error) {
    console.error('Error:', error.message);
  }
}

main();
```

#### Step 3: Environment Setup

Create `.env`:

```bash
PLUTOS_API_KEY=your-api-key-here
```

#### Step 4: Run

```bash
node index.js
```

## Text Processing Examples

### Sentiment Analysis

Analyze the sentiment of text data.

```javascript
import { PlutosAI } from '@plutos-ai/sdk';

const client = new PlutosAI({ apiKey: process.env.PLUTOS_API_KEY });

async function analyzeSentiment(text) {
  const result = await client.processData({
    input: text,
    model: 'gpt-4',
    options: {
      systemPrompt: `Analyze the sentiment of the following text. 
      Respond with only: positive, negative, or neutral. 
      Provide a brief explanation.`,
      temperature: 0.1,
      maxTokens: 100
    }
  });
  
  return result.output;
}

// Example usage
const texts = [
  'I love this product! It works perfectly.',
  'This is the worst experience I have ever had.',
  'The service was okay, nothing special.'
];

for (const text of texts) {
  const sentiment = await analyzeSentiment(text);
  console.log(`Text: "${text}"`);
  console.log(`Sentiment: ${sentiment}\n`);
}
```

### Text Summarization

Create concise summaries of long text.

```javascript
async function summarizeText(text, maxLength = 150) {
  const result = await client.processData({
    input: text,
    model: 'gpt-4',
    options: {
      systemPrompt: `Summarize the following text in ${maxLength} characters or less. 
      Focus on the main points and key information.`,
      temperature: 0.3,
      maxTokens: 200
    }
  });
  
  return result.output;
}

// Example usage
const longText = `
  Artificial Intelligence (AI) has become one of the most transformative technologies 
  of the 21st century. From virtual assistants like Siri and Alexa to autonomous 
  vehicles and medical diagnosis systems, AI is reshaping how we live and work. 
  Machine learning algorithms can now process vast amounts of data to identify 
  patterns and make predictions with remarkable accuracy. However, this rapid 
  advancement also raises important questions about privacy, job displacement, 
  and the ethical implications of AI decision-making. As we continue to develop 
  more sophisticated AI systems, it's crucial to ensure they are designed and 
  deployed responsibly.
`;

const summary = await summarizeText(longText);
console.log('Summary:', summary);
```

### Language Translation

Translate text between different languages.

```javascript
async function translateText(text, targetLanguage) {
  const result = await client.processData({
    input: text,
    model: 'gpt-4',
    options: {
      systemPrompt: `Translate the following text to ${targetLanguage}. 
      Maintain the original tone and style.`,
      temperature: 0.3,
      maxTokens: 500
    }
  });
  
  return result.output;
}

// Example usage
const englishText = 'Hello, how are you today?';
const spanishTranslation = await translateText(englishText, 'Spanish');
const frenchTranslation = await translateText(englishText, 'French');

console.log('English:', englishText);
console.log('Spanish:', spanishTranslation);
console.log('French:', frenchTranslation);
```

### Text Classification

Classify text into different categories.

```javascript
async function classifyText(text, categories) {
  const result = await client.processData({
    input: text,
    model: 'gpt-4',
    options: {
      systemPrompt: `Classify the following text into one of these categories: ${categories.join(', ')}. 
      Respond with only the category name.`,
      temperature: 0.1,
      maxTokens: 50
    }
  });
  
  return result.output.trim();
}

// Example usage
const categories = ['Technology', 'Sports', 'Politics', 'Entertainment', 'Science'];
const texts = [
  'The new iPhone features advanced AI capabilities.',
  'The team won the championship with a last-minute goal.',
  'Scientists discover new species in the Amazon rainforest.'
];

for (const text of texts) {
  const category = await classifyText(text, categories);
  console.log(`Text: "${text}"`);
  console.log(`Category: ${category}\n`);
}
```

## Chat Applications

### Simple Chat Bot

Create a basic conversational AI.

```javascript
import { PlutosAI } from '@plutos-ai/sdk';
import readline from 'readline';

const client = new PlutosAI({ apiKey: process.env.PLUTOS_API_KEY });

class ChatBot {
  constructor() {
    this.conversationHistory = [];
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
  }

  async chat(userInput) {
    // Add user message to history
    this.conversationHistory.push({ role: 'user', content: userInput });
    
    // Create context from conversation history
    const context = this.conversationHistory
      .map(msg => `${msg.role}: ${msg.content}`)
      .join('\n');
    
    const result = await client.processData({
      input: context,
      model: 'gpt-4',
      options: {
        systemPrompt: 'You are a helpful and friendly AI assistant. Respond naturally to the conversation.',
        temperature: 0.7,
        maxTokens: 200
      }
    });
    
    // Add AI response to history
    this.conversationHistory.push({ role: 'assistant', content: result.output });
    
    return result.output;
  }

  async start() {
    console.log('ChatBot: Hello! How can I help you today? (Type "quit" to exit)');
    
    const askQuestion = () => {
      this.rl.question('You: ', async (input) => {
        if (input.toLowerCase() === 'quit') {
          console.log('ChatBot: Goodbye!');
          this.rl.close();
          return;
        }
        
        try {
          const response = await this.chat(input);
          console.log('ChatBot:', response);
        } catch (error) {
          console.error('Error:', error.message);
        }
        
        askQuestion();
      });
    };
    
    askQuestion();
  }
}

// Start the chat bot
const bot = new ChatBot();
bot.start();
```

### Streaming Chat Interface

Create a real-time streaming chat experience.

```javascript
async function streamingChat(userInput) {
  const stream = await client.streamProcess({
    input: userInput,
    model: 'gpt-4',
    options: {
      systemPrompt: 'You are a helpful AI assistant. Respond conversationally.',
      temperature: 0.7,
      maxTokens: 300
    }
  });
  
  let fullResponse = '';
  
  for await (const chunk of stream) {
    if (chunk.chunk === 'partial') {
      process.stdout.write(chunk.output);
      fullResponse += chunk.output;
    } else if (chunk.chunk === 'final') {
      console.log('\n[Complete]');
      return fullResponse;
    }
  }
}

// Example usage
const userMessage = 'Tell me a short story about a robot learning to paint.';
console.log('User:', userMessage);
console.log('AI: ');
await streamingChat(userMessage);
```

### React Chat Component

Create a React component for chat functionality.

```jsx
import React, { useState, useRef, useEffect } from 'react';
import { usePlutosAI } from '@plutos-ai/react';

function ChatComponent() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  
  const { processData, isLoading, error } = usePlutosAI({
    apiKey: process.env.REACT_APP_PLUTOS_API_KEY,
    model: 'gpt-4'
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const result = await processData(input);
      const aiMessage = { 
        role: 'assistant', 
        content: result.output, 
        timestamp: new Date() 
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="content">{message.content}</div>
            <div className="timestamp">
              {message.timestamp.toLocaleTimeString()}
            </div>
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
          onKeyPress={handleKeyPress}
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

export default ChatComponent;
```

## Content Generation

### Blog Post Generator

Generate blog posts from topics and outlines.

```javascript
async function generateBlogPost(topic, outline) {
  const prompt = `
    Topic: ${topic}
    Outline: ${outline}
    
    Write a comprehensive blog post based on the topic and outline above. 
    The post should be engaging, informative, and well-structured. 
    Include an introduction, body sections following the outline, and a conclusion.
  `;
  
  const result = await client.processData({
    input: prompt,
    model: 'gpt-4',
    options: {
      temperature: 0.7,
      maxTokens: 2000
    }
  });
  
  return result.output;
}

// Example usage
const topic = 'The Future of Artificial Intelligence in Healthcare';
const outline = `
  1. Introduction to AI in healthcare
  2. Current applications of AI in medical diagnosis
  3. AI-powered drug discovery
  4. Ethical considerations and challenges
  5. Future prospects and conclusion
`;

const blogPost = await generateBlogPost(topic, outline);
console.log(blogPost);
```

### Social Media Content Creator

Generate social media posts for different platforms.

```javascript
async function generateSocialMediaPost(content, platform, tone = 'professional') {
  const platformPrompts = {
    'twitter': 'Create a tweet (max 280 characters)',
    'linkedin': 'Create a professional LinkedIn post',
    'instagram': 'Create an Instagram caption with relevant hashtags',
    'facebook': 'Create an engaging Facebook post'
  };
  
  const prompt = `
    ${platformPrompts[platform]}
    
    Content: ${content}
    Tone: ${tone}
    
    Make it engaging and appropriate for the platform.
  `;
  
  const result = await client.processData({
    input: prompt,
    model: 'gpt-4',
    options: {
      temperature: 0.8,
      maxTokens: 300
    }
  });
  
  return result.output;
}

// Example usage
const content = 'New AI-powered features in our product';
const platforms = ['twitter', 'linkedin', 'instagram'];

for (const platform of platforms) {
  const post = await generateSocialMediaPost(content, platform);
  console.log(`${platform.toUpperCase()}:`);
  console.log(post);
  console.log('---');
}
```

### Email Template Generator

Generate personalized email templates.

```javascript
async function generateEmailTemplate(type, context) {
  const templates = {
    'welcome': 'Welcome email for new customers',
    'follow-up': 'Follow-up email after a meeting',
    'promotional': 'Promotional email for a new product',
    'support': 'Customer support response',
    'newsletter': 'Monthly newsletter template'
  };
  
  const prompt = `
    Create a ${templates[type]} email template.
    
    Context: ${context}
    
    Make it professional, engaging, and personalized. Include a subject line and body.
  `;
  
  const result = await client.processData({
    input: prompt,
    model: 'gpt-4',
    options: {
      temperature: 0.6,
      maxTokens: 500
    }
  });
  
  return result.output;
}

// Example usage
const emailType = 'welcome';
const context = 'New customer signed up for our AI-powered analytics platform';
const emailTemplate = await generateEmailTemplate(emailType, context);
console.log(emailTemplate);
```

## Data Analysis

### CSV Data Analyzer

Analyze CSV data and generate insights.

```javascript
import fs from 'fs';
import csv from 'csv-parser';

async function analyzeCSVData(filePath) {
  const data = [];
  
  return new Promise((resolve, reject) => {
    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', (row) => data.push(row))
      .on('end', async () => {
        try {
          const analysis = await client.processData({
            input: `Analyze this CSV data and provide insights:
            
            Data: ${JSON.stringify(data, null, 2)}
            
            Please provide:
            1. Summary of the data
            2. Key trends or patterns
            3. Recommendations based on the data
            4. Any anomalies or outliers`,
            model: 'gpt-4',
            options: {
              temperature: 0.3,
              maxTokens: 1000
            }
          });
          
          resolve(analysis.output);
        } catch (error) {
          reject(error);
        }
      });
  });
}

// Example usage
const analysis = await analyzeCSVData('sales_data.csv');
console.log('Data Analysis:');
console.log(analysis);
```

### Survey Response Analyzer

Analyze survey responses and extract insights.

```javascript
async function analyzeSurveyResponses(responses) {
  const prompt = `
    Analyze these survey responses and provide insights:
    
    Responses: ${JSON.stringify(responses, null, 2)}
    
    Please provide:
    1. Overall sentiment analysis
    2. Common themes and patterns
    3. Key insights and recommendations
    4. Areas for improvement
  `;
  
  const result = await client.processData({
    input: prompt,
    model: 'gpt-4',
    options: {
      temperature: 0.3,
      maxTokens: 800
    }
  });
  
  return result.output;
}

// Example usage
const surveyResponses = [
  'The product is great but could be faster',
  'Excellent customer service and easy to use',
  'Too expensive for what it offers',
  'Love the features but the UI needs work',
  'Perfect for my needs, highly recommend'
];

const analysis = await analyzeSurveyResponses(surveyResponses);
console.log('Survey Analysis:');
console.log(analysis);
```

## Integration Examples

### Express.js API Server

Create a REST API server using Express.js.

```javascript
import express from 'express';
import { PlutosAI } from '@plutos-ai/sdk';
import rateLimit from 'express-rate-limit';

const app = express();
const client = new PlutosAI({ apiKey: process.env.PLUTOS_API_KEY });

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});

app.use(express.json());
app.use(limiter);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Process text endpoint
app.post('/process', async (req, res) => {
  try {
    const { input, model = 'gpt-4', options = {} } = req.body;
    
    if (!input) {
      return res.status(400).json({ error: 'Input is required' });
    }
    
    const result = await client.processData({
      input,
      model,
      options
    });
    
    res.json(result);
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ 
      error: 'Processing failed', 
      message: error.message 
    });
  }
});

// Batch process endpoint
app.post('/batch', async (req, res) => {
  try {
    const { inputs, model = 'gpt-4', options = {} } = req.body;
    
    if (!inputs || !Array.isArray(inputs)) {
      return res.status(400).json({ error: 'Inputs array is required' });
    }
    
    const result = await client.batchProcess({
      inputs,
      model,
      options
    });
    
    res.json(result);
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ 
      error: 'Batch processing failed', 
      message: error.message 
    });
  }
});

// Stream endpoint
app.post('/stream', async (req, res) => {
  try {
    const { input, model = 'gpt-4', options = {} } = req.body;
    
    if (!input) {
      return res.status(400).json({ error: 'Input is required' });
    }
    
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    
    const stream = await client.streamProcess({
      input,
      model,
      options
    });
    
    for await (const chunk of stream) {
      res.write(`data: ${JSON.stringify(chunk)}\n\n`);
    }
    
    res.end();
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ 
      error: 'Streaming failed', 
      message: error.message 
    });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

### Next.js Integration

Create a Next.js API route for PlutosAI integration.

```javascript
// pages/api/process.js
import { PlutosAI } from '@plutos-ai/sdk';

const client = new PlutosAI({ apiKey: process.env.PLUTOS_API_KEY });

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { input, model = 'gpt-4', options = {} } = req.body;
    
    if (!input) {
      return res.status(400).json({ error: 'Input is required' });
    }
    
    const result = await client.processData({
      input,
      model,
      options
    });
    
    res.status(200).json(result);
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ 
      error: 'Processing failed', 
      message: error.message 
    });
  }
}
```

```jsx
// pages/index.js
import { useState } from 'react';

export default function Home() {
  const [input, setInput] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input,
          model: 'gpt-4',
          options: {
            temperature: 0.7,
            maxTokens: 500
          }
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setResult(data.output);
      } else {
        setResult(`Error: ${data.message}`);
      }
    } catch (error) {
      setResult(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>PlutosAI Integration</h1>
      
      <form onSubmit={handleSubmit}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter your text here..."
          rows={4}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          {loading ? 'Processing...' : 'Process'}
        </button>
      </form>
      
      {result && (
        <div className="result">
          <h3>Result:</h3>
          <p>{result}</p>
        </div>
      )}
    </div>
  );
}
```

## Advanced Patterns

### Caching with Redis

Implement caching to improve performance and reduce costs.

```javascript
import Redis from 'ioredis';
import crypto from 'crypto';

const redis = new Redis(process.env.REDIS_URL);

class PlutosAICache {
  constructor(client, ttl = 3600) {
    this.client = client;
    this.ttl = ttl;
  }

  generateKey(input, model, options) {
    const data = JSON.stringify({ input, model, options });
    return `plutos:${crypto.createHash('md5').update(data).digest('hex')}`;
  }

  async get(key) {
    try {
      const cached = await redis.get(key);
      return cached ? JSON.parse(cached) : null;
    } catch (error) {
      console.error('Cache get error:', error);
      return null;
    }
  }

  async set(key, data) {
    try {
      await redis.setex(key, this.ttl, JSON.stringify(data));
    } catch (error) {
      console.error('Cache set error:', error);
    }
  }

  async processWithCache(input, model, options = {}) {
    const key = this.generateKey(input, model, options);
    
    // Try to get from cache
    const cached = await this.get(key);
    if (cached) {
      console.log('Cache hit');
      return cached;
    }
    
    // Process with PlutosAI
    console.log('Cache miss, processing...');
    const result = await this.client.processData({ input, model, options });
    
    // Cache the result
    await this.set(key, result);
    
    return result;
  }
}

// Usage
const cache = new PlutosAICache(client);
const result = await cache.processWithCache(
  'What is the capital of France?',
  'gpt-4'
);
```

### Queue Processing

Implement queue-based processing for handling large volumes of requests.

```javascript
import Bull from 'bull';

const processQueue = new Bull('plutos-processing', {
  redis: process.env.REDIS_URL
});

// Add jobs to queue
async function addToQueue(inputs, model, options) {
  const jobs = inputs.map(input => ({
    data: { input, model, options },
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000
    }
  }));
  
  return await processQueue.addBulk(jobs);
}

// Process jobs
processQueue.process(async (job) => {
  const { input, model, options } = job.data;
  
  try {
    const result = await client.processData({ input, model, options });
    return result;
  } catch (error) {
    console.error(`Job ${job.id} failed:`, error);
    throw error;
  }
});

// Handle completed jobs
processQueue.on('completed', (job, result) => {
  console.log(`Job ${job.id} completed:`, result.output);
});

// Handle failed jobs
processQueue.on('failed', (job, error) => {
  console.error(`Job ${job.id} failed:`, error.message);
});

// Example usage
const inputs = [
  'What is the capital of France?',
  'What is the capital of Germany?',
  'What is the capital of Italy?'
];

const jobs = await addToQueue(inputs, 'gpt-4', { maxTokens: 100 });
console.log(`Added ${jobs.length} jobs to queue`);
```

## Troubleshooting

### Common Issues and Solutions

#### Rate Limiting

```javascript
// Implement exponential backoff
async function processWithRetry(input, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await client.processData({ input, model: 'gpt-4' });
    } catch (error) {
      if (error.code === 'rate_limit_exceeded') {
        const delay = error.details?.retryAfter * 1000 || 60000;
        console.log(`Rate limited, waiting ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else if (attempt === maxRetries) {
        throw error;
      } else {
        const delay = Math.pow(2, attempt) * 1000;
        console.log(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
}
```

#### Input Validation

```javascript
function validateInput(input, model, options) {
  const errors = [];
  
  if (!input || typeof input !== 'string') {
    errors.push('Input must be a non-empty string');
  }
  
  if (input.length > 10000) {
    errors.push('Input too long (max 10,000 characters)');
  }
  
  if (!model || typeof model !== 'string') {
    errors.push('Model must be specified');
  }
  
  if (options) {
    if (options.temperature && (options.temperature < 0 || options.temperature > 2)) {
      errors.push('Temperature must be between 0 and 2');
    }
    
    if (options.maxTokens && (options.maxTokens < 1 || options.maxTokens > 4000)) {
      errors.push('Max tokens must be between 1 and 4000');
    }
  }
  
  return errors;
}

// Usage
const errors = validateInput(input, model, options);
if (errors.length > 0) {
  throw new Error(`Validation failed: ${errors.join(', ')}`);
}
```

#### Error Monitoring

```javascript
class PlutosAIMonitor {
  constructor() {
    this.errors = [];
    this.requests = 0;
    this.startTime = Date.now();
  }

  logRequest(success, duration, error = null) {
    this.requests++;
    
    if (!success) {
      this.errors.push({
        timestamp: new Date(),
        error: error?.message || 'Unknown error',
        code: error?.code,
        duration
      });
    }
  }

  getStats() {
    const uptime = Date.now() - this.startTime;
    const errorRate = this.errors.length / this.requests;
    
    return {
      totalRequests: this.requests,
      totalErrors: this.errors.length,
      errorRate: errorRate.toFixed(4),
      uptime: Math.floor(uptime / 1000),
      recentErrors: this.errors.slice(-10)
    };
  }
}

// Usage
const monitor = new PlutosAIMonitor();

try {
  const startTime = Date.now();
  const result = await client.processData({ input, model: 'gpt-4' });
  const duration = Date.now() - startTime;
  
  monitor.logRequest(true, duration);
} catch (error) {
  const duration = Date.now() - startTime;
  monitor.logRequest(false, duration, error);
}

console.log('Stats:', monitor.getStats());
```

This comprehensive examples and tutorials document provides real-world use cases, step-by-step guides, and advanced patterns for using PlutosAI effectively in various scenarios.
