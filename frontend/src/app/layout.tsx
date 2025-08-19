import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import React from 'react'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AlphaStrat Trading Platform',
  description: 'AI-powered trading strategy discovery and validation system',
  icons: {
    icon: '/logos/favicon.ico',
    shortcut: '/logos/favicon.ico',
    apple: '/logos/alphastrat-logo-192.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}