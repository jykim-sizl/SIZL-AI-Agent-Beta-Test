"use client";

import { useRef, useState, type Dispatch, type SetStateAction } from "react";
import { Textarea } from "@/components/ui/field";
import { FileIcon } from "@/components/icons";

export interface Attachment {
  name: string;
  type: string;
  size: number;
  dataUrl?: string; // 이미지 미리보기용 (이미지가 아닌 파일은 미설정)
}

const MAX = 5;

// 파일 다이얼로그 힌트 (모든 파일 허용하되 자주 쓰는 형식을 우선 노출)
const ACCEPT =
  "image/*,.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.csv,.md,.json,.log,.zip";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function AttachmentsField({
  attachments,
  onAttachmentsChange,
  errorLog = "",
  onErrorLogChange,
  showConsoleLog = true,
}: {
  attachments: Attachment[];
  onAttachmentsChange: Dispatch<SetStateAction<Attachment[]>>;
  errorLog?: string;
  onErrorLogChange?: (next: string) => void;
  showConsoleLog?: boolean;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showLog, setShowLog] = useState(false);

  const addFiles = (files: FileList | File[]) => {
    Array.from(files).forEach((file) => {
      const base: Attachment = { name: file.name, type: file.type, size: file.size };
      if (file.type.startsWith("image/")) {
        // 이미지는 썸네일용 data URL 로드
        const reader = new FileReader();
        reader.onload = () =>
          onAttachmentsChange((prev) =>
            prev.length >= MAX ? prev : [...prev, { ...base, dataUrl: String(reader.result) }],
          );
        reader.readAsDataURL(file);
      } else {
        // 그 외(PDF·문서 등)는 메타데이터만 보관
        onAttachmentsChange((prev) => (prev.length >= MAX ? prev : [...prev, base]));
      }
    });
  };

  const removeAt = (i: number) =>
    onAttachmentsChange((prev) => prev.filter((_, idx) => idx !== i));

  return (
    <div className="flex flex-col gap-4">
      <div
        tabIndex={0}
        onPaste={(e) => {
          const files = Array.from(e.clipboardData.files);
          if (files.length) {
            e.preventDefault();
            addFiles(files);
          }
        }}
        onClick={() => fileInputRef.current?.click()}
        onDrop={(e) => {
          e.preventDefault();
          addFiles(e.dataTransfer.files);
        }}
        onDragOver={(e) => e.preventDefault()}
        className="cursor-pointer rounded-lg border-2 border-dashed border-border p-8 text-center focus:border-primary focus:outline-none"
      >
        <p className="text-sm text-muted-foreground">
          이미지·PDF·문서 등을 드래그하거나 여기를 클릭, 또는 <strong>Ctrl+V</strong>로 붙여넣으세요
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          (최대 {MAX}개 · 이미지는 Ctrl+V 가능, 문서는 드래그/클릭으로 첨부)
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPT}
          multiple
          className="hidden"
          onChange={(e) => e.target.files && addFiles(e.target.files)}
        />
      </div>

      {attachments.length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          {attachments.map((a, i) => (
            <div key={i} className="relative overflow-hidden rounded-md border border-border">
              {a.dataUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={a.dataUrl} alt={a.name} className="h-24 w-full object-cover" />
              ) : (
                <div className="flex h-24 flex-col items-center justify-center gap-1 bg-gray-50 px-2 text-center">
                  <FileIcon className="h-7 w-7 text-muted-foreground" />
                  <span className="w-full truncate text-xs text-gray-700">{a.name}</span>
                </div>
              )}
              <span className="absolute bottom-0 left-0 right-0 bg-black/50 px-1 py-0.5 text-[10px] text-white">
                {formatSize(a.size)}
              </span>
              <button
                type="button"
                onClick={() => removeAt(i)}
                className="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-black/60 text-xs text-white"
                aria-label="첨부 삭제"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* 콘솔/에러 메시지 (선택, 토글) — showConsoleLog일 때만 */}
      {showConsoleLog && (
        <div>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={showLog}
              onChange={(e) => {
                setShowLog(e.target.checked);
                if (!e.target.checked) onErrorLogChange?.("");
              }}
              className="h-4 w-4"
            />
            콘솔 / 에러 메시지 직접 입력 (선택)
          </label>
          {showLog && (
            <Textarea
              className="mt-2 font-mono"
              rows={4}
              placeholder="콘솔 로그나 에러 메시지를 붙여넣어 주세요..."
              value={errorLog}
              onChange={(e) => onErrorLogChange?.(e.target.value)}
            />
          )}
        </div>
      )}
    </div>
  );
}
