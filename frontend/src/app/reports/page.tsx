'use client';

import { useEffect, useState } from 'react';
import { FileText, Download, RefreshCw } from 'lucide-react';
import { getReports, generateReport, getSettings } from '@/lib/api';
import { formatUnixTimestamp } from '@/utils/datetime';

interface Report {
  filename: string;
  size: number;
  created_at: number;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const fetchReports = async () => {
    try {
      const res = await getReports();
      setReports(res.reports);
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const settings = await getSettings();
      await generateReport(settings.search_start_date, settings.search_end_date);
      fetchReports();
    } catch (error) {
      console.error('Failed to generate report:', error);
      alert('Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  if (loading) {
    return <div className="text-center py-10">Loading...</div>;
  }

  const reportList = reports.map((report) => (
    <tr key={report.filename}>
      <td className="px-6 py-4">
        <div className="flex items-center gap-2">
          <FileText size={18} className="text-gray-400" />
          {report.filename}
        </div>
      </td>
      <td className="px-6 py-4 text-gray-500">
        {formatFileSize(report.size)}
      </td>
      <td className="px-6 py-4 text-gray-500">
        {formatUnixTimestamp(report.created_at)}
      </td>
      <td className="px-6 py-4 text-right">
        <a
          href={'/api/v1/reports/download/' + report.filename}
          download
          className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800"
        >
          <Download size={18} />
          Download
        </a>
      </td>
    </tr>
  ));

  const emptyRow = (
    <tr>
      <td colSpan={4} className="px-6 py-10 text-center text-gray-500">
        No reports found
      </td>
    </tr>
  );

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Reports</h1>
        <div className="flex gap-3">
          <button
            onClick={fetchReports}
            className="flex items-center gap-2 border px-4 py-2 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw size={18} />
            Refresh
          </button>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <FileText size={20} />
            {generating ? 'Generating...' : 'Generate Report'}
          </button>
        </div>
      </div>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">Filename</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">Size</th>
              <th className="px-6 py-3 text-left text-sm font-medium text-gray-500">Created</th>
              <th className="px-6 py-3 text-right text-sm font-medium text-gray-500">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {reports.length === 0 ? emptyRow : reportList}
          </tbody>
        </table>
      </div>
    </div>
  );
}