'use client'

import { createContext, useContext, useEffect, useState } from 'react'

const ThemeContext = createContext({
  isDark: false,
  toggleTheme: () => {},
})

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    // Ler cookie no carregamento
    const theme = document.cookie.match(/theme=(.+?)(;|$)/)?.[1]
    if (theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      setIsDark(true)
      document.documentElement.classList.add('dark')
    }
  }, [])

  const toggleTheme = () => {
    const newDark = !isDark
    setIsDark(newDark)
    if (newDark) {
      document.documentElement.classList.add('dark')
      document.cookie = "theme=dark; path=/; max-age=31536000"
    } else {
      document.documentElement.classList.remove('dark')
      document.cookie = "theme=light; path=/; max-age=31536000"
    }
  }

  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => useContext(ThemeContext)
