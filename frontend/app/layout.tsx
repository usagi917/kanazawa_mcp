import type { Metadata } from 'next'
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: '金沢市なんでもチャット',
  description: '金沢市の観光情報、交通情報、ごみ収集情報を簡単に検索できるチャットボットアプリです',
  keywords: ['金沢市', 'チャット', '観光', '交通', 'ごみ収集'],
  authors: [{ name: 'Kanazawa City' }],
  viewport: 'width=device-width, initial-scale=1',
  robots: 'index, follow',
  openGraph: {
    title: '金沢市なんでもチャット',
    description: '金沢市の観光情報、交通情報、ごみ収集情報を簡単に検索できるチャットボットアプリです',
    type: 'website',
    locale: 'ja_JP',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
} 