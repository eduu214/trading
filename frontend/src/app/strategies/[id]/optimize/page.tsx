'use client';

import { ComplexityOptimizer } from '@/components/complexity/ComplexityOptimizer';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

export default function OptimizeStrategyPage() {
  const params = useParams();
  const strategyId = params.id as string;

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Navigation */}
      <div className="flex items-center gap-4">
        <Link href={`/strategies/${strategyId}`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Strategy
          </Button>
        </Link>
      </div>

      {/* Main Content */}
      <ComplexityOptimizer strategyId={strategyId} />
    </div>
  );
}