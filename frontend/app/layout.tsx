import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans_KR, Newsreader } from "next/font/google";
import { UserProvider } from "@/context/UserContext";
import "./globals.css";

const plexSans = IBM_Plex_Sans_KR({
  variable: "--font-portal",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const newsreader = Newsreader({
  variable: "--font-verdict",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  style: ["normal", "italic"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-utility",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "금융상품 한눈에 | 전국은행연합회 상품비교공시",
  description: "예금·적금·대출 상품을 한눈에 비교하세요.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body
        className={`${plexSans.variable} ${newsreader.variable} ${plexMono.variable} antialiased`}
      >
        <UserProvider>{children}</UserProvider>
      </body>
    </html>
  );
}
