import { FormEvent, useEffect, useState } from "react";
import { ShieldCheck, Stethoscope } from "lucide-react";
import { api } from "../api";
import type { RecommendationItem } from "../types";

type SafetyResult = { status: string; emergency: boolean; guidance: string; normal_ranking_allowed: boolean };
type Specialty = { name: string; source: string };

export default function AssessmentPage() {
  const [description, setDescription] = useState("");
  const [duration, setDuration] = useState("");
  const [severity, setSeverity] = useState<"mild" | "moderate" | "severe" | "critical" | "">("");
  const [onset, setOnset] = useState("");
  const [associated, setAssociated] = useState("");
  const [history, setHistory] = useState("");
  const [context, setContext] = useState("");
  const [location, setLocation] = useState("");
  const [consultationType, setConsultationType] = useState<"" | "in-person" | "video">("");
  const [requestedSpecialty, setRequestedSpecialty] = useState("");
  const [specialties, setSpecialties] = useState<Specialty[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [safety, setSafety] = useState<SafetyResult | null>(null);
  const [followUp, setFollowUp] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api<Specialty[]>("/api/v1/specialties")
      .then(setSpecialties)
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Could not load available specialties."));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setFollowUp("");
    setSafety(null);
    setRecommendations([]);
    setLoading(true);
    try {
      const assessment = await api<{
        assessment_id: string;
        safety: SafetyResult;
        needs_more_information: boolean;
        follow_up: string | null;
      }>("/api/v1/symptoms/assess", {
        method: "POST",
        body: JSON.stringify({
          description,
          duration: duration || null,
          severity: severity || null,
          onset: onset || null,
          associated_symptoms: associated.split(",").map((value) => value.trim()).filter(Boolean),
          relevant_medical_history: history || null,
          additional_context: context || null,
        }),
      });
      setSafety(assessment.safety);
      if (assessment.safety.emergency) {
        setFollowUp(assessment.safety.guidance);
        return;
      }
      if (assessment.needs_more_information) {
        setFollowUp(assessment.follow_up || "Please provide more detail before continuing.");
        return;
      }
      if (!requestedSpecialty) {
        setFollowUp("No specialty was inferred. Select a specialty already suggested by your healthcare professional to compare demo providers.");
        return;
      }
      const result = await api<{
        items: RecommendationItem[];
        safety: SafetyResult;
        follow_up: string | null;
      }>("/api/v1/recommendations", {
        method: "POST",
        body: JSON.stringify({
          assessment_id: assessment.assessment_id,
          requested_specialty: requestedSpecialty,
          location: location || null,
          consultation_type: consultationType || null,
        }),
      });
      setSafety(result.safety);
      setRecommendations(result.items);
      if (result.follow_up) setFollowUp(result.follow_up);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to complete the assessment.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-heading"><div><div className="eyebrow">Symptom navigation</div><h1>Tell us what you’re experiencing</h1></div></div>
      <p className="page-intro">This questionnaire records your concern and checks configured safety signals. It does not diagnose or infer a specialty from symptoms.</p>
      <div className="assessment-grid">
        <form className="panel form-panel" onSubmit={submit} aria-busy={loading}>
          <label>Describe your concern
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} required minLength={3} maxLength={2000} rows={4} placeholder="Describe the concern in your own words." />
          </label>
          <div className="form-row">
            <label>How long has it been happening?
              <input value={duration} onChange={(event) => setDuration(event.target.value)} maxLength={100} placeholder="For example, about three days" />
            </label>
            <label>Severity as you experience it
              <select value={severity} onChange={(event) => setSeverity(event.target.value as typeof severity)}>
                <option value="">Not specified</option><option value="mild">Mild</option><option value="moderate">Moderate</option><option value="severe">Severe</option><option value="critical">Critical</option>
              </select>
            </label>
          </div>
          <label>Onset
            <input value={onset} onChange={(event) => setOnset(event.target.value)} maxLength={100} placeholder="Sudden, gradual, or when it began" />
          </label>
          <label>Other symptoms (comma separated)
            <input value={associated} onChange={(event) => setAssociated(event.target.value)} placeholder="Only include symptoms you are experiencing" />
          </label>
          <label>Relevant medical history (optional)
            <textarea value={history} onChange={(event) => setHistory(event.target.value)} maxLength={2000} rows={2} />
          </label>
          <label>Additional context (optional)
            <textarea value={context} onChange={(event) => setContext(event.target.value)} maxLength={2000} rows={2} />
          </label>
          <div className="section-divider">
            <h2>Provider preferences <span className="badge">OPTIONAL</span></h2>
            <p>These preferences affect provider ranking only; they do not imply medical suitability.</p>
          </div>
          <label>Specialty already suggested by your healthcare professional
            <select value={requestedSpecialty} onChange={(event) => setRequestedSpecialty(event.target.value)}>
              <option value="">Not provided — do not infer</option>
              {specialties.map((item) => <option key={item.name} value={item.name}>{item.name} (demo catalogue)</option>)}
            </select>
          </label>
          <div className="form-row">
            <label>Preferred location<input value={location} onChange={(event) => setLocation(event.target.value)} maxLength={255} /></label>
            <label>Consultation type
              <select value={consultationType} onChange={(event) => setConsultationType(event.target.value as typeof consultationType)}>
                <option value="">Any</option><option value="in-person">In person</option><option value="video">Video</option>
              </select>
            </label>
          </div>
          {error && <div className="error" role="alert">{error}</div>}
          <button className="button primary" disabled={loading}>{loading ? "Saving assessment…" : "Submit assessment"}</button>
        </form>
        <section className="panel results-panel" aria-live="polite">
          <h2>Assessment and provider options</h2>
          {!safety && !loading && <div className="empty"><Stethoscope size={28} /><strong>Complete the questionnaire</strong><span>Safety guidance and supported next steps will appear here.</span></div>}
          {loading && <div role="status" className="loading-message">Saving your assessment and checking safety…</div>}
          {safety && <div className={`safety-banner ${safety.emergency ? "danger" : ""}`}><ShieldCheck size={18} /><div><strong>{safety.emergency ? "Urgent-care guidance" : "Safety status: " + safety.status}</strong><span>{safety.guidance}</span></div></div>}
          {followUp && <p className={safety?.emergency ? "urgent-message" : "follow-up"}>{followUp}</p>}
          {recommendations.length > 0 && <div className="provider-list">{recommendations.map((item) =>
            <article key={item.provider_id}><div className="rank">{item.rank}</div><div><h3>{item.provider_name} <small>DEMO · NOT VERIFIED</small></h3><p>{item.specialty} · {item.location} · {item.consultation_type}</p><span>{item.explanation}</span></div></article>
          )}</div>}
          {recommendations.length > 0 && <p className="disclaimer">All displayed providers and availability signals are synthetic demonstration data, not verified or bookable.</p>}
        </section>
      </div>
    </div>
  );
}
