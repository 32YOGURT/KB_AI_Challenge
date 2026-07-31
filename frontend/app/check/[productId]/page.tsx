import { CheckWorkspace } from "@/components/CheckWorkspace";

// 원문 PDF에 집중하는 전체 화면 뷰 — 공용 Header 대신 워크스페이스가 자체 툴바를 갖는다.
export default async function CheckPage({
  params,
}: {
  params: Promise<{ productId: string }>;
}) {
  const { productId } = await params;
  return <CheckWorkspace productId={productId} />;
}
