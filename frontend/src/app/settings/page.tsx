'use client';

import { useEffect, useState } from 'react';
import { Save, Clock, Search as SearchIcon, Building2, Plus, X, FileText } from 'lucide-react';
import {
  getSettings,
  updateSettings,
  getGlobalSearchSettings,
  updateGlobalSearchSettings,
  getCompanies,
  getCompanySearchSettings,
  updateCompanySearchSettings,
  deleteCompanySearchSettings,
  getPrompts,
  getRegionKeywords,
} from '@/lib/api';

interface GlobalSearchSettings {
  id?: number;
  default_region: string | null;
}

interface CompanySearchSettings {
  id?: number;
  company_name: string;
  region: string | null;
  custom_keywords: string[] | null;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'schedule' | 'search-global' | 'search-company' | 'prompts'>('schedule');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  // Prompts data
  const [promptsData, setPromptsData] = useState<any>(null);

  // Schedule settings
  const [scheduleData, setScheduleData] = useState({
    schedule_type: 'weekly',
    schedule_day: 1,
    schedule_hour: 9,
  });
  const [periodInput, setPeriodInput] = useState('1m');

  // Global search settings
  const [globalSearchSettings, setGlobalSearchSettings] = useState<GlobalSearchSettings>({
    default_region: null,
  });
  const [regionKeywords, setRegionKeywords] = useState<string[]>([]);

  // Company search settings
  const [companies, setCompanies] = useState<any[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [companySearchSettings, setCompanySearchSettings] = useState<CompanySearchSettings | null>(null);
  const [companyKeywordInput, setCompanyKeywordInput] = useState('');

  const toDateInput = (value: Date) => value.toISOString().split('T')[0];

  const getPresetRange = (preset: string) => {
    const today = new Date();
    const start = new Date(today);
    switch (preset) {
      case '1d':
        start.setDate(today.getDate() - 1);
        break;
      case '1w':
        start.setDate(today.getDate() - 7);
        break;
      case '1m':
        start.setMonth(today.getMonth() - 1);
        break;
      case '1y':
        start.setFullYear(today.getFullYear() - 1);
        break;
      default:
        return null;
    }
    return {
      start: toDateInput(start),
      end: toDateInput(today),
    };
  };

  const detectPreset = (start: string, end: string) => {
    const today = new Date();
    if (end !== toDateInput(today)) {
      return null;
    }
    const presets = ['1d', '1w', '1m', '1y'];
    for (const preset of presets) {
      const range = getPresetRange(preset);
      if (range && range.start === start && range.end === end) {
        return preset;
      }
    }
    return null;
  };

  useEffect(() => {
    async function fetchData() {
      try {
        const [settingsData, searchSettingsData, companiesData, promptsDataRes] = await Promise.all([
          getSettings(),
          getGlobalSearchSettings(),
          getCompanies(),
          getPrompts(),
        ]);

        const nextSchedule = {
          schedule_type: settingsData.schedule_type,
          schedule_day: settingsData.schedule_day,
          schedule_hour: settingsData.schedule_hour,
        };
        setScheduleData(nextSchedule);
        const detected = detectPreset(settingsData.search_start_date, settingsData.search_end_date);
        setPeriodInput(detected || '1m');

        setGlobalSearchSettings(searchSettingsData);
        setCompanies(companiesData.items || []);
        setPromptsData(promptsDataRes);

        // Load keywords for the default region
        const region = searchSettingsData.default_region || 'global';
        const keywordsData = await getRegionKeywords(region);
        setRegionKeywords(keywordsData.keywords);
      } catch (error) {
        console.error('Failed to load settings:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleSaveSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');

    try {
      const range = getPresetRange(periodInput.trim());
      if (!range) {
        setMessage('期間は 1y / 1m / 1w / 1d のいずれかで入力してください');
        return;
      }
      await updateSettings({
        search_start_date: range.start,
        search_end_date: range.end,
        ...scheduleData,
      });
      setMessage('スケジュール設定を保存しました');
    } catch (error) {
      console.error('Failed to save settings:', error);
      setMessage('保存に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveGlobalSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');

    try {
      await updateGlobalSearchSettings(globalSearchSettings);
      setMessage('グローバル検索設定を保存しました');
    } catch (error) {
      console.error('Failed to save global search settings:', error);
      setMessage('保存に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const handleRegionChange = async (newRegion: string | null) => {
    setGlobalSearchSettings({
      ...globalSearchSettings,
      default_region: newRegion,
    });

    // Load keywords for new region
    try {
      const region = newRegion || 'global';
      const keywordsData = await getRegionKeywords(region);
      setRegionKeywords(keywordsData.keywords);
    } catch (error) {
      console.error('Failed to load keywords for region:', error);
    }
  };

  const loadCompanySettings = async (companyName: string) => {
    if (!companyName) return;

    try {
      const data = await getCompanySearchSettings(companyName);
      setCompanySearchSettings(data);
    } catch (error) {
      setCompanySearchSettings({
        company_name: companyName,
        region: null,
        custom_keywords: null,
      });
    }
  };

  const handleCompanyChange = (companyName: string) => {
    setSelectedCompany(companyName);
    loadCompanySettings(companyName);
  };

  const handleSaveCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!companySearchSettings) return;

    setSaving(true);
    setMessage('');

    try {
      await updateCompanySearchSettings(companySearchSettings.company_name, {
        region: companySearchSettings.region || null,
        custom_keywords: companySearchSettings.custom_keywords || null,
      });
      setMessage('企業別検索設定を保存しました');
      // 保存後に設定を再読み込み
      await loadCompanySettings(companySearchSettings.company_name);
    } catch (error) {
      console.error('Failed to save company search settings:', error);
      setMessage('保存に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCompany = async () => {
    if (!companySearchSettings || !confirm('この企業の検索設定を削除しますか？')) return;

    setSaving(true);
    setMessage('');

    try {
      await deleteCompanySearchSettings(companySearchSettings.company_name);
      setMessage('企業別検索設定を削除しました');
      setCompanySearchSettings({
        company_name: companySearchSettings.company_name,
        region: null,
        custom_keywords: null,
      });
    } catch (error) {
      console.error('Failed to delete company search settings:', error);
      setMessage('削除に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const addCompanyKeyword = () => {
    const trimmed = companyKeywordInput.trim();
    if (!companySearchSettings) return;

    const currentKeywords = companySearchSettings.custom_keywords || [];
    if (trimmed && !currentKeywords.includes(trimmed)) {
      setCompanySearchSettings({
        ...companySearchSettings,
        custom_keywords: [...currentKeywords, trimmed],
      });
      setCompanyKeywordInput('');
    }
  };

  const removeCompanyKeyword = (index: number) => {
    if (!companySearchSettings) return;
    const keywords = companySearchSettings.custom_keywords || [];
    setCompanySearchSettings({
      ...companySearchSettings,
      custom_keywords: keywords.filter((_, i) => i !== index),
    });
  };

  if (loading) {
    return <div className="text-center py-10">読み込み中...</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">設定</h1>

      <div className="mb-4 flex gap-2">
        <button
          onClick={() => setActiveTab('schedule')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
            activeTab === 'schedule'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          <Clock size={20} />
          スケジュール
        </button>
        <button
          onClick={() => setActiveTab('search-global')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
            activeTab === 'search-global'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          <SearchIcon size={20} />
          検索設定
        </button>
        <button
          onClick={() => setActiveTab('search-company')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
            activeTab === 'search-company'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          <Building2 size={20} />
          企業別検索
        </button>
        <button
          onClick={() => setActiveTab('prompts')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
            activeTab === 'prompts'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          <FileText size={20} />
          記事分析設定
        </button>
      </div>

      {activeTab === 'schedule' && (
        <div className="bg-white rounded-lg shadow p-6 max-w-2xl">
          <form onSubmit={handleSaveSchedule} className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold mb-4">検索期間</h2>
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">期間</label>
                  <select
                    value={periodInput}
                    onChange={(e) => setPeriodInput(e.target.value)}
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value="1y">直近1年</option>
                    <option value="1m">直近1ヶ月</option>
                    <option value="1w">直近1週間</option>
                    <option value="1d">直近1日</option>
                  </select>
                </div>
              </div>
            </div>

            <div>
              <h2 className="text-lg font-semibold mb-4">スケジュール設定</h2>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">実行頻度</label>
                  <select
                    value={scheduleData.schedule_type}
                    onChange={(e) =>
                      setScheduleData({ ...scheduleData, schedule_type: e.target.value })
                    }
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    <option value="daily">毎日</option>
                    <option value="weekly">毎週</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">
                    {scheduleData.schedule_type === 'weekly' ? '曜日' : '日'}
                  </label>
                  <select
                    value={scheduleData.schedule_day}
                    onChange={(e) =>
                      setScheduleData({ ...scheduleData, schedule_day: parseInt(e.target.value) })
                    }
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    {scheduleData.schedule_type === 'weekly' ? (
                      <>
                        <option value={0}>月曜日</option>
                        <option value={1}>火曜日</option>
                        <option value={2}>水曜日</option>
                        <option value={3}>木曜日</option>
                        <option value={4}>金曜日</option>
                        <option value={5}>土曜日</option>
                        <option value={6}>日曜日</option>
                      </>
                    ) : (
                      Array.from({ length: 28 }, (_, i) => (
                        <option key={i + 1} value={i + 1}>
                          {i + 1}日
                        </option>
                      ))
                    )}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">時刻</label>
                  <select
                    value={scheduleData.schedule_hour}
                    onChange={(e) =>
                      setScheduleData({ ...scheduleData, schedule_hour: parseInt(e.target.value) })
                    }
                    className="w-full border rounded-lg px-3 py-2"
                  >
                    {Array.from({ length: 24 }, (_, i) => (
                      <option key={i} value={i}>
                        {i}:00
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {message && activeTab === 'schedule' && (
              <div
                className={`p-3 rounded-lg ${
                  message.includes('失敗') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
                }`}
              >
                {message}
              </div>
            )}

            <div className="pt-4">
              <button
                type="submit"
                disabled={saving}
                className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <Save size={20} />
                {saving ? '保存中...' : '設定を保存'}
              </button>
            </div>
          </form>
        </div>
      )}

      {activeTab === 'search-global' && (
        <div className="bg-white rounded-lg shadow p-6">
          <form onSubmit={handleSaveGlobalSearch} className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold mb-4">デフォルトリージョン</h2>
              <input
                type="text"
                value={globalSearchSettings.default_region || ''}
                onChange={(e) => handleRegionChange(e.target.value || null)}
                placeholder="例: jp-jp, us-en, sg-en (空欄でグローバル)"
                className="w-full border rounded-lg px-3 py-2"
                maxLength={10}
              />
              <p className="text-sm text-gray-500 mt-2">
                リージョンコード形式: 国-言語 (例: jp-jp, us-en, sg-en)
              </p>
            </div>

            <div>
              <h2 className="text-lg font-semibold mb-4">検索キーワード（自動設定）</h2>
              <div className="bg-gray-50 border rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-3">
                  以下のキーワードがリージョンに基づいて自動的に使用されます:
                </p>
                <div className="flex flex-wrap gap-2">
                  {regionKeywords.map((keyword, index) => (
                    <div
                      key={index}
                      className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                    >
                      {keyword}
                    </div>
                  ))}
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                ※ これらのキーワードはコードで管理されており、編集できません
              </p>
            </div>

            {message && activeTab === 'search-global' && (
              <div
                className={`p-3 rounded-lg ${
                  message.includes('失敗') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
                }`}
              >
                {message}
              </div>
            )}

            <div className="pt-4">
              <button
                type="submit"
                disabled={saving}
                className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <Save size={20} />
                {saving ? '保存中...' : '設定を保存'}
              </button>
            </div>
          </form>
        </div>
      )}

      {activeTab === 'search-company' && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">企業を選択</label>
            <select
              value={selectedCompany}
              onChange={(e) => handleCompanyChange(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
            >
              <option value="">企業を選択してください</option>
              {companies.map((company) => (
                <option key={company.id} value={company.name}>
                  {company.name}
                </option>
              ))}
            </select>
          </div>

          {companySearchSettings && (
            <form onSubmit={handleSaveCompany} className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold mb-4">
                  {companySearchSettings.company_name} の検索設定
                </h2>
              </div>

              {companySearchSettings.id && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-blue-900 mb-3">現在の設定値</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-blue-700 font-medium">検索リージョン:</span>
                      <span className="text-blue-900 font-mono bg-blue-100 px-2 py-0.5 rounded">
                        {companySearchSettings.region || '（グローバル設定を使用）'}
                      </span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-blue-700 font-medium">カスタムキーワード:</span>
                      <div className="flex flex-wrap gap-1">
                        {companySearchSettings.custom_keywords && companySearchSettings.custom_keywords.length > 0 ? (
                          companySearchSettings.custom_keywords.map((keyword, idx) => (
                            <span key={idx} className="text-blue-900 font-mono bg-blue-100 px-2 py-0.5 rounded text-xs">
                              {keyword}
                            </span>
                          ))
                        ) : (
                          <span className="text-blue-900">（グローバル設定を使用）</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium mb-2">
                  検索リージョン（この企業専用）
                </label>
                <input
                  type="text"
                  value={companySearchSettings.region || ''}
                  onChange={(e) =>
                    setCompanySearchSettings({
                      ...companySearchSettings,
                      region: e.target.value || null,
                    })
                  }
                  placeholder="例: sg-en, jp, us-en (空欄でグローバル設定を使用)"
                  className="w-full border rounded-lg px-3 py-2"
                  maxLength={10}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  カスタムキーワード（この企業専用）
                </label>
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={companyKeywordInput}
                      onChange={(e) => setCompanyKeywordInput(e.target.value)}
                      onKeyPress={(e) =>
                        e.key === 'Enter' && (e.preventDefault(), addCompanyKeyword())
                      }
                      placeholder="キーワードを入力してEnter"
                      className="flex-1 border rounded-lg px-3 py-2"
                    />
                    <button
                      type="button"
                      onClick={addCompanyKeyword}
                      className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                    >
                      <Plus size={20} />
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {(companySearchSettings.custom_keywords || []).map((keyword, index) => (
                      <div
                        key={index}
                        className="bg-green-100 text-green-800 px-3 py-1 rounded-full flex items-center gap-2"
                      >
                        {keyword}
                        <button
                          type="button"
                          onClick={() => removeCompanyKeyword(index)}
                          className="hover:text-green-900"
                        >
                          <X size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                  <p className="text-sm text-gray-500">
                    空欄の場合、グローバル設定のキーワードが使用されます
                  </p>
                </div>
              </div>

              {message && activeTab === 'search-company' && (
                <div
                  className={`p-3 rounded-lg ${
                    message.includes('失敗')
                      ? 'bg-red-50 text-red-700'
                      : 'bg-green-50 text-green-700'
                  }`}
                >
                  {message}
                </div>
              )}

              <div className="pt-4 flex gap-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  <Save size={20} />
                  {saving ? '保存中...' : '設定を保存'}
                </button>
                {companySearchSettings.id && (
                  <button
                    type="button"
                    onClick={handleDeleteCompany}
                    disabled={saving}
                    className="flex items-center gap-2 bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50"
                  >
                    <X size={20} />
                    設定を削除
                  </button>
                )}
              </div>
            </form>
          )}
        </div>
      )}

      {activeTab === 'prompts' && promptsData && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-6">AI分析プロンプト設定</h2>

          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-semibold mb-4 text-blue-700">記事分類 (Classifier)</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">システムプロンプト</label>
                  <div className="bg-gray-50 border rounded-lg p-4">
                    <pre className="text-sm whitespace-pre-wrap text-gray-700">
                      {promptsData.classifier.system_prompt}
                    </pre>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">ユーザープロンプトテンプレート</label>
                  <div className="bg-gray-50 border rounded-lg p-4 max-h-96 overflow-y-auto">
                    <pre className="text-sm whitespace-pre-wrap text-gray-700">
                      {promptsData.classifier.user_prompt_template}
                    </pre>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">カテゴリ一覧</label>
                    <div className="bg-gray-50 border rounded-lg p-4 max-h-60 overflow-y-auto">
                      <ul className="space-y-1">
                        {promptsData.classifier.categories.map((cat: string, idx: number) => (
                          <li key={idx} className="text-sm text-gray-700">• {cat}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">業務領域一覧</label>
                    <div className="bg-gray-50 border rounded-lg p-4 max-h-60 overflow-y-auto">
                      <ul className="space-y-1">
                        {promptsData.classifier.business_areas.map((area: string, idx: number) => (
                          <li key={idx} className="text-sm text-gray-700">• {area}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Temperature</label>
                  <div className="bg-gray-50 border rounded-lg px-4 py-2">
                    <span className="text-sm text-gray-700">{promptsData.classifier.temperature}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="border-t pt-8">
              <h3 className="text-lg font-semibold mb-4 text-green-700">記事要約 (Summarizer)</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">システムプロンプト</label>
                  <div className="bg-gray-50 border rounded-lg p-4">
                    <pre className="text-sm whitespace-pre-wrap text-gray-700">
                      {promptsData.summarizer.system_prompt}
                    </pre>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">ユーザープロンプトテンプレート</label>
                  <div className="bg-gray-50 border rounded-lg p-4 max-h-96 overflow-y-auto">
                    <pre className="text-sm whitespace-pre-wrap text-gray-700">
                      {promptsData.summarizer.user_prompt_template}
                    </pre>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Temperature</label>
                  <div className="bg-gray-50 border rounded-lg px-4 py-2">
                    <span className="text-sm text-gray-700">{promptsData.summarizer.temperature}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="border-t pt-8">
              <h3 className="text-lg font-semibold mb-4 text-purple-700">AI関連性判定 (AI Relevance Filter)</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">システムプロンプト</label>
                  <div className="bg-gray-50 border rounded-lg p-4">
                    <pre className="text-sm whitespace-pre-wrap text-gray-700">
                      {promptsData.ai_relevance.system_prompt}
                    </pre>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">記事本文用プロンプトテンプレート</label>
                  <div className="bg-gray-50 border rounded-lg p-4 max-h-96 overflow-y-auto">
                    <pre className="text-sm whitespace-pre-wrap text-gray-700">
                      {promptsData.ai_relevance.content_prompt_template}
                    </pre>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">タイトル+スニペット用プロンプトテンプレート（フォールバック）</label>
                  <div className="bg-gray-50 border rounded-lg p-4 max-h-96 overflow-y-auto">
                    <pre className="text-sm whitespace-pre-wrap text-gray-700">
                      {promptsData.ai_relevance.text_prompt_template}
                    </pre>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Temperature</label>
                  <div className="bg-gray-50 border rounded-lg px-4 py-2">
                    <span className="text-sm text-gray-700">{promptsData.ai_relevance.temperature}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>注意:</strong> これらのプロンプトは表示専用です。変更する場合は、バックエンドのコード
                (<code className="bg-blue-100 px-1 rounded">backend/app/services/llm/prompt_templates.py</code>) を直接編集してください。
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
