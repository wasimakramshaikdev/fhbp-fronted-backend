import React, { useState, useEffect } from 'react';
import { CalendarCheck, CheckCircle2, XCircle, Clock, Eye, AlertCircle, Users, IndianRupee } from 'lucide-react';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../components/ui/Table';
import { BookingStatusBadge } from '../components/ui/BookingStatusBadge';
import { Spinner, EmptyState } from '../components/ui/Feedback';
import { formatCurrency, formatDate } from '../utils/formatters';

export const OwnerBookingsPage = () => {
  const { showSuccess, showError } = useToast();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  // Decision Modals
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      const url = statusFilter ? `/owner/bookings/?status=${statusFilter}` : '/owner/bookings/';
      const res = await api.get(url);
      if (res.success) {
        setBookings(res.data);
      }
    } catch (err) {
      showError('Failed to load booking requests');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, [statusFilter]);

  const handleAccept = async (booking) => {
    try {
      setActionLoading(true);
      const res = await api.post(`/bookings/${booking.id}/accept/`, {
        notes: 'Confirmed and scheduled on venue calendar',
      });
      if (res.success) {
        showSuccess(`Booking #${booking.booking_number} accepted! Calendar slot is locked.`);
        fetchBookings();
      }
    } catch (err) {
      showError(err.message || 'Failed to accept booking');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectSubmit = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      const res = await api.post(`/bookings/${selectedBooking.id}/reject/`, {
        notes: rejectReason || 'Venue unavailable',
      });
      if (res.success) {
        showSuccess(`Booking #${selectedBooking.booking_number} declined. Customer refunded.`);
        setRejectModalOpen(false);
        setRejectReason('');
        setSelectedBooking(null);
        fetchBookings();
      }
    } catch (err) {
      showError(err.message || 'Failed to decline booking');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Booking Requests Queue</h1>
          <p className="text-sm text-slate-500 mt-1">Review incoming reservations, accept bookings, and manage customer communications</p>
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-900 focus:outline-none"
        >
          <option value="">All Requests</option>
          <option value="PENDING_OWNER_CONFIRMATION">Awaiting Response</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="COMPLETED">Completed</option>
          <option value="REJECTED">Declined</option>
          <option value="CANCELLED_BY_CUSTOMER">Cancelled by Customer</option>
        </select>
      </div>

      {loading ? (
        <div className="min-h-[40vh] flex items-center justify-center">
          <Spinner size="lg" />
        </div>
      ) : bookings.length === 0 ? (
        <EmptyState
          icon={CalendarCheck}
          title="No booking requests"
          description="There are no reservation requests matching the selected filter."
        />
      ) : (
        <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
          <Table>
            <TableHead>
              <TableRow>
                <TableHeaderCell>Booking Ref & Venue</TableHeaderCell>
                <TableHeaderCell>Customer & Contact</TableHeaderCell>
                <TableHeaderCell>Event Date & Slot</TableHeaderCell>
                <TableHeaderCell>Total & Advance</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell className="text-right">Actions</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {bookings.map((b) => {
                const isPending = b.status === 'PENDING_OWNER_CONFIRMATION';

                return (
                  <TableRow key={b.id}>
                    <TableCell>
                      <div className="font-bold text-slate-900 text-sm">#{b.booking_number}</div>
                      <div className="text-xs text-slate-500">{b.hall_name}</div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm font-medium text-slate-900">{b.customer_name}</div>
                      <div className="text-xs text-slate-500">{b.customer_email}</div>
                    </TableCell>
                    <TableCell>
                      <div className="text-xs font-bold text-slate-900">{formatDate(b.event_date)}</div>
                      <div className="text-xs text-slate-500">{b.time_slot} ({b.guest_count} guests)</div>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm font-bold text-slate-900">{formatCurrency(b.total_amount)}</div>
                      <div className="text-[11px] text-emerald-600 font-semibold">Advance: {formatCurrency(b.advance_amount)}</div>
                    </TableCell>
                    <TableCell>
                      <BookingStatusBadge status={b.status} />
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        {isPending && (
                          <>
                            <Button
                              variant="success"
                              size="sm"
                              icon={CheckCircle2}
                              onClick={() => handleAccept(b)}
                              disabled={actionLoading}
                            >
                              Accept
                            </Button>
                            <Button
                              variant="danger"
                              size="sm"
                              icon={XCircle}
                              onClick={() => {
                                setSelectedBooking(b);
                                setRejectModalOpen(true);
                              }}
                              disabled={actionLoading}
                            >
                              Decline
                            </Button>
                          </>
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

      {/* Reject Modal */}
      <Modal
        isOpen={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
        title={`Decline Booking #${selectedBooking?.booking_number}`}
        description="Provide a reason for declining. The customer will receive an immediate 100% refund of their advance payment."
      >
        <form onSubmit={handleRejectSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Reason for Declining
            </label>
            <textarea
              rows={3}
              required
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Venue is reserved for private function, maintenance ongoing..."
              className="w-full rounded-xl border border-slate-300 p-2.5 text-xs text-slate-900 focus:border-rose-500 focus:outline-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setRejectModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="danger" isLoading={actionLoading}>
              Decline & Trigger Full Refund
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
