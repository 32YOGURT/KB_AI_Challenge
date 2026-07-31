"use client";

import { useCallback, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import type { TextContent } from "pdfjs-dist/types/src/display/api";
import "react-pdf/dist/Page/TextLayer.css";

// react-pdf 요구사항: workerSrc는 <Document>/<Page>를 쓰는 모듈과 같은 파일에서 설정해야
// 모듈 실행 순서 때문에 기본값으로 덮어써지지 않는다.
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

const REGEX_SPECIAL = /[.*+?^${}()|[\]\\]/g;

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * 글자 사이에 공백을 허용하는 패턴. pdf.js는 텍스트를 "제"/" "/"1"/" "/"조" 처럼 잘게
 * 쪼개므로, 이어붙인 문자열에는 원본에 없던 공백이 섞여 들어온다.
 */
function toPattern(term: string): RegExp | null {
  const chars = [...term.replace(/\s+/g, "")];
  if (chars.length < 2) return null;
  return new RegExp(chars.map((c) => c.replace(REGEX_SPECIAL, "\\$&")).join("\\s*"), "gi");
}

function buildPatterns(query: string): RegExp[] {
  // 조항 제목 전체가 안 잡히면 "제N조"만으로 재시도한다.
  const article = query.match(/제\s*\d+\s*조/)?.[0];
  return [toPattern(query), article && article !== query ? toPattern(article) : null].filter(
    (p): p is RegExp => p !== null,
  );
}

type Ranges = Map<number, [number, number][]>;

/**
 * 텍스트 아이템을 전부 이어붙여 검색한 뒤, 매치 구간을 다시 아이템별 로컬 오프셋으로
 * 되돌린다. customTextRenderer는 아이템 하나씩 호출되는데 조항 제목은 거의 항상 여러
 * 아이템에 걸쳐 있어서, 아이템 안에서만 찾으면 한 건도 못 맞춘다.
 */
function computeRanges(items: TextContent["items"], query: string): Ranges {
  const spans: { index: number; start: number; end: number }[] = [];
  let haystack = "";
  items.forEach((item, index) => {
    if (!("str" in item)) return;
    spans.push({ index, start: haystack.length, end: haystack.length + item.str.length });
    haystack += item.str;
  });

  const ranges: Ranges = new Map();
  for (const pattern of buildPatterns(query)) {
    pattern.lastIndex = 0;
    let match: RegExpExecArray | null;
    while ((match = pattern.exec(haystack)) !== null) {
      const start = match.index;
      const end = start + match[0].length;
      for (const span of spans) {
        if (span.end <= start || span.start >= end) continue;
        const local: [number, number] = [
          Math.max(span.start, start) - span.start,
          Math.min(span.end, end) - span.start,
        ];
        const existing = ranges.get(span.index);
        if (existing) existing.push(local);
        else ranges.set(span.index, [local]);
      }
      if (match[0].length === 0) pattern.lastIndex += 1;
    }
    if (ranges.size > 0) break; // 더 구체적인 패턴이 걸렸으면 대체 패턴은 쓰지 않는다
  }
  return ranges;
}

export default function PdfDocument({
  url,
  pageNumber,
  query,
  width,
  onLoadSuccess,
}: {
  url: string;
  pageNumber: number;
  query: string;
  width: number;
  onLoadSuccess: (numPages: number) => void;
}) {
  const [ranges, setRanges] = useState<Ranges>(new Map());

  const handleGetTextSuccess = useCallback(
    (textContent: TextContent) => {
      setRanges(query ? computeRanges(textContent.items, query) : new Map());
    },
    [query],
  );

  const customTextRenderer = useCallback(
    ({ str, itemIndex }: { str: string; itemIndex: number }) => {
      const local = ranges.get(itemIndex);
      if (!local) return escapeHtml(str);

      let out = "";
      let last = 0;
      for (const [start, end] of local) {
        out += escapeHtml(str.slice(last, start));
        out += `<mark>${escapeHtml(str.slice(start, end))}</mark>`;
        last = end;
      }
      return out + escapeHtml(str.slice(last));
    },
    [ranges],
  );

  const scrollToHighlight = useCallback(() => {
    document
      .querySelector(".react-pdf__Page__textContent mark")
      ?.scrollIntoView({ block: "center", behavior: "smooth" });
  }, []);

  return (
    <Document
      file={url}
      onLoadSuccess={(doc) => onLoadSuccess(doc.numPages)}
      loading={<p className="p-8 text-center text-sm text-muted font-data">PDF 불러오는 중…</p>}
      error={<p className="p-8 text-center text-sm text-risk-red">PDF를 불러오지 못했습니다.</p>}
    >
      <Page
        pageNumber={pageNumber}
        width={width}
        customTextRenderer={customTextRenderer}
        onGetTextSuccess={handleGetTextSuccess}
        onRenderTextLayerSuccess={scrollToHighlight}
        renderAnnotationLayer={false}
      />
    </Document>
  );
}
