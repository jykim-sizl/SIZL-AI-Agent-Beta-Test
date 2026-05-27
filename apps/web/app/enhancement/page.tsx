"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { AREA_OPTIONS, enhancementSchema, type EnhancementForm } from "@/lib/schemas";
import { Field, inputClass, selectClass, textareaClass } from "@/components/form-ui";

export default function EnhancementPage() {
  const [submitted, setSubmitted] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<EnhancementForm>({
    resolver: zodResolver(enhancementSchema),
  });

  const onSubmit = (data: EnhancementForm) => {
    // W1: 백엔드 미연동 — 제출 JSON을 콘솔에 출력 (W2에서 POST /issues 연동)
    console.log("[enhancement] submit payload:", data);
    setSubmitted(JSON.stringify(data, null, 2));
  };

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold text-gray-900">✨ 개선 사항</h1>
        <p className="text-sm text-gray-600">더 편리하거나 강력해질 수 있는 아이디어를 제안해주세요.</p>
      </header>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" noValidate>
        <Field label="이메일" htmlFor="tester_email" required error={errors.tester_email?.message} hint="구성원 확인에 사용됩니다.">
          <input id="tester_email" type="email" placeholder="예- hong@sizl.co.kr" className={inputClass} {...register("tester_email")} />
        </Field>

        <Field label="관련 영역" htmlFor="area" required error={errors.area?.message}>
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

        <Field label="개선 제안 내용" htmlFor="description" required error={errors.description?.message} hint="현재 동작과 무엇이 아쉬운지 설명해주세요.">
          <textarea id="description" placeholder="현재 동작과 개선이 필요한 점을 적어주세요." className={textareaClass} {...register("description")} />
        </Field>

        <Field label="기대 동작" htmlFor="expected_behavior" required error={errors.expected_behavior?.message} hint="개선 후 어떻게 동작하길 기대하나요?">
          <textarea id="expected_behavior" placeholder="개선 후 기대하는 동작을 적어주세요." className={textareaClass} {...register("expected_behavior")} />
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
