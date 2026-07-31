"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { presignDocument } from "@/lib/api";
import type { RiskBasis } from "@/lib/types";

// pdf.js는 브라우저 전용 API를 쓰므로 SSR을 건너뛴다.
const PdfDocument = dynamic(() => import("./PdfDocument"), {
  ssr: false,
  loading: () => <p className="p-8 text-center text-sm text-white/50 font-data">뷰어 준비 중…</p>,
});

// 배율 1 = 패널 폭에 맞춤. 그 이상은 패널이 스크롤된다.
// <Page width>는 PDF 원본 종횡비로 높이를 계산하므로 폭만 키워도 비율은 안 깨진다.
const ZOOM_STEPS = [1, 1.25, 1.5, 2, 2.5, 3];

const PILL_BUTTON =
  "rounded-full px-2.5 py-1 text-sm leading-none text-white/80 transition-colors hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-transparent";

function Stage({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-0 flex-1 items-center justify-center bg-[#4b5058] p-8">{children}</div>
  );
}

/**
 * 부모가 `key={basis.source_key}`로 문서가 바뀔 때만 리마운트시킨다. 같은 문서 안에서
 * 다른 조항을 고르면 presign/PDF 다운로드 없이 페이지만 이동한다.
 */
export function SourcePdfViewer({ basis }: { basis: RiskBasis | null }) {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [width, setWidth] = useState(0);
  // 수동으로 넘긴 페이지. 어느 근거를 보던 중이었는지 함께 들고 있다가, 다른 근거가
  // 선택되면 자동으로 무효가 되어 그 근거의 페이지로 돌아간다.
  const [override, setOverride] = useState<{ basis: RiskBasis; page: number } | null>(null);
  const [zoomStep, setZoomStep] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const sourceKey = basis?.source_key ?? "";

  useEffect(() => {
    if (!sourceKey) return;
    let cancelled = false;
    presignDocument(sourceKey)
      .then((doc) => !cancelled && setUrl(doc.url))
      .catch(() => !cancelled && setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [sourceKey]);

  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  if (!basis || !sourceKey) {
    return (
      <Stage>
        <p className="max-w-xs text-center text-sm leading-relaxed text-white/50">
          오른쪽 리포트에서 <span className="text-gold">근거 조항</span>을 누르면
          <br />
          약관 원문이 여기에 표시됩니다.
        </p>
      </Stage>
    );
  }

  if (failed) {
    return (
      <Stage>
        <p className="text-center text-sm text-white/70">
          원문 문서를 찾을 수 없습니다.
          <br />
          객체 스토리지에 해당 PDF가 있는지 확인해주세요.
        </p>
      </Stage>
    );
  }

  const pageNumber = override?.basis === basis ? override.page : (basis.page ?? 1);
  const goToPage = (page: number) => setOverride({ basis, page });
  const zoom = ZOOM_STEPS[zoomStep];
  // ResizeObserver의 contentRect는 padding을 제외한 폭이라 그대로 쓰면 된다.
  const pageWidth = Math.max(240, width * zoom);

  return (
    <div className="relative flex min-h-0 min-w-0 flex-1">
      <div ref={containerRef} className="flex-1 overflow-auto bg-[#4b5058] p-6">
        {url && width > 0 ? (
          <div className="mx-auto shadow-2xl" style={{ width: pageWidth }}>
            <PdfDocument
              url={url}
              pageNumber={pageNumber}
              clause={basis.clause}
              quote={basis.quote}
              width={pageWidth}
              onLoadSuccess={setNumPages}
            />
          </div>
        ) : (
          <p className="p-8 text-center text-sm text-white/50 font-data">원문 불러오는 중…</p>
        )}
      </div>

      {numPages !== null && (
        <div className="absolute bottom-5 left-1/2 z-10 flex -translate-x-1/2 items-center gap-1 rounded-full border border-white/10 bg-[#22262c]/95 px-2 py-1.5 shadow-xl backdrop-blur">
          <button
            onClick={() => goToPage(Math.max(1, pageNumber - 1))}
            disabled={pageNumber <= 1}
            className={PILL_BUTTON}
            aria-label="이전 페이지"
          >
            ◀
          </button>
          <span className="min-w-14 text-center text-xs text-white/60 font-data">
            {pageNumber} / {numPages}
          </span>
          <button
            onClick={() => goToPage(Math.min(numPages, pageNumber + 1))}
            disabled={pageNumber >= numPages}
            className={PILL_BUTTON}
            aria-label="다음 페이지"
          >
            ▶
          </button>

          <span className="mx-1 h-4 w-px bg-white/15" />

          <button
            onClick={() => setZoomStep((s) => Math.max(0, s - 1))}
            disabled={zoomStep === 0}
            className={PILL_BUTTON}
            aria-label="축소"
          >
            −
          </button>
          <span className="min-w-11 text-center text-xs text-white/60 font-data">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={() => setZoomStep((s) => Math.min(ZOOM_STEPS.length - 1, s + 1))}
            disabled={zoomStep === ZOOM_STEPS.length - 1}
            className={PILL_BUTTON}
            aria-label="확대"
          >
            +
          </button>
        </div>
      )}
    </div>
  );
}
