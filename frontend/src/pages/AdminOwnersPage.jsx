import React, { useState, useEffect } from 'react';
import { Users, Search, Filter, ShieldCheck, ShieldAlert, CheckCircle2, XCircle, Power, RotateCcw } from 'lucide-react';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../components/ui/Table';
import { Spinner, EmptyState } from '../components/ui/Feedback';
import { formatDate } from '../utils/formatters';

export const AdminOwnersPage = () => {
  const { showSuccess, showError } = useToast();
  const [owners, setOwners] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchOwners = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (searchTerm) params.append('q', searchTerm);
      if (statusFilter) params.append('status', statusFilter);

      const res = await api.get(`/admin/owners/?${params.toString()}`);
      if (res.success) {
        setOwners(res.data);
      }
    } catch (err) {
      showError('Failed to load hall owners');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOwners();
  }, [statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchOwners();
  };

  const handleOwnerAction = async (ownerId, actionName, ownerName) => {
    try {
      setActionLoading(true);
      const res = await api.post(`/admin/owners/${ownerId}/action/`, { action: actionName });
      if (res.success) {
        showSuccess(res.message);
        fetchOwners();
      }
    } catch (err) {
      showError(err.message || 'Action failed');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Hall Owner Management</h1>
          <p className="text-sm text-slate-400 mt-1">Verify business registrations, monitor active listings, and manage account suspensions</p>
        </div>
      </div>

      {/* Search & Filter Bar (Wireframe Admin Screen 2) */}
      <div className="bg-slate-900 p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row gap-4 justify-between">
        <form onSubmit={handleSearchSubmit} className="flex gap-2 flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search owner or business name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 rounded-xl border border-slate-700 bg-slate-800 px-3.5 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none"
          />
          <Button type="submit" variant="primary" size="sm" icon={Search}>
            Search
          </Button>
        </form>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-semibold text-white focus:outline-none"
          >
            <option value="">All Owner States</option>
            <option value="ACTIVE">Active & Verified</option>
            <option value="UNDER_REVIEW">Under Review</option>
            <option value="SUSPENDED">Suspended</option>
          </select>
        </div>
      </div>

      {/* Owners Table (Wireframe Admin Screen 2) */}
      {loading ? (
        <div className="min-h-[40vh] flex items-center justify-center">
          <Spinner size="lg" />
        </div>
      ) : owners.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No venue owners found"
          description="There are no hall owners matching your search criteria."
        />
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <Table>
            <TableHead>
              <TableRow className="border-slate-800 bg-slate-800/60">
                <TableHeaderCell className="text-slate-300">Owner Name & Email</TableHeaderCell>
                <TableHeaderCell className="text-slate-300">Business / Venue Name</TableHeaderCell>
                <TableHeaderCell className="text-slate-300">Locality</TableHeaderCell>
                <TableHeaderCell className="text-slate-300">Venues</TableHeaderCell>
                <TableHeaderCell className="text-slate-300">Status</TableHeaderCell>
                <TableHeaderCell className="text-slate-300">Joined</TableHeaderCell>
                <TableHeaderCell className="text-slate-300 text-right">Actions</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {owners.map((owner) => {
                const isUnderReview = owner.verification_status === 'PENDING';
                const isSuspended = !owner.is_active || owner.verification_status === 'SUSPENDED';
                const isActive = owner.is_active && owner.verification_status === 'VERIFIED';

                return (
                  <TableRow key={owner.id} className="border-slate-800 hover:bg-slate-800/40">
                    <TableCell>
                      <div className="font-bold text-white text-sm">{owner.full_name}</div>
                      <div className="text-xs text-slate-400">{owner.email}</div>
                    </TableCell>
                    <TableCell>
                      <div className="text-xs font-semibold text-slate-200">{owner.business_name || 'Individual Host'}</div>
                    </TableCell>
                    <TableCell>
                      <div className="text-xs text-slate-300">{owner.locality || owner.city}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="primary" size="sm">{owner.venue_count} Halls</Badge>
                    </TableCell>
                    <TableCell>
                      {isActive && <Badge variant="success" size="sm">Active</Badge>}
                      {isUnderReview && <Badge variant="warning" size="sm">Under Review</Badge>}
                      {isSuspended && <Badge variant="danger" size="sm">Suspended</Badge>}
                    </TableCell>
                    <TableCell className="text-xs text-slate-400">
                      {formatDate(owner.joined_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        {isUnderReview && (
                          <Button
                            variant="success"
                            size="sm"
                            icon={CheckCircle2}
                            onClick={() => handleOwnerAction(owner.id, 'APPROVE', owner.full_name)}
                            disabled={actionLoading}
                          >
                            Verify & Approve
                          </Button>
                        )}
                        {isActive && (
                          <Button
                            variant="danger"
                            size="sm"
                            icon={ShieldAlert}
                            onClick={() => handleOwnerAction(owner.id, 'SUSPEND', owner.full_name)}
                            disabled={actionLoading}
                          >
                            Suspend
                          </Button>
                        )}
                        {isSuspended && (
                          <Button
                            variant="outline"
                            size="sm"
                            icon={RotateCcw}
                            onClick={() => handleOwnerAction(owner.id, 'REACTIVATE', owner.full_name)}
                            disabled={actionLoading}
                          >
                            Reactivate
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
};
