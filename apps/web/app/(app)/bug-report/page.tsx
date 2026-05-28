"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FormField, Input, Textarea, Select } from "@/components/ui/field";
import { Section } from "@/components/ui/section";
import { AttachmentsField, type Attachment } from "@/components/attachments-field";
import { ProgressStepper } from "@/components/progress-stepper";
import { BugIcon } from "@/components/icons";
import { detectEnv } from "@/lib/test-environment";
import { submitIssue, SubmitError } from "@/lib/api";
import { getUser } from "@/lib/auth";

const TEST_AREAS = [
  "Research agent",
  "Document agent",
  "Chat",
  "ETL",
  "Login",
  "기타",
] as const;

const SEVERITIES = [
  { value: "P1", label: "🔴 P1 (치명적)" },
  { value: "P2", label: "🟠 P2 (높음)" },
  { value: "P3", label: "🟡 P3 (보통)" },
  { value: "P4", label: "⚪ P4 (낮음)" },
] as const;

const FREQUENCIES = ["항상", "가끔", "드물게"] as const;

interface BugForm {
  title: string;
  testAccount: string;
  screenUrl: string;
  accessTime: string;
  testArea: string;
  testAreaEtc: string;
  severity: string;
  os: string;
  browser: string;
  device: string;
  network: string;
  detailedFeature: string;
  scenarioDescription: string;
  frequency: string;
  reproductionSteps: string[];
  expectedBehavior: string;
  actualBehavior: string;
  inputValue: string;
  actualOutput: string;
  expectedOutput: string;
  additionalComments: string;
}

const initialForm: BugForm = {
  title: "",
  testAccount: "",
  screenUrl: "",
  accessTime: "",
  testArea: "Research agent",
  testAreaEtc: "",
  severity: "P3",
  os: "",
  browser: "",
  device: "",
  network: "",
  detailedFeature: "",
  scenarioDescription: "",
  frequency: "항상",
  reproductionSteps: [""],
  expectedBehavior: "",
  actualBehavior: "",
  inputValue: "",
  actualOutput: "",
  expectedOutput: "",
  additionalComments: "",
};

const SECTIONS = [
  { id: "summary", title: "요약" },
  { id: "scenario", title: "테스트 시나리오" },
  { id: "reproduction", title: "재현 방법" },
  { id: "behavior", title: "예상 vs 실제 동작" },
  { id: "values", title: "입력/출력 값" },
  { id: "attachments", title: "첨부파일" },
  { id: "comments", title: "추가 의견" },
] as const;

// Date → datetime-local 입력값("YYYY-MM-DDTHH:mm", 로컬 시각 기준)
function toLocalInput(date: Date): string {
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

const ACCESS_SHORTCUTS = [
  { label: "방금", minutes: 0 },
  { label: "30분 전", minutes: 30 },
  { label: "1시간 전", minutes: 60 },
  { label: "2시간 전", minutes: 120 },
] as const;

export default function BugReportPage() {
  const router = useRouter();
  const [form, setForm] = useState<BugForm>(initialForm);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [errorLog, setErrorLog] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showPreview, setShowPreview] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const set = <K extends keyof BugForm>(key: K, value: BugForm[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  // #1 테스트 환경 자동 감지 + 접근 시간 현재 시각으로 기본 채움 (둘 다 수정 가능)
  useEffect(() => {
    setForm((f) => ({ ...f, ...detectEnv(), accessTime: toLocalInput(new Date()) }));
  }, []);

  const setAccessMinutesAgo = (minutes: number) =>
    set("accessTime", toLocalInput(new Date(Date.now() - minutes * 60000)));

  // 재현 단계
  const addStep = () => set("reproductionSteps", [...form.reproductionSteps, ""]);
  const updateStep = (i: number, v: string) => {
    const steps = [...form.reproductionSteps];
    steps[i] = v;
    set("reproductionSteps", steps);
  };
  const removeStep = (i: number) =>
    set("reproductionSteps", form.reproductionSteps.filter((_, idx) => idx !== i));

  // Enter → 다음 단계로(혹은 마지막이면 새 단계 추가) + 새 입력에 포커스.
  // (data-step 속성으로 input 식별; Input 컴포넌트가 ref 를 안 받아서 querySelector 사용)
  const focusStep = (i: number) =>
    requestAnimationFrame(() =>
      document.querySelector<HTMLInputElement>(`input[data-step="${i}"]`)?.focus(),
    );
  const onStepKeyDown = (i: number) => (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    const isLast = i === form.reproductionSteps.length - 1;
    if (isLast) {
      addStep();
      focusStep(i + 1);
    } else {
      focusStep(i + 1);
    }
  };

  const completed = useMemo<Record<string, boolean>>(
    () => ({
      summary: Boolean(form.title && form.screenUrl),
      scenario: Boolean(form.detailedFeature || form.scenarioDescription),
      reproduction: form.reproductionSteps.some((s) => s.trim()),
      behavior: Boolean(form.expectedBehavior && form.actualBehavior),
      values: Boolean(form.inputValue || form.actualOutput || form.expectedOutput),
      attachments: attachments.length > 0 || errorLog.trim().length > 0,
      comments: form.additionalComments.trim().length > 0,
    }),
    [form, attachments, errorLog],
  );

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.title.trim()) e.title = "제목을 입력해주세요.";
    if (!form.screenUrl.trim()) e.screenUrl = "발생 화면 URL을 입력해주세요.";
    else if (!/^https?:\/\//.test(form.screenUrl.trim()))
      e.screenUrl = "http(s):// 로 시작하는 URL을 입력해주세요.";
    if (form.testArea === "기타" && !form.testAreaEtc.trim())
      e.testAreaEtc = "테스트 영역을 직접 입력해주세요.";
    setErrors(e);
    const firstId = Object.keys(e)[0];
    if (firstId) {
      // 다음 paint 후 DOM 에 에러 메시지 렌더 → 첫 에러 필드로 스크롤·포커스.
      requestAnimationFrame(() => {
        const el = document.getElementById(firstId);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
          (el as HTMLInputElement).focus({ preventScroll: true });
        }
      });
      return false;
    }
    return true;
  };

  const handleSubmit = async () => {
    if (!validate()) {
      setShowPreview(false);
      return;
    }
    const user = getUser();
    if (!user) {
      setSubmitError("로그인이 필요합니다.");
      return;
    }
    const orUndef = (v: string) => (v.trim() ? v : undefined);
    // 백엔드 계약(camelCase) 에 맞춰 정리 — testArea→area, 빈 옵션 제외, 로그인 이메일=reporterEmail
    const payload = {
      reporterEmail: user.email,
      title: form.title.trim(),
      testAccount: orUndef(form.testAccount),
      screenUrl: form.screenUrl,
      accessTime: orUndef(form.accessTime),
      area: form.testArea === "기타" ? form.testAreaEtc : form.testArea,
      severity: form.severity,
      os: orUndef(form.os),
      browser: orUndef(form.browser),
      device: orUndef(form.device),
      network: orUndef(form.network),
      detailedFeature: orUndef(form.detailedFeature),
      scenarioDescription: orUndef(form.scenarioDescription),
      frequency: form.frequency,
      reproductionSteps: form.reproductionSteps.filter((s) => s.trim()),
      expectedBehavior: orUndef(form.expectedBehavior),
      actualBehavior: orUndef(form.actualBehavior),
      inputValue: orUndef(form.inputValue),
      actualOutput: orUndef(form.actualOutput),
      expectedOutput: orUndef(form.expectedOutput),
      additionalComments: orUndef(form.additionalComments),
      errorLog: orUndef(errorLog),
      attachments: attachments.map((a) => ({ name: a.name, dataUrl: a.dataUrl })),
    };
    setSubmitError("");
    setSubmitting(true);
    try {
      const { issueNumber } = await submitIssue(payload);
      router.push(`/submitted/${issueNumber}`);
    } catch (e) {
      setSubmitError(e instanceof SubmitError ? e.message : "제출 중 오류가 발생했습니다.");
      setShowPreview(false);
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-sizl-surface">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <header className="mb-6">
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <BugIcon className="h-6 w-6 text-red-600" />
            버그 신고
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            동작이 이상하거나 오류가 발생한 내용을 알려주세요.
          </p>
        </header>

        <div className="grid gap-8 lg:grid-cols-[1fr_280px]">
          <div className="flex flex-col gap-6">
            {/* 요약 */}
            <Section title="요약">
              <FormField label="제목" htmlFor="title" required error={errors.title} hint="한 줄로 어떤 문제인지 요약해주세요. GitHub 이슈/시트 목록에 그대로 표시됩니다.">
                <Input id="title" placeholder="예) 검색 결과가 간헐적으로 비어 있음" value={form.title} onChange={(e) => set("title", e.target.value)} />
              </FormField>

              <FormField label="테스트 계정 (이메일)" htmlFor="testAccount" hint="선택 · 테스트에 사용한 계정. 로그인 화면 테스트처럼 계정이 없으면 비워두세요. (제보자 본인 정보는 로그인에서 확인됩니다)">
                <Input id="testAccount" type="email" placeholder="test@company.com" value={form.testAccount} onChange={(e) => set("testAccount", e.target.value)} />
              </FormField>

              <FormField label="발생 화면 URL" htmlFor="screenUrl" required error={errors.screenUrl} hint="버그가 발생한 화면의 주소를 붙여넣어 주세요.">
                <Input id="screenUrl" type="url" placeholder="https://..." value={form.screenUrl} onChange={(e) => set("screenUrl", e.target.value)} />
              </FormField>

              <FormField label="접근 시간 (KST)" htmlFor="accessTime" hint="테스트한 시각입니다. 기본값은 현재 시각 — 실제 테스트 시각으로 조정해주세요.">
                <div className="flex flex-col gap-2">
                  <Input id="accessTime" type="datetime-local" value={form.accessTime} onChange={(e) => set("accessTime", e.target.value)} />
                  <div className="flex flex-wrap gap-2">
                    {ACCESS_SHORTCUTS.map((s) => (
                      <button
                        key={s.label}
                        type="button"
                        onClick={() => setAccessMinutesAgo(s.minutes)}
                        className="rounded-full border border-border bg-white px-3 py-1 text-xs text-gray-600 hover:bg-gray-50"
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>
              </FormField>

              <FormField label="테스트 영역" htmlFor="testArea" required>
                <Select id="testArea" value={form.testArea} onChange={(e) => set("testArea", e.target.value)}>
                  {TEST_AREAS.map((a) => (<option key={a} value={a}>{a}</option>))}
                </Select>
              </FormField>

              {form.testArea === "기타" && (
                <FormField label="테스트 영역 직접 입력" htmlFor="testAreaEtc" required error={errors.testAreaEtc}>
                  <Input id="testAreaEtc" placeholder="어떤 영역인지 입력해주세요" value={form.testAreaEtc} onChange={(e) => set("testAreaEtc", e.target.value)} />
                </FormField>
              )}

              <FormField label="심각도" required>
                <div className="flex flex-wrap gap-4">
                  {SEVERITIES.map((s) => (
                    <label key={s.value} className="flex cursor-pointer items-center gap-2">
                      <input type="radio" name="severity" value={s.value} checked={form.severity === s.value} onChange={(e) => set("severity", e.target.value)} className="h-4 w-4" />
                      <span className="text-sm">{s.label}</span>
                    </label>
                  ))}
                </div>
              </FormField>

              <div>
                <p className="mb-2 text-sm font-medium">테스트 환경 <span className="font-normal text-muted-foreground">(자동 감지됨 · 수정 가능)</span></p>
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                  <FormField label="OS" htmlFor="os"><Input id="os" value={form.os} onChange={(e) => set("os", e.target.value)} /></FormField>
                  <FormField label="브라우저" htmlFor="browser"><Input id="browser" value={form.browser} onChange={(e) => set("browser", e.target.value)} /></FormField>
                  <FormField label="기기" htmlFor="device"><Input id="device" value={form.device} onChange={(e) => set("device", e.target.value)} /></FormField>
                  <FormField label="네트워크" htmlFor="network"><Input id="network" value={form.network} onChange={(e) => set("network", e.target.value)} /></FormField>
                </div>
              </div>
            </Section>

            {/* 테스트 시나리오 */}
            <Section title="테스트 시나리오">
              <FormField label="상세 기능" htmlFor="detailedFeature"><Input id="detailedFeature" placeholder="테스트한 기능" value={form.detailedFeature} onChange={(e) => set("detailedFeature", e.target.value)} /></FormField>
              <FormField label="시나리오 설명" htmlFor="scenarioDescription"><Textarea id="scenarioDescription" rows={4} placeholder="테스트 시나리오를 설명해주세요..." value={form.scenarioDescription} onChange={(e) => set("scenarioDescription", e.target.value)} /></FormField>
            </Section>

            {/* 재현 방법 */}
            <Section title="재현 방법">
              <FormField label="재현 빈도" htmlFor="frequency">
                <Select id="frequency" value={form.frequency} onChange={(e) => set("frequency", e.target.value)}>
                  {FREQUENCIES.map((f) => (<option key={f} value={f}>{f}</option>))}
                </Select>
              </FormField>
              <div>
                <label className="mb-2 block text-sm font-medium">재현 단계</label>
                <div className="flex flex-col gap-2">
                  {form.reproductionSteps.map((step, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="w-6 pt-2 text-sm text-muted-foreground">{i + 1}.</span>
                      <Input
                        data-step={i}
                        placeholder="단계 설명 (Enter → 다음 단계)"
                        value={step}
                        onChange={(e) => updateStep(i, e.target.value)}
                        onKeyDown={onStepKeyDown(i)}
                      />
                      {form.reproductionSteps.length > 1 && (
                        <button type="button" onClick={() => removeStep(i)} className="rounded p-2 text-destructive hover:bg-destructive/10" aria-label="단계 삭제">✕</button>
                      )}
                    </div>
                  ))}
                </div>
                <Button type="button" variant="ghost" onClick={addStep} className="mt-2">+ 단계 추가</Button>
              </div>
            </Section>

            {/* 예상 vs 실제 */}
            <Section title="예상 vs 실제 동작">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField label="예상 동작" htmlFor="expectedBehavior"><Textarea id="expectedBehavior" rows={4} placeholder="어떻게 동작해야 하나요..." value={form.expectedBehavior} onChange={(e) => set("expectedBehavior", e.target.value)} /></FormField>
                <FormField label="실제 동작" htmlFor="actualBehavior"><Textarea id="actualBehavior" rows={4} placeholder="실제로 어떻게 동작했나요..." value={form.actualBehavior} onChange={(e) => set("actualBehavior", e.target.value)} /></FormField>
              </div>
            </Section>

            {/* 입력/출력 값 */}
            <Section title="입력/출력 값">
              <FormField label="입력 값" htmlFor="inputValue"><Textarea id="inputValue" rows={3} placeholder="입력 데이터..." value={form.inputValue} onChange={(e) => set("inputValue", e.target.value)} /></FormField>
              <FormField label="실제 출력" htmlFor="actualOutput"><Textarea id="actualOutput" rows={3} placeholder="실제 출력..." value={form.actualOutput} onChange={(e) => set("actualOutput", e.target.value)} /></FormField>
              <FormField label="예상 출력" htmlFor="expectedOutput"><Textarea id="expectedOutput" rows={3} placeholder="예상 출력..." value={form.expectedOutput} onChange={(e) => set("expectedOutput", e.target.value)} /></FormField>
            </Section>

            {/* 첨부파일 (+ 콘솔/에러 토글) */}
            <Section title="첨부파일">
              <AttachmentsField
                attachments={attachments}
                onAttachmentsChange={setAttachments}
                errorLog={errorLog}
                onErrorLogChange={setErrorLog}
              />
            </Section>

            {/* 추가 의견 */}
            <Section title="추가 의견">
              <Textarea rows={4} placeholder="추가로 전달할 내용이 있다면 적어주세요..." value={form.additionalComments} onChange={(e) => set("additionalComments", e.target.value)} />
            </Section>
          </div>

          {/* 진행 상황 (측면 스텝퍼, sticky) */}
          <ProgressStepper sections={SECTIONS} completed={completed} />
        </div>
      </div>

      {/* 하단 액션 바 */}
      <div className="sticky bottom-0 border-t border-border bg-white shadow-lg">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-6 py-4">
          <span className="text-sm text-destructive">{submitError}</span>
          <div className="flex gap-2">
            <Button variant="secondary" disabled={submitting} onClick={() => { if (validate()) setShowPreview(true); }}>미리보기</Button>
            <Button onClick={handleSubmit} disabled={submitting}>{submitting ? "제출 중..." : "제출하기"}</Button>
          </div>
        </div>
      </div>

      {/* 미리보기 모달 */}
      {showPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="max-h-[80vh] w-full max-w-2xl overflow-auto">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold">제출 내용 확인</h2>
                <p className="text-sm text-muted-foreground">GitHub Issue로 등록되기 전 확인해주세요.</p>
              </div>
              <button onClick={() => setShowPreview(false)} className="rounded p-2 hover:bg-gray-100" aria-label="닫기">✕</button>
            </div>
            <div className="mb-6 flex flex-col gap-2 rounded-lg bg-sizl-surface p-4 text-sm">
              <div><strong>제목:</strong> {form.title || "-"}</div>
              <div><strong>테스트 계정:</strong> {form.testAccount || "-"}</div>
              <div><strong>발생 화면:</strong> {form.screenUrl || "-"}</div>
              <div><strong>심각도:</strong> {SEVERITIES.find((s) => s.value === form.severity)?.label}</div>
              <div><strong>테스트 영역:</strong> {form.testArea === "기타" ? form.testAreaEtc : form.testArea}</div>
              <div><strong>첨부:</strong> {attachments.length}개{errorLog.trim() ? " · 로그 포함" : ""}</div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setShowPreview(false)} disabled={submitting}>수정하기</Button>
              <Button onClick={handleSubmit} disabled={submitting}>{submitting ? "제출 중..." : "제출 확정"}</Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
