import type { Metadata } from 'next'
import Link from 'next/link'
import { Public_Sans, Source_Serif_4 } from 'next/font/google'
import './globals.css'

const publicSans = Public_Sans({ subsets: ['latin'], variable: '--font-public-sans' })
const sourceSerif = Source_Serif_4({ subsets: ['latin'], variable: '--font-source-serif' })

export const metadata: Metadata = {
  title: 'ANOMALY: preços em compras públicas',
  description: 'Preços de compras públicas do RJ, como gasolina e papel A4, comparados com a referência estadual.',
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR" className={`${publicSans.variable} ${sourceSerif.variable}`}>
      <body className="min-h-dvh antialiased">
        <header className="border-b border-fio">
          <div className="mx-auto flex max-w-6xl items-baseline gap-4 px-5 py-4 sm:px-8">
            <Link href="/" className="text-lg font-bold tracking-tight no-underline">
              ANOMALY
            </Link>
            <p className="text-sm text-apoio">Existe algo estranho nesses dados?</p>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-5 pb-24 sm:px-8">{children}</main>
      </body>
    </html>
  )
}
