import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import {
  FileText,
  Send,
  Shield,
  HelpCircle,
  MapPin,
  Users,
  Sparkles,
  Globe,
  Loader2,
} from 'lucide-react';
import AiAnalysisModal from '../components/AiAnalysisModal';
import ErrorAlert from '../components/ErrorAlert';

export const SubmitComplaint = () => {
  const routerLocation = useLocation();
  const { user, isAuthenticated } = useAuth();
  const { addToast } = useToast();

  const [text, setText] = useState(routerLocation.state?.prefillText || '');
  const [locationId, setLocationId] = useState('');
  const [affectedCount, setAffectedCount] = useState(1);
  const [isAnonymous, setIsAnonymous] = useState(!isAuthenticated);

  const [locations, setLocations] = useState([]);
  const [loadingLocations, setLoadingLocations] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  // Load campus locations from heatmap endpoint
  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const res = await api.analytics.getHeatmap();
        setLocations(res.data || []);
        if (res.data?.length > 0) {
          setLocationId(res.data[0].location_id);
        }
      } catch (err) {
        console.warn('Could not load locations dynamically, falling back to defaults');
        setLocations([
          { location_id: 2, location_name: 'Hostel Block B' },
          { location_id: 1, location_name: 'Academic Block A' },
          { location_id: 3, location_name: 'Central Library' },
          { location_id: 4, location_name: 'Student Activity Center (SAC)' },
          { location_id: 5, location_name: 'Administrative Building' },
        ]);
        setLocationId(2);
      } finally {
        setLoadingLocations(false);
      }
    };
    fetchLocations();
  }, []);

  const handlePreset = (presetText, locId = null) => {
    setText(presetText);
    if (locId) setLocationId(locId);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim() || text.trim().length < 5) {
      setError('Please provide a detailed grievance description (at least 5 characters).');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const payload = {
        text: text.trim(),
        location_id: locationId ? parseInt(locationId) : null,
        affected_count: parseInt(affectedCount) || 1,
        is_anonymous: Boolean(isAnonymous),
      };

      const res = await api.complaints.submit(payload);
      addToast('Grievance registered and analysed by AI engine.', 'success');
      setAnalysisResult(res.data);
      // Reset input
      setText('');
    } catch (err) {
      setError(err.userMessage || 'Failed to submit grievance');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      {/* Modal on success */}
      {analysisResult && (
        <AiAnalysisModal
          data={analysisResult}
          onClose={() => setAnalysisResult(null)}
        />
      )}

      {/* Page Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-indigo-600 font-semibold text-xs uppercase tracking-wider mb-1">
          <Globe className="w-4 h-4" />
          Multilingual Grievance Portal
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          File a Campus Grievance
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Describe the issue in <strong>English</strong>, <strong>Hindi</strong> (हिंदी), or <strong>Hinglish</strong>. Our AI classifier will automatically route and cluster it.
        </p>
      </div>

      <ErrorAlert message={error} />

      {/* Main Form Card */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
        {/* Preset Quick Fill Buttons */}
        <div>
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            Quick Test Examples (Multilingual):
          </label>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() =>
                handlePreset(
                  'Severe drinking water leakage from main pipe near Hostel Block B entrance, flooding walkway',
                  2
                )
              }
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 border border-slate-200 transition text-left"
            >
              💧 English: Water leak outside Hostel Block B
            </button>
            <button
              type="button"
              onClick={() =>
                handlePreset(
                  'हॉस्टल ब्लॉक बी के मुख्य गेट के पास पानी का पाइप फटा हुआ है और सड़क पर बहुत सारा पानी बह रहा है',
                  2
                )
              }
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 border border-slate-200 transition text-left"
            >
              🇮🇳 Hindi: हॉस्टल ब्लॉक बी में पानी का पाइप फटा
            </button>
            <button
              type="button"
              onClick={() =>
                handlePreset(
                  'Hostel Block B ground floor ke paas paani ka pipe leak ho raha hai nal ka paani waste ho raha hai',
                  2
                )
              }
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 border border-slate-200 transition text-left"
            >
              🗣️ Hinglish: Paani ka pipe leak ho raha hai
            </button>
            <button
              type="button"
              onClick={() =>
                handlePreset(
                  'Spark and burning plastic odor coming from Computer Lab 2 distribution switchboard',
                  1
                )
              }
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-700 border border-slate-200 transition text-left"
            >
              ⚡ Critical: Sparks in Computer Lab 2
            </button>
          </div>
        </div>

        {/* Text Area */}
        <div>
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            Grievance Description <span className="text-rose-500">*</span>
          </label>
          <textarea
            rows={4}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type your complaint here in English, Hindi, or Hinglish..."
            className="w-full text-sm rounded-xl border border-slate-300 p-3.5 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition"
            required
          />
          <p className="text-[11px] text-slate-400 mt-1">
            Include specific landmarks, room numbers, or equipment details if known.
          </p>
        </div>

        {/* Location & Impact Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Location Picker */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-slate-500" />
              Campus Location
            </label>
            <select
              value={locationId}
              onChange={(e) => setLocationId(e.target.value)}
              className="w-full text-sm rounded-xl border border-slate-300 p-2.5 bg-white text-slate-800 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition"
            >
              {locations.map((loc) => (
                <option key={loc.location_id} value={loc.location_id}>
                  {loc.location_name} {loc.parent_name ? `(${loc.parent_name})` : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Affected Count */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Users className="w-3.5 h-3.5 text-slate-500" />
              Estimated People Affected
            </label>
            <input
              type="number"
              min="1"
              max="500"
              value={affectedCount}
              onChange={(e) => setAffectedCount(e.target.value)}
              className="w-full text-sm rounded-xl border border-slate-300 p-2.5 bg-white text-slate-800 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition"
            />
          </div>
        </div>

        {/* Anonymous Reporting Checkbox */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={isAnonymous}
              onChange={(e) => setIsAnonymous(e.target.checked)}
              className="mt-0.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
            />
            <div>
              <span className="font-semibold text-xs text-slate-800 flex items-center gap-1">
                <Shield className="w-3.5 h-3.5 text-indigo-600" />
                Submit Anonymously (Zero Identity Leakage)
              </span>
              <p className="text-[11px] text-slate-500 mt-0.5">
                When enabled, your user ID will <strong>not</strong> be linked to this grievance in the database. You will receive an 8-character confidential access code for status tracking.
              </p>
            </div>
          </label>
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-slate-400">
            {isAuthenticated
              ? `Submitting as ${user.full_name}${isAnonymous ? ' (Anonymously)' : ''}`
              : 'Submitting as Guest / Public'}
          </span>

          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-xl text-sm font-semibold shadow-md shadow-indigo-100 transition"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Processing with AI...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Submit Grievance
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SubmitComplaint;
