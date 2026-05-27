"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  AREA_OPTIONS,
  SEVERITY_OPTIONS,
  bugReportSchema,
  type BugReportForm,
} from "@/lib/schemas";
import { detectTestEnvironment } from "@/lib/test-environment";
import { Field, inputClass, selectClass, textareaClass } from "@/components/form-ui";

export default function BugReportPage() {
  const [submitted, setSubmitted] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<BugReportForm>({
    resolver: zodResolver(bugReportSchema),
    defaultValues: { test_environment: "" },
  });

  // 테스트 환경은 브라우저에서 자동 채움 (사용자가 수정 가능)
  useEffect(() => {
    setValue("test_environment", detectTestEnvironment());
  }, [setValue]);

  const onSubmit = (data: BugReportForm) => {
    // 백엔드 BugReport(extra=forbid)에 맞춰 빈 선택 필드는 제거한다.
    const payload: Record<string, unknown> = { ...data };
    if (!payload.tester_name) delete payload.tester_name;
    if (!payload.image_url) delete payload.image_url;

    // W1: 백엔드 미연동 — 제출 JSON을 콘솔에 출력 (W2에서 POST /issues 연동)
    console.log("[bug-report] submit payload:", payload);
    setSubmitted(JSON.stringify(payload, null, 2));
  };

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold text-gray-900">🐞 버그 리포트</h1>
        <p className="text-sm text-gray-600">의도와 다르게 동작하거나 오류가 발생한 내용을 알려주세요.</p>
      </header>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" noValidate>
        <Field label="이메일" htmlFor="tester_email" required error={errors.tester_email?.message} hint="구성원 확인에 사용됩니다.">
          <input id="tester_email" type="email" placeholder="예- hong@sizl.co.kr" className={inputClass} {...register("tester_email")} />
        </Field>

        <Field label="이름" htmlFor="tester_name" error={errors.tester_name?.message} hint="선택 사항 (미입력 시 구성원 명단에서 자동 확인)">
          <input id="tester_name" type="text" placeholder="예- 홍길동" className={inputClass} {...register("tester_name")} />
        </Field>

        <Field label="테스트 영역" htmlFor="area" required error={errors.area?.message}>
          <select id="area" className={selectClass} defaultValue="" {...register("area")}>
            <option value="" disabled>
              선택해주세요
            </option>
            {AREA_OPTIONS.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </Field>

        <Field label="심각도" htmlFor="severity" required error={errors.severity?.message}>
          <select id="severity" className={selectClass} defaultValue="" {...register("severity")}>
            <option value="" disabled>
              선택해주세요
            </option>
            {SEVERITY_OPTIONS.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        </Field>

        <Field label="테스트 환경" htmlFor="test_environment" required error={errors.test_environment?.message} hint="브라우저 정보로 자동 채워집니다. 필요 시 수정하세요.">
          <input id="test_environment" type="text" className={inputClass} {...register("test_environment")} />
        </Field>

        <Field label="버그 설명" htmlFor="description" required error={errors.description?.message}>
          <textarea id="description" placeholder="어떤 상황에서 무엇이 잘못되었는지 설명해주세요." className={textareaClass} {...register("description")} />
        </Field>

        <Field label="재현 절차" htmlFor="reproduction_steps" required error={errors.reproduction_steps?.message}>
          <textarea id="reproduction_steps" placeholder={"1.\n2.\n3."} className={textareaClass} {...register("reproduction_steps")} />
        </Field>

        <Field label="이미지 URL" htmlFor="image_url" error={errors.image_url?.message} hint="선택 사항. 스크린샷 링크가 있다면 붙여넣어 주세요. (파일 업로드는 추후 지원)">
          <input id="image_url" type="url" placeholder="https://..." className={inputClass} {...register("image_url")} />
        </Field>

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-md bg-gray-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
        >
          제출
        </button>
      </form>

      {submitted && (
        <div className="flex flex-col gap-2 rounded-md border border-green-200 bg-green-50 p-4">
          <p className="text-sm font-medium text-green-800">제출되었습니다 (현재는 콘솔 출력 단계입니다)</p>
          <pre className="overflow-x-auto rounded bg-white p-3 text-xs text-gray-800">{submitted}</pre>
        </div>
      )}
    </div>
  );
}
