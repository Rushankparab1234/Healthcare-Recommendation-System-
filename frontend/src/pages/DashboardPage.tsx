import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, Bookmark, ClipboardList, UserRound } from "lucide-react";
import { api } from "../api";
import type { DashboardRecommendation, Provider } from "../types";

type DashboardData = {
  assessment_count: number;
  recommendation_count: number;
  saved_provider_count: number;
  profile_completion: { completed: number; total: number; percentage: number };
  recent_assessments: { id: string; created_at: string; severity: string | null; emergency: boolean; symptoms: string[] }[];
  recent_recommendations: DashboardRecommendation[];
  saved_providers: Provider[];
  recent_activity: { type: string; id: string; created_at: string }[];
};

function formatDate(value: string) {
  return new Date(value).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<DashboardData>("/api/v1/patients/me/dashboard")
      .then(setData)
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Unable to load your dashboard."));
  }, []);

  return (
    <div className="page">
      <div className="page-heading">
        <div><div className="eyebrow">Patient overview</div><h1>Good morning, {localStorage.getItem("healthwise_name") || "there"}</h1></div>
        <Link className="button" to="/assessment">New assessment</Link>
      </div>
      {error && <div className="error" role="alert">{error}</div>}
      {!data && !error && <div className="panel" role="status">Loading your patient dashboard…</div>}
      {data && <>
        <div className="stats-grid">
          <section className="stat-card"><span className="stat-icon teal"><ClipboardList /></span><div><small>Total assessments</small><strong>{data.assessment_count}</strong></div></section>
          <section className="stat-card"><span className="stat-icon blue"><Activity /></span><div><small>Recommendations</small><strong>{data.recommendation_count}</strong></div></section>
          <section className="stat-card"><span className="stat-icon gold"><UserRound /></span><div><small>Profile completed</small><strong>{data.profile_completion.percentage}%</strong></div></section>
        </div>
        <div className="content-grid dashboard-panels">
          <section className="panel">
            <div className="panel-heading"><h2>Recent assessments</h2><Link to="/assessment">New</Link></div>
            {data.recent_assessments.length ? <ul className="activity-list">{data.recent_assessments.map((item) =>
              <li key={item.id}><strong>{item.symptoms.length ? item.symptoms.join(", ") : "Symptom review"}</strong><span>{formatDate(item.created_at)} · {item.severity || "severity not specified"}</span>{item.emergency && <b className="badge danger">Urgent-care pathway</b>}</li>
            )}</ul> : <p className="muted">No assessments recorded yet.</p>}
          </section>
          <section className="panel">
            <div className="panel-heading"><h2>Recent recommendations</h2><Link to="/providers">Explore</Link></div>
            {data.recent_recommendations.length ? <ul className="activity-list">{data.recent_recommendations.map((item) =>
              <li key={item.id}>
                <strong>Recommendation</strong>
                <small>Recommendation ID: {item.id}</small>
                <span>{formatDate(item.created_at)}</span>
                {item.items.length
                  ? <ol className="recommendation-items">{item.items.map((recommendation) =>
                    <li className="recommendation-item" key={`${recommendation.provider_id ?? recommendation.provider_name}-${recommendation.rank}`}>
                      <strong>#{recommendation.rank} {recommendation.provider_name}</strong>
                      <span>{recommendation.specialty}</span>
                      <p>{recommendation.explanation}</p>
                    </li>
                  )}</ol>
                  : <span>No provider matches were recorded.</span>}
              </li>
            )}</ul> : <p className="muted">Recommendations appear after you complete an assessment and choose a specialty.</p>}
          </section>
        </div>
        <div className="content-grid dashboard-panels">
          <section className="panel">
            <div className="panel-heading"><h2>Saved demo providers <span className="badge">DEMO DATA</span></h2><span><Bookmark size={15} /> {data.saved_provider_count}</span></div>
            {data.saved_providers.length ? <ul className="activity-list">{data.saved_providers.map((provider) =>
              <li key={provider.id}><Link to={`/providers/${provider.id}`}><strong>{provider.name}</strong></Link><span>{provider.specialty} · {provider.location}</span></li>
            )}</ul> : <p className="muted">Save a provider from discovery to see it here. Demo providers are not verified or bookable.</p>}
          </section>
          <section className="panel">
            <div className="panel-heading"><h2>Recent activity</h2><span>{data.recent_activity.length} items</span></div>
            {data.recent_activity.length ? <ul className="activity-list">{data.recent_activity.map((item) =>
              <li key={`${item.type}-${item.id}`}><strong>{item.type === "assessment" ? "Assessment submitted" : "Recommendation created"}</strong><span>{formatDate(item.created_at)}</span></li>
            )}</ul> : <p className="muted">Your activity will appear here.</p>}
          </section>
        </div>
        <section className="panel profile-progress">
          <div><div className="eyebrow">Profile completeness</div><p>{data.profile_completion.completed} of {data.profile_completion.total} profile fields completed.</p></div>
          <progress value={data.profile_completion.percentage} max="100" aria-label="Profile completion" />
          <Link className="button" to="/profile">Review profile</Link>
        </section>
        <footer className="disclaimer">HealthWise AI provides navigation and general information only. It does not diagnose or prescribe.</footer>
      </>}
    </div>
  );
}
