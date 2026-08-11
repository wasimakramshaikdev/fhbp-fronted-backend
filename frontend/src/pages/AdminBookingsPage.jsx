import React, { useState, useEffect } from 'react';
import { CalendarRange, Filter, Search, IndianRupee } from 'lucide-react';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from '../components/ui/Table';
import { BookingStatusBadge } from '../components/ui/BookingStatusBadge';
import { Spinner, EmptyState } from '../components/ui/Feedback';
import { formatCurrency, formatDate } from '../utils/formatters';

export const AdminBookingsPage = () => {
  const { showError } = useToast();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  const fetchBookings = async () => {
    try {
      setLoading(true);
      const url = statusFilter ? `/admin/bookings/?status=${statusFilter}` : '/admin/bookings/';
      const res = await api.get(url);
      if (res.success) {
        setBookings(res.data);
      }
    } catch (err) {
      showError('Failed to load bookings list');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, [statusFilter]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Platform Bookings Monitor</h1>
          <p className="text-sm text-slate-400 mt-1">Real-time oversight across all function hall bookings, escrow payments, and cancellations</p>
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-xl border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-semibold text-white focus:outline-none"
        >
          <option value="">All Booking Statuses</option>
          <option value="CONFIRMED">Confirmed</option>
          <option value="PENDING_OWNER_CONFIRMATION">Awaiting Owner</option>
          <option value="COMPLETED">Completed</option>
          <option value="DISPUTED">Disputed</option>
          <option value="CANCELLED_BY_CUSTOMER">Cancelled by Customer</option>
          <option value="REFUNDED">Refunded</option>
        </select>
      </div>

      {loading ? (
        <div className="min-h-[40vh] flex items-center justify-center">
          <Spinner size="lg" />
        </div>
      ) : bookings.length === 0 ? (
        <EmptyState
          icon={CalendarRange}
          title="No bookings found"
          description="There are no reservations matching your filter."
        />
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <Table>
            <TableHead>
              <TableRow className="border-slate-800 bg-slate-800/60">
                <TableHeaderCell className="text-slate-300">Booking Ref</TableHeaderCell>
                <TableHeaderCell className="text-slate-300">Venue</TableHeaderCell>
                <TableHeaderCell className="text-slate-300">Customer</TableHeaderCell>
                <TableHeaderCell className="text-slate-300">Event Date & Slot</TableHeaderCell>
                <TableHeaderCell className="text-slate-300">Gross Total</TableHeaderCell>
                <TableHeaderCell className="text-slate-300">Paid Amount</TableHeaderCell>
                <TableHeaderCell className="text-slate-300 text-right">Status</TableHeaderCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {bookings.map((b) => (
                <TableRow key={b.id} className="border-slate-800 hover:bg-slate-800/40">
                  <TableCell>
                    <div className="font-bold text-white text-xs">#{b.booking_number}</div>
                    <div className="text-[10px] text-slate-500">{formatDate(b.created_at)}</div>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs font-semibold text-slate-200">{b.hall_name}</div>
                    <div className="text-[10px] text-slate-400">Host: {b.owner_name}</div>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs text-slate-300 font-medium">{b.customer_name}</div>
                    <div className="text-[10px] text-slate-500">{b.customer_email}</div>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs text-slate-300">{formatDate(b.event_date)}</div>
                    <div className="text-[10px] text-slate-500">{b.time_slot} ({b.guest_count} guests)</div>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs font-bold text-slate-200">{formatCurrency(b.total_amount)}</div>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs font-bold text-emerald-400">{formatCurrency(b.amount_paid)}</div>
                  </TableCell>
                  <TableCell className="text-right">
                    <BookingStatusBadge status={b.status} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
};
