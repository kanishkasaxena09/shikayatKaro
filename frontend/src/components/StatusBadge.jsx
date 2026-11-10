import React from 'react';

export const StatusBadge = ({ status }) => {
  const getBadgeStyle = () => {
    switch (status) {
      case 'Submitted':
        return 'bg-slate-100 text-slate-700 border-slate-300';
      case 'AI Analysed':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'Assigned':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'Under Investigation':
      case 'In Progress':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'Awaiting Info':
        return 'bg-orange-50 text-orange-700 border-orange-200';
      case 'Resolved':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'Closed':
        return 'bg-teal-50 text-teal-800 border-teal-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getBadgeStyle()}`}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-70"></span>
      {status || 'Unknown'}
    </span>
  );
};

export default StatusBadge;
