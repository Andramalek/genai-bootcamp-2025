Step 1

docker compose -f
/home/andramalek/projects/clone/gen-ai-bootcamp-2025/opea-comps/docker-compose.yml
up -d

Step 2 

cd /home/andramalek/projects/clone/gen-ai-bootcamp-2025/opea-comps/mega-service
/home/andramalek/projects/clone/gen-ai-bootcamp-2025/path/to/venv/bin/python
app.py

Step 3 

   # Try one of these smaller models
   curl -X POST http://localhost:9000/api/pull -d '{"name": "phi"}'
   # OR
   curl -X POST http://localhost:9000/api/pull -d '{"name": "orca-mini:3b"}'
   # OR
   curl -X POST http://localhost:9000/api/pull -d '{"name": "gemma:2b"}'
   # OR
   curl -X POST http://localhost:9000/api/pull -d '{"name": "tiny-llama"}'

   Step 4

   Run curl command

```sh
curl -X POST http://localhost:8000/v1/example \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "hello, this is a test message"
  }'
  ```

  ```sh
 curl -X POST http://localhost:8000/v1/example-service \
-H "Content-Type: application/json" \
-d '{
    "messages": [
        {
            "role": "user",
            "content": "Hello, this is a test message"
        }
    ],
    "model": "test-model",
    "max_tokens": 100,
    "temperature": 0.7
}'
``` 

```sh
curl -X POST http://localhost:8080/v1/example-service \
-H "Content-Type: application/json" \
-H "Accept: application/json" \
-d '{
    "messages": [
        {
            "role": "user",
            "content": "What is artificial intelligence?"
        }
    ],
    "model": "llama2",
    "max_tokens": 100,
    "temperature": 0.7,
    "stream": false
}'
```