import { Header } from "@/components/Header";
import { UserProfileList } from "@/components/UserProfileList";

export const metadata = {
  title: "체험 프로필 | Fin-Guard AI",
};

export default function UserProfilePage() {
  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <p className="text-sm text-muted font-data">Fin-Guard AI 데모</p>
        <h1 className="mt-1 text-2xl font-semibold text-ink">체험 프로필</h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-ink/80">
          같은 상품이라도 유저의 자산·소비 데이터에 따라 AI 경고가 달라집니다. 아래 값은
          마이데이터 표준 API 규격의 목업(<span className="font-data">mydata_mock.json</span>)에서
          실시간으로 조회한 실제 데이터입니다.
        </p>

        <div className="mt-8">
          <UserProfileList />
        </div>
      </main>
    </div>
  );
}
