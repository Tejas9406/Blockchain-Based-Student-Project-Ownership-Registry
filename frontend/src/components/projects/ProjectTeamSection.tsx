import React, { useState } from 'react';
import { Users, UserPlus } from 'lucide-react';
import { ProjectMemberItem, ProjectSummary } from '../../types';
import { useAuth } from '../../context/AuthContext';
import { ProjectMemberCard } from './ProjectMemberCard';
import { AddMemberModal } from './AddMemberModal';

export interface ProjectTeamSectionProps {
  projectId: string;
  project: ProjectSummary;
  members: ProjectMemberItem[];
  onMemberAdded: (newMember: ProjectMemberItem) => void;
  isLoading?: boolean;
}

export const ProjectTeamSection: React.FC<ProjectTeamSectionProps> = ({
  projectId,
  project,
  members,
  onMemberAdded,
}) => {
  const { user } = useAuth();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // Check if current user is owner or admin to display Add Member button
  const isOwner = user?.public_id && project.owner?.public_id === user.public_id;
  const isLead = members.some(
    (m) => m.user.public_id === user?.public_id && (m.is_owner || m.role_in_project === 'LEAD')
  );
  const isAdmin = user?.role === 'ADMIN';
  const canAddMember = isOwner || isLead || isAdmin;

  return (
    <div
      data-testid="project-team-section"
      className="p-6 sm:p-8 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-6"
    >
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shrink-0">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-tight">Project Team & Mentors</h2>
              <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
                {members.length} {members.length === 1 ? 'Member' : 'Members'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Verified student authors, contributors, and supervising faculty mentors.
            </p>
          </div>
        </div>

        {canAddMember && (
          <button
            type="button"
            onClick={() => setIsAddModalOpen(true)}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-xs font-bold text-slate-950 transition-colors shadow-lg shadow-emerald-500/20 self-start sm:self-auto shrink-0"
          >
            <UserPlus className="w-4 h-4" />
            <span>Add Member</span>
          </button>
        )}
      </div>

      {/* Member Cards Grid / Empty State */}
      {members.length === 0 ? (
        <div
          data-testid="team-empty-state"
          className="p-8 text-center rounded-2xl bg-slate-950/40 border border-slate-800/60 space-y-3"
        >
          <div className="w-10 h-10 mx-auto rounded-xl bg-slate-800/80 flex items-center justify-center text-slate-400">
            <Users className="w-5 h-5" />
          </div>
          <div className="space-y-1 max-w-sm mx-auto">
            <h3 className="text-sm font-bold text-white">No Additional Team Members Yet</h3>
            <p className="text-xs text-slate-400">
              {project.owner
                ? `Primary creator is ${project.owner.full_name}. Invite co-authors or faculty mentors to this project.`
                : 'No contributors have been added to this project.'}
            </p>
          </div>
          {canAddMember && (
            <button
              type="button"
              onClick={() => setIsAddModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-emerald-400 border border-slate-700 transition-colors"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Add Contributor</span>
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {members.map((member) => (
            <ProjectMemberCard key={member.user.public_id} member={member} />
          ))}
        </div>
      )}

      {/* Add Member Modal */}
      <AddMemberModal
        projectId={projectId}
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={(newMember) => {
          onMemberAdded(newMember);
        }}
      />
    </div>
  );
};
