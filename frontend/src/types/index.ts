export interface Company {
  id: number;
  name: string;
  name_en: string | null;
  country: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  source_urls: SourceUrl[];
}

export interface SourceUrl {
  id: number;
  company_id: number;
  url: string;
  url_type: string;
  is_active: boolean;
  created_at: string;
}

export interface Article {
  id: number;
  company_id: number;
  title: string;
  content: string | null;
  summary: string | null;
  url: string;
  published_date: string | null;
  category: string | null;
  business_area: string | null;
  tags: string | null;
  is_inappropriate: boolean;
  inappropriate_reason: string | null;
  is_reviewed: boolean;
  created_at: string;
}

export interface ArticleAnalysisGroup {
  label: string;
  count: number;
}

export interface ArticleAnalysisTimeSeries {
  period: string;
  count: number;
}

export interface ArticleAnalysisCoefficients {
  total: number;
  by_category: ArticleAnalysisGroup[];
  by_business_area: ArticleAnalysisGroup[];
  by_region: ArticleAnalysisGroup[];
  by_month: ArticleAnalysisTimeSeries[];
}

export interface ArticleAnalysisStats {
  total: number;
  analyzed: number;
  coefficient: number;
}

export interface JobHistory {
  id: number;
  job_type: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  total_companies: number;
  processed_companies: number;
  total_articles: number;
  error_message: string | null;
}

export interface SearchSetting {
  id: number;
  search_start_date: string;
  search_end_date: string;
  schedule_type: string;
  schedule_day: number;
  schedule_hour: number;
  created_at: string;
  updated_at: string;
}

export interface Report {
  filename: string;
  size: number;
  created_at: number;
}
