import { z } from "zod";

// 폼 필드는 백엔드 Pydantic 모델(BugReport / EnhancementRequest)을 그대로 미러링한다.
// 두 모델 모두 extra=forbid 이므로 제출 JSON은 정확히 아래 필드만 포함해야 한다.
// (참고: GitHub 이슈 템플릿은 더 많은 필드를 갖지만, 현재 백엔드 계약은 이 축소 집합이다.)

export const AREA_OPTIONS = ["Research agent", "Document agent", "기타"] as const;
export const SEVERITY_OPTIONS = ["P1", "P2", "P3", "P4"] as const;

// BugReport: tester_email, tester_name?, area, severity, test_environment,
//            description, reproduction_steps, image_url?
export const bugReportSchema = z.object({
  tester_email: z.email("올바른 이메일 형식이 아닙니다"),
  tester_name: z.string().trim().optional(),
  area: z.enum(AREA_OPTIONS, { error: "영역을 선택해주세요" }),
  severity: z.enum(SEVERITY_OPTIONS, { error: "심각도를 선택해주세요" }),
  test_environment: z.string().trim().min(1, "테스트 환경을 입력해주세요"),
  description: z.string().trim().min(1, "버그 설명을 입력해주세요"),
  reproduction_steps: z.string().trim().min(1, "재현 절차를 입력해주세요"),
  image_url: z.union([z.url("올바른 URL 형식이 아닙니다"), z.literal("")]).optional(),
});
export type BugReportForm = z.infer<typeof bugReportSchema>;

// EnhancementRequest: tester_email, area, description, expected_behavior
export const enhancementSchema = z.object({
  tester_email: z.email("올바른 이메일 형식이 아닙니다"),
  area: z.enum(AREA_OPTIONS, { error: "영역을 선택해주세요" }),
  description: z.string().trim().min(1, "개선 제안 내용을 입력해주세요"),
  expected_behavior: z.string().trim().min(1, "기대 동작을 입력해주세요"),
});
export type EnhancementForm = z.infer<typeof enhancementSchema>;
