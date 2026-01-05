import type { Article, ArticleAnalysisCoefficients } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';
const API_PREFIX = API_BASE.includes('/.netlify/functions/api-proxy') ? '' : '/api/v1';
const BASIC_AUTH_USERNAME = process.env.NEXT_PUBLIC_BASIC_AUTH_USERNAME;
const BASIC_AUTH_PASSWORD = process.env.NEXT_PUBLIC_BASIC_AUTH_PASSWORD;

function getBasicAuthHeader(): string | null {
  if (BASIC_AUTH_USERNAME && BASIC_AUTH_PASSWORD) {
    if (typeof window === 'undefined') {
      return `Basic ${Buffer.from(`${BASIC_AUTH_USERNAME}:${BASIC_AUTH_PASSWORD}`).toString('base64')}`;
    }
    return `Basic ${btoa(`${BASIC_AUTH_USERNAME}:${BASIC_AUTH_PASSWORD}`)}`;
  }
  return null;
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const basicAuth = getBasicAuthHeader();
  const res = await fetch(`${API_BASE}${API_PREFIX}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(basicAuth ? { Authorization: basicAuth } : {}),
      ...options?.headers,
    },
  });

  if (!res.ok) {
    throw new Error(`API Error: ${res.status}`);
  }

  return res.json();
}

// Companies
export const getCompanies = () => 
  fetchAPI<{ items: any[]; total: number }>('/companies');

export const createCompany = (data: any) =>
  fetchAPI('/companies', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const updateCompany = (id: number, data: any) =>
  fetchAPI(`/companies/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const deleteCompany = (id: number) =>
  fetchAPI(`/companies/${id}`, { method: 'DELETE' });

export const addSourceUrl = (companyId: number, data: any) =>
  fetchAPI(`/companies/${companyId}/urls`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const updateSourceUrl = (companyId: number, urlId: number, data: any) =>
  fetchAPI(`/companies/${companyId}/urls/${urlId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const deleteSourceUrl = (companyId: number, urlId: number) =>
  fetchAPI(`/companies/${companyId}/urls/${urlId}`, { method: 'DELETE' });

// Articles
export const getArticles = (params?: Record<string, string>) => {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetchAPI<{ items: any[]; total: number }>(`/articles${query}`);
};

export const updateArticle = (id: number, data: any) =>
  fetchAPI<Article>(`/articles/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const addArticleFromUrl = (url: string, companyId: number) =>
  fetchAPI<{ job_id: number; message: string }>('/articles/from-url', {
    method: 'POST',
    body: JSON.stringify({ url, company_id: companyId }),
  });

export const addArticlesFromUrls = (urls: string[], companyId: number) =>
  fetchAPI<{ job_id: number; message: string }>('/articles/from-urls', {
    method: 'POST',
    body: JSON.stringify({ urls, company_id: companyId }),
  });

export const getArticleAnalysisCoefficients = (params?: Record<string, string>) => {
  const query = params ? '?' + new URLSearchParams(params).toString() : '';
  return fetchAPI<ArticleAnalysisCoefficients>(`/articles/analysis-coefficients${query}`);
};

export const getArticleAnalysisStats = () =>
  fetchAPI<{ total: number; analyzed: number; coefficient: number }>(
    '/articles/analysis-stats'
  );

// Jobs
export const getJobs = () =>
  fetchAPI<{ items: any[]; total: number }>('/jobs');

export const startJob = (jobType: string = 'manual') =>
  fetchAPI<{ job_id: number; message: string }>('/jobs/start', {
    method: 'POST',
    body: JSON.stringify({ job_type: jobType }),
  });

// Settings
export const getSettings = () =>
  fetchAPI<any>('/settings');

export const updateSettings = (data: any) =>
  fetchAPI('/settings', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// Reports
export const getReports = () =>
  fetchAPI<{ reports: any[] }>('/reports');

export const generateReport = (startDate: string, endDate: string) =>
  fetchAPI(`/reports/generate?start_date=${startDate}&end_date=${endDate}`, {
    method: 'POST',
  });

// Search Settings
export const getGlobalSearchSettings = () =>
  fetchAPI<any>('/search-settings/global');

export const updateGlobalSearchSettings = (data: any) =>
  fetchAPI('/search-settings/global', {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const getCompanySearchSettings = (companyName: string) =>
  fetchAPI<any>(`/search-settings/company/${encodeURIComponent(companyName)}`);

export const updateCompanySearchSettings = (companyName: string, data: any) =>
  fetchAPI(`/search-settings/company/${encodeURIComponent(companyName)}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const deleteCompanySearchSettings = (companyName: string) =>
  fetchAPI(`/search-settings/company/${encodeURIComponent(companyName)}`, {
    method: 'DELETE',
  });

export const getRegionKeywords = (region: string) =>
  fetchAPI<{ region: string; keywords: string[] }>(`/search-settings/keywords/${encodeURIComponent(region)}`);

// Prompts
export const getPrompts = () =>
  fetchAPI<{
    classifier: {
      system_prompt: string;
      user_prompt_template: string;
      categories: string[];
      business_areas: string[];
      temperature: number;
    };
    summarizer: {
      system_prompt: string;
      user_prompt_template: string;
      temperature: number;
    };
  }>('/prompts');
