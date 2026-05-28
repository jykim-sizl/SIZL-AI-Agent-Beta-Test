import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Cloud Run 배포용: 빌드 산출물을 self-contained server.js + 최소 node_modules로 추림
  output: "standalone",
  // pnpm 모노레포: 추적 루트를 repo 루트로 잡아야 standalone이 워크스페이스 파일까지 포함
  outputFileTracingRoot: path.join(__dirname, "../../"),
};

export default nextConfig;
