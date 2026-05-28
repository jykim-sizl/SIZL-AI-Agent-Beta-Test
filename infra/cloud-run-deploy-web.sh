#!/usr/bin/env bash
# Cloud Run 배포 (FE / Next.js standalone). 저장소 루트에서 실행:
#   bash infra/cloud-run-deploy-web.sh [BACKEND_URL]
# BACKEND_URL 생략 시 sizl-beta-api 서비스의 URL을 자동 조회해 사용.
set -euo pipefail

REGION="asia-northeast3"
SERVICE="sizl-beta-web"
API_SERVICE="sizl-beta-api"
PROJECT="$(gcloud config get-value project)"

# 1) 백엔드 URL 결정 (인자 우선, 없으면 동일 프로젝트의 api 서비스 URL 조회)
if [[ $# -ge 1 ]]; then
  API_URL="$1"
else
  API_URL="$(gcloud run services describe "$API_SERVICE" --region "$REGION" --format='value(status.url)')"
fi
echo "▶ 프로젝트: $PROJECT / 리전: $REGION"
echo "▶ NEXT_PUBLIC_API_URL = $API_URL"

# 2) Docker 이미지 빌드 (Cloud Build, 루트 컨텍스트)
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com >/dev/null
gcloud builds submit \
  --config infra/cloudbuild-web.yaml \
  --substitutions "_API_URL=${API_URL}" \
  .

IMAGE="gcr.io/${PROJECT}/sizl-beta-web:latest"
echo "✓ 이미지: $IMAGE"

# 3) Cloud Run 배포
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "NODE_ENV=production"

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
echo
echo "✅ FE 배포 완료: $URL"
echo "다음(수동):"
echo "  ① 백엔드 .env 의 CORS_ORIGINS 에 ${URL} 추가 후 백엔드 재배포(bash infra/cloud-run-deploy.sh)"
echo "  ② 브라우저로 ${URL} 접속 → 로그인 → 내 이슈에 실데이터 표시 확인"
