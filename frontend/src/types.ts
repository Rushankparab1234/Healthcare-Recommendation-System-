export type Provider = {
  id: string;
  name: string;
  specialty: string;
  location: string;
  consultation_type: string;
  is_demo: boolean;
  verification_status: string;
  qualification_information: string;
  availability: {
    demo_signal: number;
    is_bookable: boolean;
    description: string;
  };
};

export type RecommendationItem = {
  rank: number;
  provider_id: string;
  provider_name: string;
  specialty: string;
  location: string;
  consultation_type: string;
  is_demo: boolean;
  ranking_score: number;
  matched_attributes: string[];
  explanation: string;
  data_completeness: string;
  verification_status: string;
  qualification_information: string;
  availability: Provider["availability"];
};

export type DashboardRecommendationItem = {
  provider_id: string | null;
  provider_name: string;
  specialty: string;
  rank: number;
  explanation: string;
};

export type DashboardRecommendation = {
  id: string;
  created_at: string;
  items: DashboardRecommendationItem[];
};
