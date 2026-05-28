# Next.js 15 (App Router) standalone → Cloud Run.
# 빌드 컨텍스트 = repo 루트 (pnpm-lock·workspace를 같이 봐야 하므로).
# 예: docker build -f apps/web/Dockerfile --build-arg NEXT_PUBLIC_API_URL=... -t web .
# 또는 cloudbuild-web.yaml 가 호출.
# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS base
RUN corepack enable
WORKDIR /repo

# 1) deps: 워크스페이스 파일만 먼저 복사해 install 캐시 살림
FROM base AS deps
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile --filter web...

# 2) builder: 소스 전체 복사 후 web만 빌드. NEXT_PUBLIC_* 는 빌드 시점에 인라인됨.
FROM base AS builder
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
COPY --from=deps /repo/node_modules ./node_modules
COPY --from=deps /repo/apps/web/node_modules ./apps/web/node_modules
COPY . .
WORKDIR /repo/apps/web
RUN pnpm build

# 3) runner: standalone 결과만 옮겨담아 가벼운 이미지로
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production HOSTNAME=0.0.0.0
# Cloud Run 은 $PORT(기본 8080)로 주입함. server.js 가 그대로 읽음.
ENV PORT=8080
# standalone 트리에는 next/server.js 와 필요한 node_modules 가 이미 포함되어 있음.
COPY --from=builder /repo/apps/web/.next/standalone ./
COPY --from=builder /repo/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder /repo/apps/web/public ./apps/web/public
EXPOSE 8080
CMD ["node", "apps/web/server.js"]
