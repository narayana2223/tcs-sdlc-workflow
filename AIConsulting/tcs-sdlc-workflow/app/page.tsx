import { Header } from '@/components/Header';
import { MaturitySelector } from '@/components/MaturitySelector';
import { A16ZWorkflowMap } from '@/components/A16ZWorkflowMap';
import { MetricsBar } from '@/components/MetricsBar';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <MaturitySelector />
      <div className="mx-auto py-6 px-4">
        <A16ZWorkflowMap />
      </div>
      <MetricsBar />
    </div>
  );
}
