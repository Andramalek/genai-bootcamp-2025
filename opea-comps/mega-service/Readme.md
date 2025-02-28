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