import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, CalendarCheck, CalendarDays, Building, IndianRupee, MessageSquareQuote, Settings } from 'lucide-react';
import { cn } from '../../utils/cn';

export const OwnerSidebar = () => {
  const links = [
    { name: 'Dashboard', path: '/owner/dashboard', icon: LayoutDashboard },
    { name: 'Booking Requests', path: '/owner/bookings', icon: CalendarCheck },
    { name: 'Availability Calendar', path: '/owner/calendar', icon: CalendarDays },
    { name: 'My Listings', path: '/owner/listings', icon: Building },
    { name: 'Earnings & Payouts', path: '/owner/earnings', icon: IndianRupee },
    { name: 'Guest Reviews', path: '/owner/reviews', icon: MessageSquareQuote },
    { name: 'Venue Settings', path: '/owner/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 shrink-0 bg-white rounded-2xl border border-slate-200/80 p-4 shadow-xs">
      <div className="px-3 py-2 mb-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-600">Venue Owner Portal</h3>
      </div>
      <nav className="space-y-1">
        {links.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition",
                  isActive
                    ? "bg-indigo-50 text-indigo-700 font-semibold"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                )
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {item.name}
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
};
