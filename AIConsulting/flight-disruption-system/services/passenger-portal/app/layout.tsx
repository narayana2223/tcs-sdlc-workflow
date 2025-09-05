import './globals.css'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Flight Assistant - Your Travel Companion',
  description: 'AI-powered flight management and assistance for passengers',
  manifest: '/manifest.json',
  icons: {
    apple: '/icon-512x512.png',
  },
  themeColor: '#0ea5e9',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: 'cover',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="Flight Assistant" />
        <link rel="apple-touch-icon" href="/icon-512x512.png" />
      </head>
      <body className={`${inter.className} safe-top safe-bottom`}>
        <div className="min-h-screen bg-slate-50">
          {children}
        </div>
      </body>
    </html>
  )
}