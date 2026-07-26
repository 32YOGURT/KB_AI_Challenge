import { Header } from "@/components/Header";

export default async function RentHouseLoanDetailPage({
  params,
}: {
  params: Promise<{ finCoNo: string; finPrdtCd: string }>;
}) {
  const { finCoNo, finPrdtCd } = await params;

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-3xl px-6 py-10">
        {/* TODO: 전세자금대출 상세 정보 구현 */}
        <p className="text-sm text-muted font-data">
          {finCoNo} / {finPrdtCd}
        </p>
      </main>
    </div>
  );
}
