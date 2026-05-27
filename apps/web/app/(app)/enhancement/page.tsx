"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FormField, Input, Textarea, Select } from "@/components/ui/field";
import { Section } from "@/components/ui/section";
import { AttachmentsField, type Attachment } from "@/components/attachments-field";
import { ProgressStepper } from "@/components/progress-stepper";
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

const PRIORITIES = [
  { value: "P1", label: "🔴 P1 (매우 높음)" },
  { value: "P2", label: "🟠 P2 (높음)" },
  { value: "P3", label: "🟡 P3 (보통)" },
  { value: "P4", label: "⚪ P4 (낮음)" },
] as const;

interface EnhForm {
  testAccount: string;
  screenUrl: string;
  testArea: string;
  testAreaEtc: string;
  priority: string;
  os: string;
  browser: string;
  device: string;
  network: string;
  featureToImprove: string;
  currentBehavior: string;
  expectedBehavior: string;
  rationale: string;
  additionalComments: string;
}

const initialForm: EnhForm = {
  testAccount: "",
  screenUrl: "",
  testArea: "Research agent",
  testAreaEtc: "",
  priority: "P3",
  os: "",
  browser: "",
  device: "",
  network: "",
  featureToImprove: "",
  currentBehavior: "",
  expectedBehavior: "",
  rationale: "",
  additionalComments: "",
};

const SECTIONS = [
  { id: "summary", title: "요약" },
  { id: "improvement", title: "개선 요청" },
  { id: "impact", title: "기대 효과" },
  { id: "attachments", title: "첨부파일" },
  { id: "comments", title: "추가 의견" },
] as const;

export default function EnhancementPage() {
  const router = useRouter();
  const [form, setForm] = useState<EnhForm>(initialForm);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showPreview, setShowPreview] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const set = <K extends keyof EnhForm>(key: K, value: EnhForm[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  useEffect(() => {
    setForm((f) => ({ ...f, ...detectEnv() }));
  }, []);

  const completed = useMemo<Record<string, boolean>>(
    () => ({
      summary: Boolean(form.screenUrl),
      improvement: Boolean(form.featureToImprove || form.currentBehavior || form.expectedBehavior),
      impact: form.rationale.trim().length > 0,
      attachments: attachments.length > 0,
      comments: form.additionalComments.trim().length > 0,
    }),
    [form, attachments],
  );

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.screenUrl.trim()) e.screenUrl = "관련 화면 URL을 입력해주세요.";
    else if (!/^https?:\/\//.test(form.screenUrl.trim()))
      e.screenUrl = "http(s):// 로 시작하는 URL을 입력해주세요.";
    if (form.testArea === "기타" && !form.testAreaEtc.trim())
      e.testAreaEtc = "관련 영역을 직접 입력해주세요.";
    if (!form.featureToImprove.trim()) e.featureToImprove = "개선할 기능을 입력해주세요.";
    setErrors(e);
    return Object.keys(e).length === 0;
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
    const payload = {
      reporterEmail: user.email,
      testAccount: orUndef(form.testAccount),
      screenUrl: form.screenUrl,
      area: form.testArea === "기타" ? form.testAreaEtc : form.testArea,
      priority: form.priority,
      os: orUndef(form.os),
      browser: orUndef(form.browser),
      device: orUndef(form.device),
      network: orUndef(form.network),
      featureToImprove: form.featureToImprove,
      currentBehavior: orUndef(form.currentBehavior),
      expectedBehavior: orUndef(form.expectedBehavior),
      rationale: orUndef(form.rationale),
      additionalComments: orUndef(form.additionalComments),
      attachments: attachments.map((a) => a.name),
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
          <h1 className="text-2xl font-bold">✨ 개선 의견</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            더 나은 기능이나 사용 경험을 제안해주세요.
          </p>
        </header>

        <div className="grid gap-8 lg:grid-cols-[1fr_280px]">
          <div className="flex flex-col gap-6">
            {/* 요약 */}
            <Section title="요약">
              <FormField label="테스트 계정 (이메일)" htmlFor="testAccount" hint="선택 · 테스트에 사용한 계정. 로그인 화면처럼 계정이 없으면 비워두세요. (제보자 본인 정보는 로그인에서 확인됩니다)">
                <Input id="testAccount" type="email" placeholder="test@company.com" value={form.testAccount} onChange={(e) => set("testAccount", e.target.value)} />
              </FormField>

              <FormField label="관련 화면 URL" htmlFor="screenUrl" required error={errors.screenUrl} hint="개선이 필요한 화면의 주소를 붙여넣어 주세요.">
                <Input id="screenUrl" type="url" placeholder="https://..." value={form.screenUrl} onChange={(e) => set("screenUrl", e.target.value)} />
              </FormField>

              <FormField label="관련 영역" htmlFor="testArea" required>
                <Select id="testArea" value={form.testArea} onChange={(e) => set("testArea", e.target.value)}>
                  {TEST_AREAS.map((a) => (<option key={a} value={a}>{a}</option>))}
                </Select>
              </FormField>

              {form.testArea === "기타" && (
                <FormField label="영역 직접 입력" htmlFor="testAreaEtc" required error={errors.testAreaEtc}>
                  <Input id="testAreaEtc" placeholder="어떤 영역인지 입력해주세요" value={form.testAreaEtc} onChange={(e) => set("testAreaEtc", e.target.value)} />
                </FormField>
              )}

              <FormField label="우선순위" required>
                <div className="flex flex-wrap gap-4">
                  {PRIORITIES.map((p) => (
                    <label key={p.value} className="flex cursor-pointer items-center gap-2">
                      <input type="radio" name="priority" value={p.value} checked={form.priority === p.value} onChange={(e) => set("priority", e.target.value)} className="h-4 w-4" />
                      <span className="text-sm">{p.label}</span>
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

            {/* 개선 요청 */}
            <Section title="개선 요청">
              <FormField label="개선할 기능" htmlFor="featureToImprove" required error={errors.featureToImprove}>
                <Input id="featureToImprove" placeholder="개선이 필요한 기능" value={form.featureToImprove} onChange={(e) => set("featureToImprove", e.target.value)} />
              </FormField>
              <FormField label="현재 동작" htmlFor="currentBehavior">
                <Textarea id="currentBehavior" rows={3} placeholder="지금은 어떻게 동작하나요..." value={form.currentBehavior} onChange={(e) => set("currentBehavior", e.target.value)} />
              </FormField>
              <FormField label="기대 동작 (개선 후)" htmlFor="expectedBehavior">
                <Textarea id="expectedBehavior" rows={3} placeholder="어떻게 바뀌면 좋을까요..." value={form.expectedBehavior} onChange={(e) => set("expectedBehavior", e.target.value)} />
              </FormField>
            </Section>

            {/* 기대 효과 */}
            <Section title="기대 효과">
              <FormField label="개선 시 기대 효과" htmlFor="rationale">
                <Textarea id="rationale" rows={4} placeholder="이 개선이 왜 필요하고 어떤 효과가 있을지 적어주세요..." value={form.rationale} onChange={(e) => set("rationale", e.target.value)} />
              </FormField>
            </Section>

            {/* 첨부파일 */}
            <Section title="첨부파일">
              <AttachmentsField
                attachments={attachments}
                onAttachmentsChange={setAttachments}
                showConsoleLog={false}
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
              <div><strong>테스트 계정:</strong> {form.testAccount || "-"}</div>
              <div><strong>관련 화면:</strong> {form.screenUrl || "-"}</div>
              <div><strong>우선순위:</strong> {form.priority}</div>
              <div><strong>관련 영역:</strong> {form.testArea === "기타" ? form.testAreaEtc : form.testArea}</div>
              <div><strong>개선할 기능:</strong> {form.featureToImprove || "-"}</div>
              <div><strong>첨부:</strong> {attachments.length}개</div>
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
