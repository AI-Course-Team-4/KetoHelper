import { ReactNode } from 'react'
import { Navigation } from './Navigation'
import { Header } from './Header'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="h-screen bg-background flex flex-col">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Navigation />
        <main className="flex-1 p-6 overflow-auto" style={{ scrollbarGutter: 'stable' }}>
          {children}
        </main>
      </div>
    </div>
  )
}
