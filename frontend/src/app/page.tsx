'use client';

import { useEffect, useState } from 'react';
import { Building2, FileText, PlayCircle, Clock, TrendingUp, Activity } from 'lucide-react';
import { getCompanies, getJobs, getArticles, getArticleAnalysisStats, getArticleAnalysisCoefficients } from '@/lib/api';
import { formatDate } from '@/utils/datetime';
import { ArticleAnalysisCoefficients } from '@/types';

export default function Dashboard() {
  const [stats, setStats] = useState({
    companies: 0,
    articles: 0,
    jobs: 0,
    lastRun: null as string | null,
    analysisCoefficient: 0,
  });
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState<ArticleAnalysisCoefficients | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        const [companiesRes, articlesRes, jobsRes, analysisRes, coefficientsRes] = await Promise.all([
          getCompanies(),
          getArticles(),
          getJobs(),
          getArticleAnalysisStats(),
          getArticleAnalysisCoefficients(),
        ]);

        const lastJob = jobsRes.items[0];

        setStats({
          companies: companiesRes.total,
          articles: articlesRes.total,
          jobs: jobsRes.total,
          lastRun: lastJob?.started_at || null,
          analysisCoefficient: analysisRes.coefficient,
        });
        setAnalysis(coefficientsRes);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400 flex flex-col items-center gap-3">
          <Activity className="animate-pulse" size={32} />
          <span className="text-sm">読み込み中...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">ダッシュボード</h1>
        <p className="text-sm text-gray-500 mt-1">システム全体の状況を確認できます</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Building2 size={20} />}
          label="登録企業"
          value={stats.companies}
          color="blue"
        />
        <StatCard
          icon={<FileText size={20} />}
          label="収集記事"
          value={stats.articles}
          color="emerald"
        />
        <StatCard
          icon={<PlayCircle size={20} />}
          label="実行回数"
          value={stats.jobs}
          color="purple"
        />
        <StatCard
          icon={<Clock size={20} />}
          label="最終実行"
          value={stats.lastRun ? formatDate(stats.lastRun) : '-'}
          isDate
        />
      </div>

      {analysis && (analysis.by_category.length > 0 || analysis.by_business_area.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <DataCard
            title="カテゴリ別"
            icon={<TrendingUp size={16} />}
            items={analysis.by_category.slice(0, 6)}
          />
          <DataCard
            title="業務領域別"
            icon={<TrendingUp size={16} />}
            items={analysis.by_business_area.slice(0, 6)}
          />
        </div>
      )}

      {analysis && analysis.by_month.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp size={16} className="text-blue-500" />
            時系列推移
          </h3>
          <TimelineChart items={analysis.by_month.slice(-12)} />
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color,
  isDate = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color?: 'blue' | 'emerald' | 'purple';
  isDate?: boolean;
}) {
  const iconColors = {
    blue: 'text-blue-600 bg-blue-50',
    emerald: 'text-emerald-600 bg-emerald-50',
    purple: 'text-purple-600 bg-purple-50',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-xs text-gray-500 font-medium mb-3">{label}</p>
          <p className={`${isDate ? 'text-lg' : 'text-2xl'} font-bold text-gray-900`}>
            {value}
          </p>
        </div>
        {color && (
          <div className={`p-2 rounded-lg ${iconColors[color]}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

function DataCard({
  title,
  icon,
  items,
}: {
  title: string;
  icon: React.ReactNode;
  items: { label: string; count: number }[];
}) {
  const maxValue = Math.max(...items.map((item) => item.count), 1);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <span className="text-blue-500">{icon}</span>
        {title}
      </h3>
      {items.length === 0 ? (
        <div className="text-sm text-gray-400 text-center py-8">データなし</div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.label}>
              <div className="flex justify-between items-baseline mb-1.5">
                <span className="text-sm text-gray-700 truncate">{item.label}</span>
                <span className="text-sm font-semibold text-gray-900 ml-3">{item.count}</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${(item.count / maxValue) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TimelineChart({
  items,
}: {
  items: { period: string; count: number }[];
}) {
  if (items.length === 0) {
    return <div className="text-sm text-gray-400 text-center py-8">データなし</div>;
  }

  const maxValue = Math.max(...items.map((item) => item.count), 1);

  return (
    <div>
      <div className="flex items-end justify-between h-48 gap-2 pb-12">
        {items.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center justify-end h-full group relative">
            <div className="w-full h-full flex items-end">
              <div
                className="w-full bg-blue-500 rounded-t hover:bg-blue-600 transition-all cursor-pointer"
                style={{ height: `${(item.count / maxValue) * 100}%` }}
              >
                <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded whitespace-nowrap transition-opacity z-10">
                  {item.count}件
                </div>
              </div>
            </div>
            <div className="absolute top-full mt-3 left-1/2 -translate-x-1/2 text-[10px] font-semibold text-gray-900 transform -rotate-45 whitespace-nowrap" style={{ textShadow: '0 0 3px white, 0 0 3px white, 0 0 3px white' }}>
              {item.period}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
