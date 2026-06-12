# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Cac anti-pattern tim thay

1. Secret bi hardcode trong source code: `OPENAI_API_KEY` va `DATABASE_URL` duoc viet truc tiep trong `app.py`.
2. Ung dung in thong tin nhay cam ra log, bao gom ca API key.
3. Cau hinh khong duoc quan ly bang environment variables; cac gia tri nhu `DEBUG` va `MAX_TOKENS` bi co dinh trong code.
4. App bind vao `localhost`, nen chi nhan ket noi noi bo va khong phu hop de chay trong container/cloud.
5. Port bi hardcode la `8000` thay vi doc tu bien moi truong `PORT`.
6. `reload=True` duoc bat, phu hop khi development nhung khong nen dung trong production.
7. Khong co endpoint `/health`, nen cloud platform khong the kiem tra service con song hay khong.
8. Khong co readiness check de bao cho load balancer biet app da san sang nhan traffic hay chua.
9. Khong co graceful shutdown khi container bi stop hoac platform restart.
10. Logging dung `print()` thay vi structured logging, gay kho khan khi debug tren production.

### Exercise 1.2: Kiem thu ban basic

Lenh da chay:

```bash
python app.py
curl.exe -X POST "http://localhost:8000/ask?question=hello"
```

Ket qua:

Ban basic khoi dong thanh cong tren localhost va tra ve cau tra loi qua endpoint `/ask`. Tuy nhien, ban nay chua production-ready vi con hardcode config, hardcode secret, khong co health check, chi bind vao localhost va dang bat debug reload.

### Exercise 1.3: Bang so sanh

| Feature | Develop | Production | Tai sao quan trong? |
|---|---|---|---|
| Config | Gia tri bi hardcode trong code | Doc config tu environment variables thong qua `settings` | Cloud platform cau hinh bang environment variables, nen khong can sua code khi chuyen moi truong |
| Secrets | API key va database URL nam trong source code | Secret duoc lay tu environment variables hoac file `.env` | Tranh lo credential tren GitHub hoac trong log |
| Host binding | Dung `localhost` | Dung host co the cau hinh, thuong la `0.0.0.0` | Container can listen tren `0.0.0.0` de nhan traffic tu ben ngoai |
| Port | Co dinh `8000` | Doc `PORT` tu environment | Railway, Render va cac platform tuong tu thuong inject port luc runtime |
| Health check | Khong co | Co `GET /health` | Platform co the phat hien container loi va restart |
| Readiness check | Khong co | Co `GET /ready` | Load balancer co the tranh gui traffic khi app chua san sang |
| Logging | Dung `print()` va co the log secret | Dung structured JSON logging va tranh log secret | Debug production de hon va an toan hon |
| Debug mode | `reload=True` | Chi reload khi debug mode duoc bat | Production khong nen chay che do reload cua development |
| Shutdown | Khong xu ly SIGTERM | Co lifecycle va graceful shutdown | Giup request hien tai va cleanup hoan thanh khi deploy/restart |
| CORS | Chua cau hinh | Cau hinh bang allowed origins | API production can kiem soat truy cap tu browser |



## Part 2: Docker

### Exercise 2.1: Cau hoi ve Dockerfile basic

1. Base image cua Dockerfile basic la `python:3.11`.
2. Working directory trong container la `/app`.
3. `COPY requirements.txt` duoc thuc hien truoc khi copy source code de tan dung Docker layer cache. Neu code thay doi nhung dependencies khong doi, Docker co the dung lai layer cai packages, giup build nhanh hon.
4. `CMD` la lenh mac dinh duoc chay khi container start. `ENTRYPOINT` thuong dung de co dinh executable chinh cua container, con `CMD` de cung cap command/argument mac dinh va de override hon khi run container.

### Exercise 2.2: Build va run image basic

Lenh build image basic:

```bash
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .
```

Lenh run container:

```bash
docker run --rm -p 8000:8000 my-agent:develop
```

Lenh test endpoint:

```bash
curl.exe -X POST "http://localhost:8000/ask?question=What%20is%20Docker"
```

Ket qua:

Container basic chay duoc va endpoint `/ask` tra ve cau tra loi. Endpoint nay nhan `question` qua query parameter, vi vay neu gui JSON body se bi loi `422 Unprocessable Entity`.

### Exercise 2.3: Multi-stage build

Trong Dockerfile production:

1. Stage 1 (`builder`) dung `python:3.11-slim`, cai build dependencies va Python packages. Day la stage phuc vu build, khong dung truc tiep de deploy.
2. Stage 2 (`runtime`) cung dung image slim, chi copy packages da cai va source code can thiet de chay app.
3. Image advanced nho hon vi runtime stage khong giu lai build tools, cache, va cac file khong can thiet.
4. Dockerfile production tao non-root user `appuser`, giup container an toan hon so voi chay bang root.

Lenh build image advanced:

```bash
docker build -f 02-docker/production/Dockerfile -t my-agent:advanced .
```

So sanh image size:

| Image | Size |
|---|---:|
| `my-agent:develop` | 1.66 GB |
| `my-agent:advanced` | 236 MB |

Nhan xet:

Image advanced nho hon rat nhieu so voi image develop. Dieu nay cho thay multi-stage build va slim base image giup giam kich thuoc image, deploy nhanh hon va giam attack surface.

### Exercise 2.4: Docker Compose stack

Lenh chay stack:

```bash
cd 02-docker/production
docker compose up --build
```

Stack gom cac service:

| Service | Vai tro |
|---|---|
| `agent` | FastAPI AI agent, chay endpoint `/ask`, `/health`, `/ready` |
| `redis` | Cache/session/rate limit backend trong kien truc production |
| `qdrant` | Vector database cho use case RAG |
| `nginx` | Reverse proxy va load balancer, expose cong `80` ra host |

Architecture:

```text
Client
  -> Nginx :80
  -> Agent :8000
  -> Redis / Qdrant qua internal Docker network
```

Ket qua test health check:

```json
{"status":"ok","uptime_seconds":11.9,"version":"2.0.0","timestamp":"2026-06-12T08:46:16.340173"}
```

Ket qua test `/ask`:

```text
Agent dang hoat dong tot! (mock response)
```

Trang thai stack:

```text
production-agent-1   Up (healthy)
production-nginx-1   Up, 0.0.0.0:80->80/tcp
production-redis-1   Up (healthy)
```

Luu y:

Qdrant trong lab bi `unhealthy` do health check cua image mau, nhung app Part 2 khong su dung Qdrant truc tiep. Da dieu chinh compose de agent khong bi block khi Qdrant chua healthy, giup Nginx va agent khoi dong dung muc tieu bai lab.


## Part 3: Cloud Deployment

### Exercise 3.1: Deploy len Render

Do Railway free plan/resource limit khong cho tao them service, em chuyen sang deploy bang Render theo lua chon hop le trong lab.

Public URL:

```text
https://day12-quickstart-agent.onrender.com
```

Platform:

```text
Render
```

File cau hinh Render:

```text
render.yaml
```

Cac cau hinh chinh trong `render.yaml`:

| Config | Gia tri |
|---|---|
| Service name | `day12-quickstart-agent` |
| Runtime | `python` |
| Region | `singapore` |
| Plan | `free` |
| Root directory | `03-cloud-deployment/railway` |
| Build command | `pip install -r requirements.txt` |
| Start command | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/health` |

Lenh test health check:

```bash
curl.exe https://day12-quickstart-agent.onrender.com/health
```

Ket qua:

```json
{"status":"ok","uptime_seconds":245.3,"platform":"Railway","timestamp":"2026-06-12T08:53:55.328861+00:00"}
```

Lenh test endpoint `/ask`:

```powershell
Invoke-RestMethod -Method POST https://day12-quickstart-agent.onrender.com/ask `
  -ContentType "application/json" `
  -Body '{"question":"Am I running on Render?"}'
```

Ket qua:

```text
question: Am I running on Render?
answer: Toi la AI agent... (mock response)
```

Ghi chu:

Response `/health` co field `"platform":"Railway"` vi app demo trong folder `03-cloud-deployment/railway` hardcode chu Railway. Tuy nhien service thuc te dang duoc deploy tren Render tai URL `.onrender.com`.

Screenshots:

```text
screenshots/image.png
screenshots/Screenshot 2026-06-12 155245.png
```

### Exercise 3.2: So sanh Render voi Railway

| Noi dung | Railway | Render |
|---|---|---|
| File config | `railway.toml` | `render.yaml` |
| Cach deploy | Dung Railway CLI nhu `railway init`, `railway up` | Connect GitHub repo va dung Blueprint |
| Start command | `uvicorn app:app --host 0.0.0.0 --port $PORT` | `uvicorn app:app --host 0.0.0.0 --port $PORT` |
| Health check | `healthcheckPath = "/health"` | `healthCheckPath: /health` |
| Environment variables | Set qua Railway CLI hoac Dashboard | Khai bao trong `envVars` hoac set tren Dashboard |
| Subfolder app | Thuong deploy trong folder hien tai | Dung `rootDir` de chi dinh folder app trong repo |
| Auto deploy | Co the deploy bang CLI/push | `autoDeployTrigger: commit` tu GitHub |

Nhan xet:

Railway phu hop de deploy nhanh bang CLI, nhung tai khoan free co the bi gioi han resource. Render Blueprint phu hop khi muon khai bao infrastructure bang file YAML va auto deploy tu GitHub.

### Exercise 3.3: Optional - GCP Cloud Run

Da doc qua cac file:

```text
03-cloud-deployment/production-cloud-run/cloudbuild.yaml
03-cloud-deployment/production-cloud-run/service.yaml
```

Y nghia:

1. `cloudbuild.yaml` mo ta CI/CD pipeline: build container image, push image len registry va deploy len Cloud Run.
2. `service.yaml` mo ta Cloud Run service: container, port, environment variables, scaling va cau hinh runtime.

Trong lab nay em khong deploy len GCP Cloud Run vi da deploy thanh cong public URL bang Render.



## Part 4: API Security

### Exercise 4.1: API Key authentication

Da test ban develop trong Quick Start voi API key:

```powershell
$env:AGENT_API_KEY="my-secret-key"
python app.py
```

Test khong co API key:

```powershell
Invoke-RestMethod -Method POST http://localhost:8000/ask `
  -ContentType "application/json" `
  -Body '{"question":"Hello"}'
```

Ket qua mong doi:

```text
401 Unauthorized
```

Test co API key hop le:

```powershell
Invoke-RestMethod -Method POST http://localhost:8000/ask `
  -Headers @{ "X-API-Key" = "my-secret-key" } `
  -ContentType "application/json" `
  -Body '{"question":"Hello"}'
```

Ket qua:

Endpoint `/ask` tra ve cau tra loi thanh cong.

Tra loi cau hoi:

1. API key duoc gui qua header `X-API-Key`.
2. Neu thieu hoac sai key, server tra ve `401 Unauthorized`.
3. De rotate key, doi gia tri bien moi truong `AGENT_API_KEY` va restart service. Khong can sua source code.

### Exercise 4.2: JWT authentication

Da chay ban production:

```powershell
cd 04-api-gateway/production
python app.py
```

Trong qua trinh test co gap loi `500 Internal Server Error` do middleware dung:

```python
response.headers.pop("server", None)
```

`response.headers` la `MutableHeaders` va khong ho tro method `.pop()`. Da sua thanh:

```python
if "server" in response.headers:
    del response.headers["server"]
```

Sau khi sua, lay JWT token thanh cong bang:

```powershell
$tokenResponse = Invoke-RestMethod -Method POST http://localhost:8000/auth/token `
  -ContentType "application/json" `
  -Body '{"username":"student","password":"demo123"}'

$TOKEN = $tokenResponse.access_token
```

Dung token de goi protected endpoint:

```powershell
Invoke-RestMethod -Method POST http://localhost:8000/ask `
  -Headers @{ "Authorization" = "Bearer $TOKEN" } `
  -ContentType "application/json" `
  -Body '{"question":"Explain JWT"}'
```

Ket qua:

```text
question: Explain JWT
answer: Agent dang hoat dong tot... (mock response)
```

Nhan xet:

JWT flow gom 2 buoc: user dang nhap bang username/password de lay token, sau do gui token trong header `Authorization: Bearer <token>` khi goi endpoint duoc bao ve.

### Exercise 4.3: Rate limiting

File `rate_limiter.py` dung algorithm Sliding Window:

1. Moi user co mot danh sach timestamp request.
2. Moi request se xoa cac timestamp cu ngoai window 60 giay.
3. Neu so request trong window vuot limit, server tra `429 Too Many Requests`.

Limit:

| Role | Limit |
|---|---:|
| User | 10 requests/minute |
| Admin | 100 requests/minute |

Lenh test:

```powershell
for ($i = 1; $i -le 20; $i++) {
  try {
    Invoke-RestMethod -Method POST http://localhost:8000/ask `
      -Headers @{ "Authorization" = "Bearer $TOKEN" } `
      -ContentType "application/json" `
      -Body "{`"question`":`"Test $i`"}" | Out-Null

    Write-Host "Request $i OK"
  } catch {
    Write-Host "Request $i failed:" $_.Exception.Response.StatusCode.value__
  }
}
```

Ket qua:

```text
Request 1 OK
Request 2 OK
Request 3 OK
Request 4 OK
Request 5 OK
Request 6 OK
Request 7 OK
Request 8 OK
Request 9 OK
Request 10 failed: 429
Request 11 failed: 429
...
Request 20 failed: 429
```

Nhan xet:

Rate limiting hoat dong dung. Sau khi user dat limit trong window hien tai, cac request tiep theo bi chan voi status code `429`.

### Exercise 4.4: Cost guard

File `cost_guard.py` dung CostGuard de track usage va budget:

1. Moi user co mot `UsageRecord` theo ngay.
2. Moi request ghi nhan input tokens, output tokens va request count.
3. Chi phi duoc tinh theo gia token mock:
   - Input: `$0.00015 / 1K tokens`
   - Output: `$0.0006 / 1K tokens`
4. Moi user co daily budget `$1/day`.
5. Toan service co global daily budget `$10/day`.
6. Neu user vuot budget thi server tra `402 Payment Required`.
7. Neu global budget vuot gioi han thi server tra `503 Service Unavailable`.
8. Usage reset theo ngay dua tren date hien tai.

Lenh xem usage:

```powershell
Invoke-RestMethod -Method GET http://localhost:8000/me/usage `
  -Headers @{ "Authorization" = "Bearer $TOKEN" }
```

Ket qua:

```text
user_id              : student
date                 : 2026-06-12
requests             : 10
input_tokens         : 40
output_tokens        : 300
cost_usd             : 0.000186
budget_usd           : 1.0
budget_remaining_usd : 0.999814
budget_used_pct      : 0.0
```

Nhan xet:

Cost guard da track duoc so request, token usage, chi phi da dung va budget con lai. Vi day la mock LLM nen chi phi rat nho va chua vuot budget.



## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks

Da chay ban develop:

```powershell
cd 05-scaling-reliability/develop
python app.py
```

Test liveness endpoint:

```powershell
curl.exe http://localhost:8000/health
```

Ket qua:

```json
{
  "status": "degraded",
  "uptime_seconds": 4.8,
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2026-06-12T09:20:21.147887+00:00",
  "checks": {
    "memory": {
      "status": "degraded",
      "used_percent": 92.4
    }
  }
}
```

Nhan xet:

Endpoint `/health` hoat dong dung vai tro liveness probe. Status la `degraded` vi memory tren may local dang dung 92.4%, nhung endpoint van tra ve thong tin ro rang de platform/ops co the theo doi.

Test readiness endpoint:

```powershell
curl.exe http://localhost:8000/ready
```

Ket qua:

```json
{"ready":true,"in_flight_requests":1}
```

Nhan xet:

Endpoint `/ready` cho biet app da san sang nhan traffic. `in_flight_requests` giup quan sat so request dang xu ly.

Test endpoint `/ask`:

```powershell
curl.exe -X POST "http://localhost:8000/ask?question=Hello"
```

Ket qua:

```json
{"answer":"Day la cau tra loi tu AI agent (mock). Trong production, day se la response tu OpenAI/Anthropic."}
```

### Exercise 5.2: Graceful shutdown

Ban develop co xu ly shutdown thong qua FastAPI lifespan va signal handler:

1. Khi startup, app load dependencies/model gia lap va dat `_is_ready = True`.
2. Khi shutdown, app dat `_is_ready = False`.
3. App cho cac in-flight requests hoan thanh truoc khi thoat, toi da 30 giay.
4. Signal handler ghi log khi nhan `SIGTERM` hoac `SIGINT`.

Y nghia:

Graceful shutdown giup container/platform restart ma khong cat ngang request dang xu ly. Day la yeu cau quan trong khi rolling deploy hoac scale down.

### Exercise 5.3: Stateless design

Ban production luu conversation/session state trong Redis thay vi memory cua tung instance.

Anti-pattern:

```python
conversation_history = {}
```

Van de cua cach nay:

Neu chay 3 instances, request dau tien co the vao instance A, request tiep theo vao instance B. Neu state nam trong memory cua A thi B se khong thay history.

Cach dung trong production:

```python
_redis.setex(f"session:{session_id}", ttl_seconds, serialized)
_redis.get(f"session:{session_id}")
```

Loi ich:

Bat ky instance nao cung co the doc/ghi session tu Redis. Vi vay app tro thanh stateless va co the scale horizontally.

### Exercise 5.4: Load balancing

Da chay production stack voi 3 agent instances:

```powershell
cd 05-scaling-reliability/production
docker compose up --build --scale agent=3
```

Nginx expose service qua port `8080` va route traffic den cac agent instances.

Test health qua Nginx:

```powershell
curl.exe http://localhost:8080/health
```

Lan dau co the fail neu Nginx/agent chua start xong:

```text
curl: (7) Failed to connect to localhost port 8080
```

Sau khi stack san sang, ket qua:

```json
{"status":"ok","instance_id":"instance-3851e5","uptime_seconds":20.5,"storage":"redis","redis_connected":true}
```

Test readiness qua Nginx:

```powershell
curl.exe http://localhost:8080/ready
```

Ket qua:

```json
{"ready":true,"instance":"instance-cddf3d"}
```

Nhan xet:

Moi response co `instance_id`/`instance`, cho thay request co the duoc phuc vu boi cac instance khac nhau. Redis connected la `true`, nen state duoc dat o backing service chung.

### Exercise 5.5: Test stateless

Chay script:

```powershell
cd 05-scaling-reliability/production
python test_stateless.py
```

Ket qua chinh:

```text
Session ID: 884e9698-846c-4ecf-9ce1-5667bcd68a31

Request 1: [instance-4f1448]
Request 2: [instance-3851e5]
Request 3: [instance-cddf3d]
Request 4: [instance-4f1448]
Request 5: [instance-3851e5]

Total requests: 5
Instances used: {'instance-cddf3d', 'instance-3851e5', 'instance-4f1448'}
All requests served despite different instances!

Total messages: 10
Session history preserved across all instances via Redis!
```

Nhan xet:

Test chung minh load balancing va stateless design hoat dong dung:

1. 5 requests duoc phuc vu boi 3 instances khac nhau.
2. Tat ca request dung chung mot `session_id`.
3. Conversation history co du 10 messages, gom 5 user messages va 5 assistant messages.
4. History van duoc giu dung du request di qua cac instances khac nhau, vi state nam trong Redis.


