import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Building2, CreditCard, XCircle, Star, Eye, AlertCircle, CheckCircle2, IndianRupee } from 'lucide-react';
import api from '../services/api';
import { useToast } from '../context/ToastContext';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { BookingStatusBadge } from '../components/ui/BookingStatusBadge';
import { Spinner, EmptyState } from '../components/ui/Feedback';
import { formatCurrency, formatDate } from '../utils/formatters';

export const MyBookingsPage = () => {
  const { showSuccess, showError } = useToast();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  // Selected Booking Modals
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [payBalanceModalOpen, setPayBalanceModalOpen] = useState(false);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [cancelReason, setCancelReason] = useState('');
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewComment, setReviewComment] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchBookings = async () => {
    try {
      setLoading(true);
      const res = await api.get('/bookings/');
      if (res.success) {
        setBookings(res.data);
      }
    } catch (err) {
      showError('Failed to load your bookings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, []);

  const handleCancelBooking = async (e) => {
    e.preventDefault();
    if (!cancelReason.trim()) {
      showError('Please provide a cancellation reason');
      return;
    }

    try {
      setActionLoading(true);
      const res = await api.post(`/bookings/${selectedBooking.id}/cancel/`, {
        reason: cancelReason,
      });
      if (res.success) {
        showSuccess(res.message);
        setCancelModalOpen(false);
        setCancelReason('');
        fetchBookings();
      }
    } catch (err) {
      showError(err.message || 'Failed to cancel booking');
    } finally {
      setActionLoading(false);
    }
  };

  const handlePayBalance = async () => {
    try {
      setActionLoading(true);
      const initRes = await api.post('/payments/razorpay/order/', {
        booking_id: selectedBooking.id,
        payment_type: 'BALANCE',
      });

      if (!initRes.success || !initRes.data?.gateway_order_id) {
        throw new Error(initRes.message || 'Payment initiation failed');
      }

      const orderData = initRes.data;

      const completeVerification = async (verifyPayload) => {
        const verifyRes = await api.post('/payments/razorpay/verify/', verifyPayload);
        if (!verifyRes.success) {
          throw new Error(verifyRes.message || 'Payment verification failed');
        }
        showSuccess('Balance payment verified and confirmed!');
        setPayBalanceModalOpen(false);
        fetchBookings();
      };

      const loadRazorpayScript = () => {
        return new Promise((resolve) => {
          if (typeof window !== 'undefined' && window.Razorpay) {
            resolve(true);
            return;
          }
          const script = document.createElement('script');
          script.src = 'https://checkout.razorpay.com/v1/checkout.js';
          script.async = true;
          script.onload = () => resolve(true);
          script.onerror = () => resolve(false);
          document.body.appendChild(script);
        });
      };

      const scriptLoaded = await loadRazorpayScript();

      if (scriptLoaded && window.Razorpay && orderData.key_id && !orderData.key_id.startsWith('sim_')) {
        const options = {
          key: orderData.key_id,
          amount: orderData.amount_subunits || Math.round(orderData.amount * 100),
          currency: orderData.currency || 'INR',
          name: 'HallBook',
          description: `Balance Settlement for Booking #${selectedBooking.booking_number}`,
          image: '/favicon.svg',
          order_id: orderData.gateway_order_id || orderData.order_id,
          handler: async function (response) {
            try {
              setActionLoading(true);
              await completeVerification({
                gateway_order_id: response.razorpay_order_id,
                gateway_payment_id: response.razorpay_payment_id,
                gateway_signature: response.razorpay_signature,
              });
            } catch (err) {
              showError(err.message || 'Payment verification failed');
            } finally {
              setActionLoading(false);
            }
          },
          prefill: {
            name: orderData.contact_name || '',
            email: orderData.contact_email || '',
            contact: orderData.contact_phone || '',
          },
          theme: {
            color: '#4f46e5',
          },
          modal: {
            ondismiss: function () {
              setActionLoading(false);
            },
          },
        };
        const rzp = new window.Razorpay(options);
        rzp.open();
      } else {
        await completeVerification({
          gateway_order_id: orderData.gateway_order_id,
          gateway_payment_id: `pay_sim_${Date.now()}`,
          gateway_signature: 'valid_simulated_signature',
        });
      }
    } catch (err) {
      showError(err.message || 'Balance payment failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    if (!reviewComment.trim()) {
      showError('Please write a comment sharing your experience');
      return;
    }

    try {
      setActionLoading(true);
      const res = await api.post(`/bookings/${selectedBooking.id}/review/`, {
        rating: reviewRating,
        comment: reviewComment,
      });
      if (res.success) {
        showSuccess('Thank you! Your verified review has been published.');
        setReviewModalOpen(false);
        setReviewComment('');
        setReviewRating(5);
        fetchBookings();
      }
    } catch (err) {
      showError(err.message || 'Failed to submit review');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">My Function Hall Bookings</h1>
        <p className="text-sm text-slate-500 mt-1">Track event dates, manage balance payments, and view cancellation refunds</p>
      </div>

      {bookings.length === 0 ? (
        <EmptyState
          icon={Calendar}
          title="No bookings yet"
          description="You haven't made any function hall reservations yet. Browse Hyderabad venues to get started."
          action={
            <Link to="/search">
              <Button variant="primary">Browse Function Halls</Button>
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {bookings.map((b) => {
            const isConfirmed = b.status === 'CONFIRMED';
            const isPendingOwner = b.status === 'PENDING_OWNER_CONFIRMATION';
            const isCompleted = b.status === 'COMPLETED';
            const isPaidFull = parseFloat(b.amount_paid) >= parseFloat(b.total_amount);
            const balanceDue = parseFloat(b.total_amount) - parseFloat(b.amount_paid);

            return (
              <Card key={b.id} className="border-slate-200 shadow-xs overflow-hidden">
                <div className="flex flex-col sm:flex-row">
                  <div className="w-full sm:w-48 aspect-video sm:aspect-auto bg-slate-100 relative">
                    <img
                      src={b.primary_image || "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?auto=format&fit=crop&w=400&q=80"}
                      alt={b.hall_name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="flex-1 p-6 space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-400">#{b.booking_number}</span>
                          <BookingStatusBadge status={b.status} />
                        </div>
                        <h3 className="text-lg font-bold text-slate-900 mt-1">{b.hall_name}</h3>
                        <p className="text-xs text-slate-500">{b.hall_locality}, {b.hall_city}</p>
                      </div>

                      <div className="text-right">
                        <div className="text-base font-bold text-slate-900">
                          {formatCurrency(b.amount_paid)} <span className="text-xs font-normal text-slate-400">/ {formatCurrency(b.total_amount)}</span>
                        </div>
                        <span className="text-[11px] text-emerald-600 font-semibold">
                          {isPaidFull ? "Fully Paid" : `Balance Due: ${formatCurrency(balanceDue)}`}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 py-3 border-y border-slate-100 text-xs text-slate-600">
                      <div>Date: <span className="font-semibold text-slate-900">{formatDate(b.event_date)}</span></div>
                      <div>Slot: <span className="font-semibold text-slate-900">{b.time_slot}</span></div>
                      <div>Guests: <span className="font-semibold text-slate-900">{b.guest_count} Expected</span></div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                      <Button
                        variant="outline"
                        size="sm"
                        icon={Eye}
                        onClick={() => {
                          setSelectedBooking(b);
                          setDetailModalOpen(true);
                        }}
                      >
                        View Breakdown
                      </Button>

                      <div className="flex items-center gap-2">
                        {isConfirmed && !isPaidFull && (
                          <Button
                            variant="primary"
                            size="sm"
                            icon={IndianRupee}
                            onClick={() => {
                              setSelectedBooking(b);
                              setPayBalanceModalOpen(true);
                            }}
                          >
                            Pay Balance ({formatCurrency(balanceDue)})
                          </Button>
                        )}

                        {isCompleted && (
                          <Button
                            variant="primary"
                            size="sm"
                            icon={Star}
                            onClick={() => {
                              setSelectedBooking(b);
                              setReviewModalOpen(true);
                            }}
                          >
                            Leave a Review
                          </Button>
                        )}

                        {(isConfirmed || isPendingOwner) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-rose-600 hover:bg-rose-50"
                            icon={XCircle}
                            onClick={() => {
                              setSelectedBooking(b);
                              setCancelModalOpen(true);
                            }}
                          >
                            Cancel Booking
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Breakdown Details Modal */}
      {selectedBooking && (
        <Modal
          isOpen={detailModalOpen}
          onClose={() => setDetailModalOpen(false)}
          title={`Booking Details: #${selectedBooking.booking_number}`}
          description={`${selectedBooking.hall_name} on ${formatDate(selectedBooking.event_date)}`}
        >
          <div className="space-y-4 text-xs text-slate-600">
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
              <div className="flex justify-between">
                <span>Status:</span>
                <BookingStatusBadge status={selectedBooking.status} />
              </div>
              <div className="flex justify-between">
                <span>Time Slot:</span>
                <span className="font-bold text-slate-900">{selectedBooking.time_slot}</span>
              </div>
              <div className="flex justify-between">
                <span>Expected Guests:</span>
                <span className="font-bold text-slate-900">{selectedBooking.guest_count}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-slate-200">
                <span>Total Quotation:</span>
                <span className="font-bold text-slate-900">{formatCurrency(selectedBooking.total_amount)}</span>
              </div>
              <div className="flex justify-between text-emerald-700 font-bold">
                <span>Amount Paid:</span>
                <span>{formatCurrency(selectedBooking.amount_paid)}</span>
              </div>
            </div>
            <div className="flex justify-end">
              <Button variant="primary" onClick={() => setDetailModalOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Cancellation Modal */}
      {selectedBooking && (
        <Modal
          isOpen={cancelModalOpen}
          onClose={() => setCancelModalOpen(false)}
          title={`Cancel Booking #${selectedBooking.booking_number}`}
          description="Are you sure you want to cancel this reservation?"
        >
          <form onSubmit={handleCancelBooking} className="space-y-4">
            <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-900 rounded-xl text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>
                Refund will be calculated automatically based on the venue's cancellation policy and days remaining until the event.
              </span>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Reason for Cancellation
              </label>
              <textarea
                rows={3}
                required
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                placeholder="e.g. Change in wedding date, personal emergency..."
                className="w-full rounded-xl border border-slate-300 p-2.5 text-xs text-slate-900 focus:border-rose-500 focus:outline-none"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setCancelModalOpen(false)}>
                Keep Booking
              </Button>
              <Button type="submit" variant="danger" isLoading={actionLoading}>
                Confirm Cancellation
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Pay Balance Modal */}
      {selectedBooking && (
        <Modal
          isOpen={payBalanceModalOpen}
          onClose={() => setPayBalanceModalOpen(false)}
          title="Pay Outstanding Balance"
          description={`Settlement for booking #${selectedBooking.booking_number}`}
        >
          <div className="space-y-4 text-xs">
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
              <div className="flex justify-between">
                <span>Total Booking Amount:</span>
                <span className="font-semibold text-slate-900">{formatCurrency(selectedBooking.total_amount)}</span>
              </div>
              <div className="flex justify-between">
                <span>Advance Already Paid:</span>
                <span className="font-semibold text-emerald-600">-{formatCurrency(selectedBooking.amount_paid)}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-slate-200 text-sm font-bold text-indigo-600">
                <span>Balance Due Now:</span>
                <span>{formatCurrency(parseFloat(selectedBooking.total_amount) - parseFloat(selectedBooking.amount_paid))}</span>
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setPayBalanceModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" onClick={handlePayBalance} isLoading={actionLoading}>
                Pay Balance via UPI / Card
              </Button>
            </div>
          </div>
        </Modal>
      )}
      {/* Leave Review Modal */}
      {selectedBooking && (
        <Modal
          isOpen={reviewModalOpen}
          onClose={() => setReviewModalOpen(false)}
          title={`Rate & Review: ${selectedBooking.hall_name}`}
          description={`Verified review for event completed on ${formatDate(selectedBooking.event_date)}`}
        >
          <form onSubmit={handleReviewSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Star Rating
              </label>
              <div className="flex items-center gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setReviewRating(star)}
                    className="p-1 text-2xl focus:outline-none transition transform hover:scale-110"
                  >
                    <Star
                      className={`w-7 h-7 ${
                        reviewRating >= star ? 'text-amber-500 fill-amber-500' : 'text-slate-200'
                      }`}
                    />
                  </button>
                ))}
                <span className="text-sm font-bold text-slate-800 ml-2">{reviewRating}.0 Stars</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Your Review & Experience
              </label>
              <textarea
                rows={4}
                required
                value={reviewComment}
                onChange={(e) => setReviewComment(e.target.value)}
                placeholder="Share your thoughts about the ambience, air conditioning, stage lighting, and staff hospitality..."
                className="w-full rounded-xl border border-slate-300 p-3 text-xs text-slate-900 focus:border-indigo-600 focus:outline-none"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setReviewModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" isLoading={actionLoading}>
                Submit Verified Review
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
