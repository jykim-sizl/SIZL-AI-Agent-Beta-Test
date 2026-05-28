#!/usr/bin/env bash
# Cloud Run 배포 (Phase B). 저장소 루트에서 실행: bash infra/cloud-run-deploy.sh
# 전제: gcloud 로그인 + 프로젝트(sizl-beta-test) 설정 완료.
# Members는 읽기전용(Secret Manager 마운트) — 자가등록은 Cloud Run에서 비활성.
set -euo pipefail

REGION="asia-northeast3"        # 서울
SERVICE="sizl-beta-api"
PROJECT="$(gcloud config get-value project)"
ENV_FILE="apps/api/.env"

# --- .env 로드 (값/시크릿 경로의 출처) ---
set -a; source "$ENV_FILE"; set +a
MEMBERS_FILE="apps/api/${MEMBERS_XLSX_PATH#apps/api/}"   # apps/api 기준 경로 → 루트 기준

echo "▶ 프로젝트: $PROJECT / 리전: $REGION"

# --- 1) API 활성화 ---
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com

# --- 2) 시크릿 생성(있으면 새 버전 추가) ---
create_secret() {  # $1=이름 $2=파일
  if gcloud secrets describe "$1" >/dev/null 2>&1; then
    gcloud secrets versions add "$1" --data-file="$2" >/dev/null
  else
    gcloud secrets create "$1" --data-file="$2" >/dev/null
  fi
  echo "  ✓ secret: $1"
}
create_secret sizl-app-pem "$GITHUB_APP_PRIVATE_KEY_PATH"
create_secret sizl-sa-json "$GOOGLE_SERVICE_ACCOUNT_JSON_PATH"
create_secret sizl-members "$MEMBERS_FILE"
printf '%s' "$GITHUB_WEBHOOK_SECRET" | gcloud secrets create sizl-webhook-secret --data-file=- 2>/dev/null \
  || printf '%s' "$GITHUB_WEBHOOK_SECRET" | gcloud secrets versions add sizl-webhook-secret --data-file=-
echo "  ✓ secret: sizl-webhook-secret"

# --- 3) 런타임 SA에 secretAccessor 부여 ---
PNUM="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"
RUNTIME_SA="${PNUM}-compute@developer.gserviceaccount.com"
for S in sizl-app-pem sizl-sa-json sizl-members sizl-webhook-secret; do
  gcloud secrets add-iam-policy-binding "$S" \
    --member="serviceAccount:${RUNTIME_SA}" \
    --role="roles/secretmanager.secretAccessor" >/dev/null
done
echo "  ✓ ${RUNTIME_SA} 에 secretAccessor 부여"

# --- 4) 배포 (Dockerfile 빌드 + 시크릿 마운트 + env) ---
gcloud run deploy "$SERVICE" \
  --source apps/api \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-secrets="/secrets/app/app.pem=sizl-app-pem:latest,/secrets/sa/sa.json=sizl-sa-json:latest,/secrets/members/Members.xlsx=sizl-members:latest,GITHUB_WEBHOOK_SECRET=sizl-webhook-secret:latest" \
  --set-env-vars="GITHUB_APP_ID=${GITHUB_APP_ID},GITHUB_APP_PRIVATE_KEY_PATH=/secrets/app/app.pem,GITHUB_ISSUE_REPO=${GITHUB_ISSUE_REPO:-jykim-sizl/SIZL-AI-Agent-Beta-Test},GITHUB_TARGET_REPO=${GITHUB_TARGET_REPO},GOOGLE_SERVICE_ACCOUNT_JSON_PATH=/secrets/sa/sa.json,GOOGLE_SPREADSHEET_ID=${GOOGLE_SPREADSHEET_ID},MEMBERS_XLSX_PATH=/secrets/members/Members.xlsx,ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY},SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL},CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:3000},APP_ENV=production,LOG_LEVEL=INFO"

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
echo
echo "✅ 배포 완료: $URL"
echo "다음(수동): ① GitHub App webhook URL → ${URL}/webhooks"
echo "          ② 프론트 .env.local: NEXT_PUBLIC_API_URL=${URL}"
echo "          ③ health 확인: curl ${URL}/health"
