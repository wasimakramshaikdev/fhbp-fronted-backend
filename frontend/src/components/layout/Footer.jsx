import React from 'react';
import { Link } from 'react-router-dom';
import { Building2, ShieldCheck, Phone, Mail, MapPin } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="bg-slate-950 text-slate-400 pt-16 pb-12 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-slate-800">
          {/* Brand Col */}
          <div className="space-y-4 md:col-span-1">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white">
                <Building2 className="w-5 h-5" />
              </div>
              <span className="text-xl font-black tracking-tight text-white">
                HALL<span className="text-indigo-500">BOOK</span>
              </span>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed">
              India's trusted marketplace for booking banquet halls, convention centers, and wedding lawns with real-time availability and guaranteed slot holds.
            </p>
            <div className="flex items-center gap-2 text-xs text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
              <span>100% Verified Venues & Secure Escrow</span>
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold uppercase tracking-wider text-white">Explore</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/search" className="hover:text-white transition">Browse All Halls</Link></li>
              <li><Link to="/search?city=Hyderabad&locality=Madhapur" className="hover:text-white transition">Banquets in Madhapur</Link></li>
              <li><Link to="/search?city=Hyderabad&locality=Gachibowli" className="hover:text-white transition">Venues in Gachibowli</Link></li>
              <li><Link to="/search?city=Hyderabad&locality=Kondapur" className="hover:text-white transition">Convention Centers in Kondapur</Link></li>
            </ul>
          </div>

          {/* For Hall Owners */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold uppercase tracking-wider text-white">For Venue Owners</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/owner/onboarding" className="hover:text-white transition">List Your Venue</Link></li>
              <li><Link to="/owner/earnings" className="hover:text-white transition">Owner Earnings & Commission</Link></li>
              <li><Link to="/owner/calendar" className="hover:text-white transition">Real-time Slot Manager</Link></li>
              <li><Link to="/how-it-works" className="hover:text-white transition">Partner Guidelines</Link></li>
            </ul>
          </div>

          {/* Contact & Support */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold uppercase tracking-wider text-white">Support & Contact</h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2.5">
                <MapPin className="w-4 h-4 text-indigo-400 shrink-0" />
                <span>Hitech City, Hyderabad, Telangana 500081</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Phone className="w-4 h-4 text-indigo-400 shrink-0" />
                <span>+91 (040) 4800-HALL</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Mail className="w-4 h-4 text-indigo-400 shrink-0" />
                <span>support@hallbook.in</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
          <p>© 2026 HallBook Technologies India Pvt Ltd. All rights reserved.</p>
          <div className="flex gap-6">
            <Link to="/privacy" className="hover:text-slate-400">Privacy Policy</Link>
            <Link to="/terms" className="hover:text-slate-400">Terms of Service</Link>
            <Link to="/cancellation" className="hover:text-slate-400">Cancellation & Refund Policy</Link>
          </div>
        </div>
      </div>
    </footer>
  );
};
