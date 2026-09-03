import React, { useContext, useState } from 'react';
import { Gavel, Lock } from 'lucide-react';
import { DisputeDetailResponse } from '../../types';
import { AuthContext } from '../../context/AuthContext';
import { AdminAdjudicationModal } from './AdminAdjudicationModal';

export interface AdminAdjudicationPanelProps {
  dispute: DisputeDetailResponse;
  onDisputeUpdated: (updated: DisputeDetailResponse) => void;
}

export const AdminAdjudicationPanel: React.FC<AdminAdjudicationPanelProps> = ({
  dispute,
  onDisputeUpdated,
}) => {
  const auth = useContext(AuthContext);
  const user = auth?.user;
  const [isModalOpen, setIsModalOpen] = useState(false);

  // System role based visibility: only ADMIN users have adjudication authority
  const isAdmin = user?.role === 'ADMIN';
  if (!isAdmin) return null;

  const isActive = dispute.status === 'OPEN' || dispute.status === 'UNDER_REVIEW';

  return (
    <div
      data-testid="admin-adjudication-panel"
      className="p-5 sm:p-6 rounded-2xl bg-amber-950/20 border border-amber-500/30 space-y-4"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shrink-0">
            <Gavel className="w-5 h-5" />
          </div>
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white tracking-tight">
                Institutional Adjudication Authority
              </h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                ADMIN PRIVILEGE
              </span>
            </div>
            <p className="text-xs text-slate-400">
              {isActive
                ? 'You are authorized to review evidence and broadcast a definitive on-chain adjudication for this claim.'
                : 'This dispute has already been concluded. The adjudication outcome is recorded on the smart contract.'}
            </p>
          </div>
        </div>

        {isActive ? (
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition-all shadow-lg shadow-amber-500/20 self-start sm:self-auto shrink-0"
          >
            <Gavel className="w-4 h-4" />
            <span>Adjudicate Claim</span>
          </button>
        ) : (
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800 text-xs font-semibold text-slate-400 self-start sm:self-auto shrink-0">
            <Lock className="w-3.5 h-3.5 text-slate-500" />
            <span>Adjudication Concluded</span>
          </div>
        )}
      </div>

      {/* Modal */}
      <AdminAdjudicationModal
        dispute={dispute}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={(updated) => {
          onDisputeUpdated(updated);
        }}
      />
    </div>
  );
};
