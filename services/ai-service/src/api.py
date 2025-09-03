from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import redis
import json
from datetime import timedelta
import hashlib

app = FastAPI()

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

openai.api_key = 'your-openai-key'  # Replace with actual key or env var
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class ProcessRequest(BaseModel):
    inputs: list[str]
    model: str = 'gpt-4'
    options: dict = {}

@app.post('/process')
def process_data(request: ProcessRequest):
    key = hashlib.md5(json.dumps({'inputs': request.inputs, 'model': request.model, 'options': request.options}).encode()).hexdigest()
    cache_key = f'ai_result:{key}'

    # Check cache
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Process batch with OpenAI
    results = []
    try:
        for input_text in request.inputs:
            response = openai.ChatCompletion.create(
                model=request.model,
                messages=[{'role': 'user', 'content': input_text}],
                **request.options
            )
            results.append(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Cache using pipeline for efficiency
    pipe = redis_client.pipeline()
    pipe.setex(cache_key, timedelta(hours=1), json.dumps({'results': results}))
    pipe.incr('ai_requests_count')
    pipe.execute()

    return {'results': results}

class QuantizedRequest(BaseModel):
    input: str

# Load quantized model
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

quantized_model = AutoModelForCausalLM.from_pretrained('gpt2', load_in_8bit=True, device_map='auto')
tokenizer = AutoTokenizer.from_pretrained('gpt2')

@app.post('/quantized_process')
def quantized_process(request: QuantizedRequest):
    cache_key = f'quantized_result:{hashlib.md5(request.input.encode()).hexdigest()}'

    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    inputs = tokenizer(request.input, return_tensors='pt').to('cuda' if torch.cuda.is_available() else 'cpu')
    outputs = quantized_model.generate(**inputs)
    result = tokenizer.decode(outputs[0])

    pipe = redis_client.pipeline()
    pipe.setex(cache_key, timedelta(hours=1), json.dumps({'result': result}))
    pipe.incr('quantized_requests_count')
    pipe.execute()

    return {'result': result}