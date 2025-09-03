<<<<<<< Current (Your changes)
# PlutosAI — Enterprise Family Office Platform

A production-ready, AI-native family office and asset management platform built with microservices architecture. Designed for regulatory compliance, scalability, and AI-driven insights.

## 🏗️ Architecture Overview

This platform follows a **microservices architecture** with domain-driven design, event-driven communication, and comprehensive observability.

### Core Services

- **🎯 Client Service** (`/clients`) - Client onboarding, KYC, profile management
- **📊 Investment Service** (`/portfolios`, `/transactions`) - Portfolio management, trading, valuations
- **⚖️ Compliance Service** (`/compliance`) - AML/KYC checks, monitoring, audit trails
- **📈 Reporting Service** (`/reports`) - Client reports, analytics, dashboards
- **🤖 AI Service** (`/insights`) - ML models, recommendations, risk analysis
- **⛓️ Blockchain Service** (`/wallets`, `/transactions`, `/nfts`) - Digital asset management, DeFi, NFTs
- **🚪 Gateway Service** - API gateway, authentication, rate limiting

### Technology Stack

**Backend:**
- **Language:** Python 3.11
- **Framework:** FastAPI (async, high-performance)
- **Database:** PostgreSQL (async SQLAlchemy)
- **Message Queue:** NATS (event-driven architecture)
- **Cache:** Redis
- **Authentication:** JWT with role-based access control

**Infrastructure:**
- **Containerization:** Docker
- **Orchestration:** Kubernetes
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus + Grafana
- **Security:** Container scanning, secrets management

**Development:**
- **Linting:** Ruff
- **Type Checking:** MyPy
- **Testing:** Pytest with async support
- **API Docs:** Auto-generated OpenAPI/Swagger

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- kubectl (for Kubernetes deployment)

### Local Development

1. **Clone and setup:**
   ```bash
   git clone https://github.com/your-org/plutosai.git
   cd plutosai
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```

2. **Start infrastructure:**
   ```bash
   cd infrastructure/docker
   docker-compose up -d
   ```

3. **Install dependencies and run client service:**
   ```bash
   cd services/client-service
   pip install -e '.[dev]'
   uvicorn src.api:app --reload --host 0.0.0.0 --port 8001
   ```

4. **Access services:**
   - **API Gateway:** http://localhost:8000
   - **Client Service:** http://localhost:8001
   - **Grafana:** http://localhost:3000 (admin/admin)
   - **Prometheus:** http://localhost:9090

### API Examples

**Create a client:**
```bash
curl -X POST "http://localhost:8001/clients" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "type": "individual",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com"
  }'
```

**Get client details:**
```bash
curl -X GET "http://localhost:8001/clients/{client_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📁 Project Structure

```
plutosai/
├── services/                    # Microservices
│   ├── client-service/         # Client management
│   ├── investment-ops/         # Portfolio & trading
│   ├── compliance-service/     # Compliance & monitoring
│   ├── reporting-service/      # Reports & analytics
│   ├── ai-service/            # AI/ML features
│   ├── blockchain-service/    # Digital asset management
│   └── gateway-service/       # API gateway
├── shared/                     # Shared libraries
│   ├── domain/                # Domain models
│   │   ├── client.py         # Client domain models
│   │   ├── investment.py     # Investment domain models
│   │   ├── compliance.py     # Compliance domain models
│   │   └── blockchain.py     # Blockchain domain models
│   ├── auth/                  # Authentication utilities
│   ├── events/                # Event definitions
│   └── utils/                 # Common utilities
├── infrastructure/            # Infrastructure as Code
│   ├── docker/               # Docker Compose & configs
│   └── k8s/                  # Kubernetes manifests
├── monitoring/                # Observability
│   ├── prometheus/           # Metrics collection
│   └── grafana/             # Dashboards
├── tests/                     # Test suites
│   ├── integration/          # Integration tests
│   └── e2e/                  # End-to-end tests
├── docs/                      # Documentation
└── .github/workflows/         # CI/CD pipelines
```

## 🔐 Security & Compliance

### Authentication & Authorization
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Multi-factor authentication support
- Session management with Redis

### Regulatory Compliance
- **AML/KYC:** Integrated screening and monitoring
- **Audit Trails:** Comprehensive logging of all actions
- **Data Privacy:** GDPR/CCPA compliant data handling
- **Risk Management:** Real-time risk scoring and alerts

### Security Features
- **Container Security:** Trivy vulnerability scanning
- **Secrets Management:** Encrypted secrets in Kubernetes
- **Network Security:** Service mesh with mTLS
- **API Security:** Rate limiting, CORS, input validation

## 📊 Monitoring & Observability

### Metrics
- **Application Metrics:** Request latency, error rates, throughput
- **Business Metrics:** Client onboarding funnel, portfolio performance
- **System Metrics:** CPU, memory, disk usage, network I/O

### Logging
- Structured logging with correlation IDs
- Centralized log aggregation
- Log levels: DEBUG, INFO, WARN, ERROR
- Retention policies and archival

### Alerting
- Real-time alerts for system issues
- Compliance violation notifications
- Performance degradation alerts
- Automated incident response

## 🚀 Deployment

### Environments
- **Development:** Local Docker Compose
- **Staging:** Kubernetes cluster for testing
- **Production:** Highly available Kubernetes cluster

### CI/CD Pipeline
1. **Code Quality:** Lint, type check, security scan
2. **Build:** Docker image creation and registry push
3. **Test:** Unit, integration, and E2E tests
4. **Deploy:** Automated deployment with rollbacks
5. **Monitor:** Health checks and alerting setup

## 🤖 AI/ML Features

### Portfolio Analysis
- **Risk Assessment:** Monte Carlo simulations, VaR calculations
- **Performance Attribution:** Factor analysis and benchmarking
- **Rebalancing Recommendations:** Tax-efficient portfolio optimization

### Client Insights
- **Personalized Recommendations:** ML-driven investment suggestions
- **Behavioral Analysis:** Client interaction patterns and preferences
- **Market Intelligence:** Real-time news and sentiment analysis

### Compliance Automation
- **Transaction Monitoring:** ML-based anomaly detection
- **KYC Enhancement:** Automated document processing and verification
- **Risk Scoring:** Predictive models for client risk assessment

## ⛓️ Blockchain Integration

### Digital Asset Management
- **Multi-Blockchain Support:** Ethereum, Polygon, BSC, Arbitrum, Bitcoin
- **Wallet Management:** Hot, cold, multi-signature, and hardware wallets
- **Asset Types:** Cryptocurrencies, tokens, NFTs, security tokens
- **DeFi Integration:** Lending, staking, liquidity provision
- **Cross-Chain Bridges:** Seamless asset transfers between networks

### Key Features
- **Secure Custody:** Institutional-grade wallet security
- **Transaction Monitoring:** Real-time blockchain transaction tracking
- **NFT Portfolio:** Complete NFT management and valuation
- **Yield Optimization:** Automated DeFi yield farming
- **Compliance Integration:** Blockchain transaction compliance reporting

### Example Use Cases
```bash
# Create a multi-signature Ethereum wallet
curl -X POST "http://localhost:8006/wallets" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "client_id": "client-123",
    "name": "ETH Multi-Sig",
    "wallet_type": "multisig_wallet",
    "blockchain": "ethereum",
    "required_signatures": 2,
    "total_signers": 3
  }'

# Register an NFT in the portfolio
curl -X POST "http://localhost:8006/nfts" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "wallet_id": "wallet-123",
    "contract_address": "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
    "token_id": "1234",
    "token_standard": "ERC-721"
  }'
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run the full test suite: `make test-all`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -e '.[dev]'

# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy shared/

# Start local services
docker-compose up -d
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋 Support

- **Issues:** [GitHub Issues](https://github.com/your-org/plutosai/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/plutosai/discussions)
- **Documentation:** [Wiki](https://github.com/your-org/plutosai/wiki)

## 🎯 Roadmap

### Phase 1 (Current)
- [x] Microservices architecture
- [x] Domain-driven design
- [x] Authentication & authorization
- [x] Basic CRUD operations
- [x] Infrastructure as code

### Phase 2 (Next)
- [ ] AI/ML model integration
- [ ] Advanced compliance features
- [ ] Multi-tenant architecture
- [ ] Real-time notifications
- [ ] Mobile app API

### Phase 3 (Future)
- [ ] Blockchain integration
- [ ] Advanced analytics
- [ ] Regulatory reporting automation
- [ ] Global expansion features

---

**Built with ❤️ for the future of wealth management.**
=======
# PlutosAI

A comprehensive AI-powered platform for intelligent data processing and analysis.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Components](#components)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## Overview

PlutosAI is a modern, scalable platform that provides intelligent data processing capabilities through a comprehensive set of APIs and components. The platform is designed to handle various AI tasks including data analysis, natural language processing, and machine learning operations.

### Key Features

- **RESTful API**: Complete REST API for all operations
- **Real-time Processing**: Stream-based data processing capabilities
- **Scalable Architecture**: Built for high-performance and scalability
- **Comprehensive SDK**: Multiple language support (JavaScript, Python, Go)
- **Web Components**: Reusable UI components for rapid development

## Installation

### Prerequisites

- Node.js 18+ (for JavaScript/TypeScript usage)
- Python 3.8+ (for Python SDK)
- Go 1.19+ (for Go SDK)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/your-org/plutos-ai.git
cd plutos-ai

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start the development server
npm run dev
```

## Quick Start

### Using the JavaScript SDK

```javascript
import { PlutosAI } from '@plutos-ai/sdk';

const client = new PlutosAI({
  apiKey: 'your-api-key',
  environment: 'production'
});

// Process data
const result = await client.processData({
  input: 'Your input data',
  model: 'gpt-4',
  options: {
    temperature: 0.7,
    maxTokens: 1000
  }
});

console.log(result.output);
```

### Using the Python SDK

```python
from plutos_ai import PlutosAI

client = PlutosAI(
    api_key="your-api-key",
    environment="production"
)

# Process data
result = client.process_data(
    input="Your input data",
    model="gpt-4",
    options={
        "temperature": 0.7,
        "max_tokens": 1000
    }
)

print(result.output)
```

## API Documentation

### Authentication

All API requests require authentication using an API key. Include your API key in the request headers:

```bash
Authorization: Bearer YOUR_API_KEY
```

### Base URL

- **Production**: `https://api.plutos-ai.com/v1`
- **Staging**: `https://staging-api.plutos-ai.com/v1`
- **Development**: `http://localhost:3000/v1`

### Core Endpoints

#### Data Processing

##### POST /process

Process data using AI models.

**Request Body:**
```json
{
  "input": "string",
  "model": "string",
  "options": {
    "temperature": "number",
    "maxTokens": "number",
    "topP": "number"
  }
}
```

**Response:**
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
  "createdAt": "string"
}
```

**Example:**
```bash
curl -X POST https://api.plutos-ai.com/v1/process \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Analyze this text for sentiment",
    "model": "gpt-4",
    "options": {
      "temperature": 0.7,
      "maxTokens": 1000
    }
  }'
```

#### Batch Processing

##### POST /batch

Process multiple inputs in a single request.

**Request Body:**
```json
{
  "inputs": ["string"],
  "model": "string",
  "options": {
    "temperature": "number",
    "maxTokens": "number"
  }
}
```

**Response:**
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
  }
}
```

#### Stream Processing

##### POST /stream

Stream data processing results in real-time.

**Request Body:**
```json
{
  "input": "string",
  "model": "string",
  "options": {
    "temperature": "number",
    "maxTokens": "number"
  }
}
```

**Response (Server-Sent Events):**
```
data: {"chunk": "partial", "output": "Hello"}

data: {"chunk": "partial", "output": " world"}

data: {"chunk": "final", "output": "Hello world", "usage": {...}}
```

### Error Handling

All API endpoints return standard HTTP status codes:

- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error

Error responses include detailed information:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object"
  }
}
```

## Components

### Web Components

PlutosAI provides a set of reusable web components for building AI-powered interfaces.

#### PlutosAIProcessor

A component for processing data with AI models.

```html
<plutos-ai-processor
  api-key="your-api-key"
  model="gpt-4"
  placeholder="Enter your text here..."
  @result="handleResult"
  @error="handleError">
</plutos-ai-processor>
```

**Properties:**
- `api-key` (string): Your PlutosAI API key
- `model` (string): AI model to use
- `placeholder` (string): Input placeholder text
- `temperature` (number): Model temperature (0-1)
- `max-tokens` (number): Maximum tokens to generate

**Events:**
- `result`: Fired when processing completes
- `error`: Fired when an error occurs
- `loading`: Fired when processing starts

#### PlutosAIStream

A component for real-time streaming AI responses.

```html
<plutos-ai-stream
  api-key="your-api-key"
  model="gpt-4"
  @chunk="handleChunk"
  @complete="handleComplete">
</plutos-ai-stream>
```

**Properties:**
- `api-key` (string): Your PlutosAI API key
- `model` (string): AI model to use
- `auto-start` (boolean): Start streaming automatically

**Events:**
- `chunk`: Fired for each stream chunk
- `complete`: Fired when streaming completes
- `error`: Fired when an error occurs

### React Components

#### usePlutosAI Hook

A React hook for integrating PlutosAI functionality.

```jsx
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

#### PlutosAIProvider

A React context provider for PlutosAI configuration.

```jsx
import { PlutosAIProvider } from '@plutos-ai/react';

function App() {
  return (
    <PlutosAIProvider
      apiKey="your-api-key"
      environment="production"
    >
      <MyComponent />
    </PlutosAIProvider>
  );
}
```

## Examples

### Basic Text Processing

```javascript
import { PlutosAI } from '@plutos-ai/sdk';

const client = new PlutosAI({ apiKey: 'your-api-key' });

// Simple text processing
const result = await client.processData({
  input: 'What is the capital of France?',
  model: 'gpt-4'
});

console.log(result.output); // "The capital of France is Paris."
```

### Sentiment Analysis

```javascript
const sentimentResult = await client.processData({
  input: 'I love this product! It works perfectly.',
  model: 'gpt-4',
  options: {
    systemPrompt: 'Analyze the sentiment of the following text. Respond with only: positive, negative, or neutral.',
    temperature: 0.1
  }
});

console.log(sentimentResult.output); // "positive"
```

### Batch Processing

```javascript
const batchResult = await client.batchProcess({
  inputs: [
    'Hello, how are you?',
    'What is the weather like?',
    'Tell me a joke'
  ],
  model: 'gpt-4'
});

batchResult.results.forEach((result, index) => {
  console.log(`Input ${index + 1}:`, result.output);
});
```

### Streaming Responses

```javascript
const stream = await client.streamProcess({
  input: 'Write a short story about a robot.',
  model: 'gpt-4'
});

for await (const chunk of stream) {
  if (chunk.chunk === 'partial') {
    process.stdout.write(chunk.output);
  } else if (chunk.chunk === 'final') {
    console.log('\nComplete!');
  }
}
```

### Web Component Integration

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://unpkg.com/@plutos-ai/components"></script>
</head>
<body>
  <plutos-ai-processor
    api-key="your-api-key"
    model="gpt-4"
    placeholder="Ask me anything..."
    @result="handleResult">
  </plutos-ai-processor>

  <script>
    function handleResult(event) {
      console.log('Result:', event.detail);
    }
  </script>
</body>
</html>
```

### React Integration

```jsx
import React, { useState } from 'react';
import { usePlutosAI } from '@plutos-ai/react';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const { processData, isLoading } = usePlutosAI({
    apiKey: 'your-api-key',
    model: 'gpt-4'
  });

  const sendMessage = async (text) => {
    const userMessage = { role: 'user', content: text };
    setMessages(prev => [...prev, userMessage]);

    const result = await processData(text);
    const aiMessage = { role: 'assistant', content: result.output };
    setMessages(prev => [...prev, aiMessage]);
  };

  return (
    <div>
      {messages.map((msg, index) => (
        <div key={index} className={msg.role}>
          {msg.content}
        </div>
      ))}
      {isLoading && <div>AI is thinking...</div>}
    </div>
  );
}
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/plutos-ai.git
cd plutos-ai

# Install dependencies
npm install

# Run tests
npm test

# Start development server
npm run dev

# Build for production
npm run build
```

### Code Style

- Follow the existing code style
- Write tests for new features
- Update documentation for API changes
- Use conventional commits

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [docs.plutos-ai.com](https://docs.plutos-ai.com)
- **API Reference**: [api.plutos-ai.com](https://api.plutos-ai.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/plutos-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/plutos-ai/discussions)
- **Email**: support@plutos-ai.com

---

**PlutosAI** - Intelligent data processing for the modern web.
>>>>>>> Incoming (Background Agent changes)
