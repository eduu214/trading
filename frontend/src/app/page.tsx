import Link from 'next/link';
import Logo from '@/components/Logo';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <Logo width={80} height={80} showText={false} />
          </div>
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-4">
            AlphaStrat Trading Platform
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            AI-Powered Market Intelligence & Automated Trading
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <Link href="/scanner" className="transform hover:scale-105 transition-transform">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 h-full cursor-pointer hover:shadow-xl">
              <div className="text-3xl mb-4">🔍</div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Market Scanner
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                Discover opportunities across equities, futures, and forex markets
              </p>
            </div>
          </Link>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 opacity-75">
            <div className="text-3xl mb-4">🤖</div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              AI Strategy Engine
            </h2>
            <p className="text-gray-600 dark:text-gray-300">
              Generate and backtest trading strategies with machine learning
            </p>
            <p className="text-sm text-gray-500 mt-2">Coming Soon</p>
          </div>
          
          <Link href="/portfolio" className="transform hover:scale-105 transition-transform">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 h-full cursor-pointer hover:shadow-xl">
              <div className="text-3xl mb-4">📊</div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Portfolio Management
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                Monitor and optimize your portfolio with correlation analysis
              </p>
            </div>
          </Link>
        </div>
        
        <div className="text-center mt-12">
          <Link href="/scanner">
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg transition-colors">
              Launch Scanner
            </button>
          </Link>
        </div>

        <div className="mt-8 text-center space-x-4">
          <a 
            href="http://localhost:8000/docs" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
          >
            API Documentation →
          </a>
        </div>
      </div>
    </main>
  )
}