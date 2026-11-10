import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const ErrorAlert = ({ message, onRetry }) => {
  if (!message) return null;

  return (
    <div className="rounded-xl bg-rose-50 border border-rose-200 p-4 text-rose-800 flex items-start gap-3 my-4">
      <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <h4 className="text-sm font-semibold text-rose-900">Request Error</h4>
        <p className="text-sm text-rose-700 mt-0.5">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1 px-3 py-1 bg-white border border-rose-300 rounded-lg text-xs font-semibold text-rose-700 hover:bg-rose-100 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry
        </button>
      )}
    </div>
  );
};

export default ErrorAlert;
