#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 로그 파일
BACKEND_LOG="logs/backend.log"
FRONTEND_LOG="logs/frontend.log"

# PID 파일
BACKEND_PID="/tmp/backend.pid"
FRONTEND_PID="/tmp/frontend.pid"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Quick Agent POC 서버 시작${NC}"
echo -e "${GREEN}========================================${NC}"

# 기존 프로세스 정리
cleanup() {
    echo -e "\n${YELLOW}서버를 종료합니다...${NC}"

    if [ -f "$BACKEND_PID" ]; then
        BPID=$(cat "$BACKEND_PID")
        if ps -p $BPID > /dev/null 2>&1; then
            echo -e "${BLUE}Backend 서버 종료 (PID: $BPID)${NC}"
            kill $BPID
        fi
        rm -f "$BACKEND_PID"
    fi

    if [ -f "$FRONTEND_PID" ]; then
        FPID=$(cat "$FRONTEND_PID")
        if ps -p $FPID > /dev/null 2>&1; then
            echo -e "${BLUE}Frontend 서버 종료 (PID: $FPID)${NC}"
            kill $FPID
        fi
        rm -f "$FRONTEND_PID"
    fi

    # tail 프로세스 종료
    if [ -n "$TAIL_PID" ] && ps -p $TAIL_PID > /dev/null 2>&1; then
        echo -e "${BLUE}로그 출력 프로세스 종료 (PID: $TAIL_PID)${NC}"
        kill $TAIL_PID
    fi

    echo -e "${GREEN}서버가 종료되었습니다.${NC}"
    exit 0
}

# Ctrl+C 시그널 처리
trap cleanup SIGINT SIGTERM

# 로그 디렉토리 생성
mkdir -p logs

# 1. Backend 서버 시작 (uvicorn)
echo -e "${BLUE}[1/2] Backend 서버 시작 중...${NC}"
echo -e "${YELLOW}      포트: 8000${NC}"
echo -e "${YELLOW}      로그: $BACKEND_LOG${NC}"

# 가상환경 활성화 및 uvicorn 실행
source .venv/bin/activate
# FORCE_COLORS 환경변수 설정하여 파일 리다이렉트 시에도 컬러 유지
FORCE_COLORS=true ENVIRONMENT=local uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > "$BACKEND_LOG" 2>&1 &
BACKEND_PID_NUM=$!
echo $BACKEND_PID_NUM > "$BACKEND_PID"

echo -e "${GREEN}✓ Backend 서버 시작됨 (PID: $BACKEND_PID_NUM)${NC}"
sleep 2

# 2. Frontend 서버 시작
echo -e "${BLUE}[2/2] Frontend 서버 시작 중...${NC}"
echo -e "${YELLOW}      포트: 3000${NC}"
echo -e "${YELLOW}      로그: $FRONTEND_LOG${NC}"

cd frontend
npm run dev > "../$FRONTEND_LOG" 2>&1 &
FRONTEND_PID_NUM=$!
cd ..
echo $FRONTEND_PID_NUM > "$FRONTEND_PID"

echo -e "${GREEN}✓ Frontend 서버 시작됨 (PID: $FRONTEND_PID_NUM)${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  서버가 성공적으로 시작되었습니다!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${BLUE}Frontend: ${NC}http://localhost:3000"
echo -e "${BLUE}Backend:  ${NC}http://localhost:8000"
echo -e "${BLUE}API Docs: ${NC}http://localhost:8000/docs"

# 브라우저 열기 시도 (macOS, Linux 우선 처리)
OPEN_URL="http://localhost:3000"
if command -v open >/dev/null 2>&1; then
    open "$OPEN_URL"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$OPEN_URL" >/dev/null 2>&1 &
elif command -v start >/dev/null 2>&1; then
    start "$OPEN_URL"
else
    echo -e "${YELLOW}브라우저 자동 실행 실패: ${OPEN_URL}${NC}"
fi

# 로그 실시간 출력
echo -e "${BLUE}=== Backend 로그 ===${NC}"
tail -f "$BACKEND_LOG" &
TAIL_PID=$!

# 프로세스가 종료될 때까지 대기
wait
