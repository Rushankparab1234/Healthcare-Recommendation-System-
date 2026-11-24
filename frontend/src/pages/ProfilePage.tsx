import { FormEvent, useEffect, useState } from "react";
import { api } from "../api";

type Profile = {
  age: number | null;
  sex: string | null;
  location: string | null;
  medical_history: string | null;
  allergies: string | null;
  preferences: string | null;
  consent_research: boolean;
  consent_research_at: string | null;
};

const emptyProfile: Profile = {
  age: null,
  sex: null,
  location: null,
  medical_history: null,
  allergies: null,
  preferences: null,
  consent_research: false,
  consent_research_at: null,
};

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile>(emptyProfile);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    api<Profile | null>("/api/v1/patients/me")
      .then((saved) => setProfile({ ...emptyProfile, ...saved }))
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Unable to load your profile."))
      .finally(() => setLoading(false));
  }, []);

  function update<K extends keyof Profile>(field: K, value: Profile[K]) {
    setProfile((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const saved = await api<{ profile: Partial<Profile> }>("/api/v1/patients/me", {
        method: "PUT",
        body: JSON.stringify(profile),
      });
      setProfile((current) => ({ ...current, ...saved.profile }));
      setNotice("Profile saved.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to save your profile.");
    } finally {
      setSaving(false);
    }
  }

  return <div className="page">
    <div className="page-heading"><div><div className="eyebrow">Patient profile</div><h1>Your health profile</h1></div></div>
    <p className="page-intro">Profile data is private to your account. Optional fields are not used to diagnose or infer specialty.</p>
    {loading && <div className="panel" role="status">Loading your profile…</div>}
    {!loading && <form className="panel profile-form" onSubmit={submit}>
      <div className="form-row">
        <label>Age<input type="number" min="0" max="130" value={profile.age ?? ""} onChange={(event) => update("age", event.target.value ? Number(event.target.value) : null)} /></label>
        <label>Sex (optional)<input value={profile.sex ?? ""} onChange={(event) => update("sex", event.target.value || null)} maxLength={32} /></label>
      </div>
      <label>Location<input value={profile.location ?? ""} onChange={(event) => update("location", event.target.value || null)} maxLength={255} /></label>
      <label>Relevant medical history<textarea value={profile.medical_history ?? ""} onChange={(event) => update("medical_history", event.target.value || null)} maxLength={4000} rows={3} /></label>
      <label>Allergies<textarea value={profile.allergies ?? ""} onChange={(event) => update("allergies", event.target.value || null)} maxLength={2000} rows={2} /></label>
      <label>Healthcare preferences<textarea value={profile.preferences ?? ""} onChange={(event) => update("preferences", event.target.value || null)} maxLength={1000} rows={2} /></label>
      <label className="checkbox-label"><input type="checkbox" checked={profile.consent_research} onChange={(event) => update("consent_research", event.target.checked)} /> Allow use of de-identified information for research (optional)</label>
      {profile.consent_research && profile.consent_research_at && <p className="muted">Research consent recorded {new Date(profile.consent_research_at).toLocaleDateString()}.</p>}
      {error && <div className="error" role="alert">{error}</div>}
      {notice && <div className="success" role="status">{notice}</div>}
      <button className="button primary" disabled={saving}>{saving ? "Saving…" : "Save profile"}</button>
    </form>}
  </div>;
}
