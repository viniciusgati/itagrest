import './globals.css'
import { Inter } from 'next/font/google'
import { ThemeProvider } from './theme-provider'
import { AuthGuard } from '@/components/AuthGuard'
import Sidebar from '@/components/Sidebar'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'iTagREST',
  description: 'Sistema Fiscal para Restaurantes',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-br">
      <body className={`${inter.className} transition-colors duration-300`}>
        <ThemeProvider>
          <AuthGuard>
            <div className="flex min-h-screen">
              <Sidebar />
              <main className="flex-1 min-w-0">
                {children}
              </main>
            </div>
          </AuthGuard>
        </ThemeProvider>
      </body>
    </html>
  )
}
