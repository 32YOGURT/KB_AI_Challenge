"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import type { PDFPageProxy, TextContent, TextItem } from "pdfjs-dist/types/src/display/api";
import type { PageViewport } from "pdfjs-dist/types/src/display/display_utils";
import "react-pdf/dist/Page/TextLayer.css";

// react-pdf 요구사항: workerSrc는 <Document>/<Page>를 쓰는 모듈과 같은 파일에서 설정해야
// 모듈 실행 순서 때문에 기본값으로 덮어써지지 않는다.
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

const REGEX_SPECIAL = /[.*+?^${}()|[\]\\]/g;

/**
 * 글자 사이에 공백을 허용하는 패턴. pdf.js는 텍스트를 "제"/" "/"1"/" "/"조" 처럼 잘게
 * 쪼개므로, 이어붙인 문자열에는 원본에 없던 공백이 섞여 들어온다.
 */
function toPattern(term: string): RegExp | null {
  const chars = [...term.replace(/\s+/g, "")];
  if (chars.length < 2) return null;
  return new RegExp(chars.map((c) => c.replace(REGEX_SPECIAL, "\\$&")).join("\\s*"), "gi");
}

// 임베딩 토큰 상한으로 조항이 쪼개지면 ingest가 clause_title 끝에 "(1/2)" 같은 접미사를
// 붙이는데, 이 문자열은 실제 PDF엔 없어서 그대로 검색하면 매치가 전부 실패한다.
function stripSplitSuffix(term: string): string {
  return term.replace(/\s*\(\d+\/\d+\)\s*$/, "");
}

function buildPatterns(rawQuery: string): RegExp[] {
  const query = stripSplitSuffix(rawQuery);
  // 조항 제목 전체가 안 잡히면 "제N조"만으로 재시도한다.
  const article = query.match(/제\s*\d+\s*조/)?.[0];
  return [toPattern(query), article && article !== query ? toPattern(article) : null].filter(
    (p): p is RegExp => p !== null,
  );
}

type Rect = { left: number; top: number; width: number; height: number };

/**
 * pdf.js는 텍스트를 아주 잘게(경우에 따라 글자 단위로) 쪼개 각 조각을 독립적으로
 * 배치한다. 조각마다 <mark>를 씌우는 방식으론 글자 사이 간격만큼 하이라이트가 끊겨
 * 보이므로, 대신 매치가 걸친 조각들의 실제 좌표(뷰포트 기준)를 모아 시작~끝을 잇는
 * 사각형 하나로 만든다. 한 페이지 안에서 검색어가 여러 번 나오면 매치마다 사각형을
 * 하나씩 만든다(여러 줄에 걸친 매치는 좌표를 통째로 감싸는 사각형 하나가 된다).
 */
function findMatchRects(items: TextContent["items"], query: string, viewport: PageViewport): Rect[] {
  const textItems: TextItem[] = [];
  const spans: { start: number; end: number; itemIndex: number }[] = [];
  let haystack = "";
  items.forEach((item) => {
    if (!("str" in item)) return;
    const itemIndex = textItems.length;
    textItems.push(item);
    spans.push({ start: haystack.length, end: haystack.length + item.str.length, itemIndex });
    haystack += item.str;
  });

  const rects: Rect[] = [];
  for (const pattern of buildPatterns(query)) {
    pattern.lastIndex = 0;
    let match: RegExpExecArray | null;
    let found = false;
    while ((match = pattern.exec(haystack)) !== null) {
      found = true;
      const start = match.index;
      const end = start + match[0].length;
      let left = Infinity;
      let top = Infinity;
      let right = -Infinity;
      let bottom = -Infinity;
      for (const span of spans) {
        if (span.end <= start || span.start >= end) continue;
        const item = textItems[span.itemIndex];
        const x1 = item.transform[4];
        const y1 = item.transform[5];
        const [vx1, vy1, vx2, vy2] = viewport.convertToViewportRectangle([
          x1,
          y1,
          x1 + item.width,
          y1 + item.height,
        ]);
        left = Math.min(left, vx1, vx2);
        right = Math.max(right, vx1, vx2);
        top = Math.min(top, vy1, vy2);
        bottom = Math.max(bottom, vy1, vy2);
      }
      if (Number.isFinite(left)) {
        rects.push({ left, top, width: right - left, height: bottom - top });
      }
      if (match[0].length === 0) pattern.lastIndex += 1;
    }
    if (found) break; // 더 구체적인 패턴이 걸렸으면 대체 패턴은 쓰지 않는다
  }
  return rects;
}

export default function PdfDocument({
  url,
  pageNumber,
  clause,
  quote,
  width,
  onLoadSuccess,
}: {
  url: string;
  pageNumber: number;
  clause: string;
  quote: string | null;
  width: number;
  onLoadSuccess: (numPages: number) => void;
}) {
  const [page, setPage] = useState<PDFPageProxy | null>(null);
  const [items, setItems] = useState<TextContent["items"] | null>(null);
  const [renderedPageNumber, setRenderedPageNumber] = useState(pageNumber);
  const firstRectRef = useRef<HTMLDivElement | null>(null);

  // 페이지가 바뀌면 이전 페이지의 좌표가 잠깐이라도 남아 엉뚱한 위치에 그려지지 않게 비운다.
  // (effect 대신 렌더 중 상태 조정 — https://react.dev/learn/you-might-not-need-an-effect)
  if (pageNumber !== renderedPageNumber) {
    setRenderedPageNumber(pageNumber);
    setPage(null);
    setItems(null);
  }

  const handlePageLoadSuccess = useCallback((loadedPage: PDFPageProxy) => {
    setPage(loadedPage);
  }, []);

  const handleGetTextSuccess = useCallback((textContent: TextContent) => {
    setItems(textContent.items);
  }, []);

  const rects = useMemo(() => {
    if (!page || !items) return [];
    const scale = width / page.getViewport({ scale: 1 }).width;
    const viewport = page.getViewport({ scale });
    return [
      ...findMatchRects(items, clause, viewport),
      ...(quote ? findMatchRects(items, quote, viewport) : []),
    ];
  }, [page, items, clause, quote, width]);

  useEffect(() => {
    if (rects.length === 0) return;
    // 오버레이 div는 rects가 바뀐 다음 렌더에야 DOM에 반영되므로 한 틱 미룬다.
    const id = requestAnimationFrame(() => {
      firstRectRef.current?.scrollIntoView({ block: "center", behavior: "smooth" });
    });
    return () => cancelAnimationFrame(id);
  }, [rects]);

  return (
    <Document
      file={url}
      onLoadSuccess={(doc) => onLoadSuccess(doc.numPages)}
      loading={<p className="p-8 text-center text-sm text-muted font-data">PDF 불러오는 중…</p>}
      error={<p className="p-8 text-center text-sm text-risk-red">PDF를 불러오지 못했습니다.</p>}
    >
      <div className="relative">
        <Page
          pageNumber={pageNumber}
          width={width}
          onLoadSuccess={handlePageLoadSuccess}
          onGetTextSuccess={handleGetTextSuccess}
          renderAnnotationLayer={false}
        />
        {rects.map((r, i) => (
          <div
            key={i}
            ref={i === 0 ? firstRectRef : undefined}
            className="pointer-events-none absolute rounded-sm"
            style={{
              left: r.left,
              top: r.top,
              width: r.width,
              height: r.height,
              backgroundColor: "color-mix(in srgb, var(--gold) 40%, transparent)",
            }}
          />
        ))}
      </div>
    </Document>
  );
}
