# MCP 서버 설치 가이드

이 문서는 MCP 서버의 설치 및 설정 방법에 대한 자세한 안내를 제공합니다.

## 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [로컬 개발 환경 설치](#로컬-개발-환경-설치)
3. [Docker를 사용한 설치](#docker를-사용한-설치)
4. [프로덕션 환경 설정](#프로덕션-환경-설정)
5. [환경 변수 구성](#환경-변수-구성)
6. [문제 해결](#문제-해결)

## 시스템 요구사항

### 최소 요구사항

- Python 3.8 이상
- 2GB RAM
- 1GB 디스크 공간

### 권장 요구사항

- Python 3.10 이상
- 4GB RAM
- 5GB 디스크 공간
- Docker 및 Docker Compose (컨테이너 배포용)

## 로컬 개발 환경 설치

### 1. 저장소 클론

```bash
git clone https://github.com/your-username/mcp-server.git
cd mcp-server
```

### 2. 가상 환경 설정

#### Linux/macOS
```bash
python -m venv venv
source venv/bin/activate
```

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 의존성 설치

#### 기본 의존성
```bash
pip install -r requirements.txt
```

#### 개발 의존성 (테스트, 린팅 등)
```bash
pip install -r requirements-dev.txt
```

### 4. 환경 변수 설정

```bash
cp .env.example .env
```

텍스트 편집기로 `.env` 파일을 열고 필요한 설정을 구성하세요.

### 5. 데이터베이스 마이그레이션 (필요한 경우)

```bash
python -m mcp_server.db.migrations
```

### 6. 서버 실행

```bash
python -m mcp_server.main
```

서버가 기본적으로 http://localhost:8000 에서 실행됩니다.

## Docker를 사용한 설치

### 1. Docker 및 Docker Compose 설치

[Docker 설치 가이드](https://docs.docker.com/get-docker/)와 [Docker Compose 설치 가이드](https://docs.docker.com/compose/install/)를 참조하세요.

### 2. 환경 변수 설정

```bash
cp .env.example .env
```

텍스트 편집기로 `.env` 파일을 열고 필요한 설정을 구성하세요.

### 3. Docker 컨테이너 빌드 및 실행

```bash
docker-compose up -d
```

### 4. 로그 확인

```bash
docker-compose logs -f
```

## 프로덕션 환경 설정

### 1. 시스템 준비

```bash
# 필요한 시스템 패키지 설치 (Ubuntu/Debian 기준)
sudo apt update
sudo apt install -y python3-pip python3-venv nginx
```

### 2. 애플리케이션 설치

```bash
git clone https://github.com/your-username/mcp-server.git /opt/mcp-server
cd /opt/mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env 파일 편집
```

### 3. Gunicorn 설정

```bash
pip install gunicorn
```

`gunicorn.conf.py` 파일 생성:

```python
workers = 4
bind = "127.0.0.1:8000"
worker_class = "uvicorn.workers.UvicornWorker"
keepalive = 120
max_requests = 1000
max_requests_jitter = 50
timeout = 120
```

### 4. Systemd 서비스 설정

`/etc/systemd/system/mcp-server.service` 파일 생성:

```ini
[Unit]
Description=MCP Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/mcp-server
EnvironmentFile=/opt/mcp-server/.env
ExecStart=/opt/mcp-server/venv/bin/gunicorn -c gunicorn.conf.py mcp_server.main:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

서비스 활성화 및 시작:

```bash
sudo systemctl enable mcp-server
sudo systemctl start mcp-server
```

### 5. Nginx 설정

`/etc/nginx/sites-available/mcp-server` 파일 생성:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

설정 활성화 및 Nginx 재시작:

```bash
sudo ln -s /etc/nginx/sites-available/mcp-server /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 환경 변수 구성

`.env` 파일에서 다음 환경 변수를 구성할 수 있습니다:

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `DEBUG` | 디버그 모드 활성화 | `False` |
| `LOG_LEVEL` | 로깅 레벨 | `INFO` |
| `API_KEY` | API 인증 키 | - |
| `MAX_SESSIONS` | 최대 세션 수 | `1000` |
| `SESSION_TIMEOUT` | 세션 타임아웃(초) | `3600` |
| `RATE_LIMIT` | 분당 최대 요청 수 | `60` |

## 문제 해결

### 일반적인 문제

#### 서버가 시작되지 않음

1. Python 버전 확인: `python --version`
2. 의존성 설치 확인: `pip list`
3. 로그 확인: `tail -f logs/mcp-server.log`

#### 연결 오류

1. 서버 실행 상태 확인: `systemctl status mcp-server`
2. 포트 사용 확인: `netstat -tulpn | grep 8000`
3. 방화벽 설정 확인: `sudo ufw status`

#### 성능 문제

1. 시스템 리소스 확인: `top` 또는 `htop`
2. 로그에서 병목 현상 확인
3. 워커 수 조정: `gunicorn.conf.py`에서 `workers` 값 수정

### 지원 받기

추가 지원이 필요한 경우 다음 방법을 이용하세요:

1. GitHub 이슈 생성
2. 프로젝트 토론 포럼 이용
3. 문서 참조: `/docs` 디렉토리