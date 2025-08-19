import Image from 'next/image'
import Link from 'next/link'

interface LogoProps {
  className?: string
  width?: number
  height?: number
  showText?: boolean
}

export default function Logo({ 
  className = '', 
  width = 40, 
  height = 40,
  showText = true 
}: LogoProps) {
  return (
    <Link href="/" className={`flex items-center gap-2 ${className}`}>
      <Image
        src="/logos/alphastrat-logo.png"
        alt="AlphaStrat Logo"
        width={width}
        height={height}
        priority
        className="object-contain"
      />
      {showText && (
        <span className="text-xl font-bold bg-gradient-to-r from-blue-500 to-blue-700 bg-clip-text text-transparent">
          AlphaStrat
        </span>
      )}
    </Link>
  )
}