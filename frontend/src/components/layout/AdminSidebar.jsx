import React from 'react';
import { NavLink } from 'react-router-dom';
import { ShieldAlert, Users, Building2, CalendarRange, Scale, Settings2, FileText } from 'lucide-react';
import { cn } from '../../utils/cn';

export const AdminSidebar = () => {
  const links = [
    { name: 'Control Plane Overview', path: '/admin', icon: ShieldAlert },
    { name: 'Hall Owners', path: '/admin/owners', icon: Users },
    { name: 'Halls & Approvals', path: '/admin/halls', icon: Building2 },
    { name: 'Bookings & Escrow', path: '/admin/bookings', icon: CalendarRange },
    { name: 'Disputes & Refunds', path: '/admin/disputes', icon: Scale },
    { name: 'Platform Settings', path: '/admin/settings', icon: Settings2 },
    { name: 'Audit Trail', path: '/admin/audit-logs', icon: FileText },
  ];

  return (
    <aside className="w-64 shrink-0 bg-slate-900 text-slate-300 rounded-2xl border border-slate-800 p-4 shadow-xl">
      <div className="px-3 py-2 mb-3 border-b border-slate-800 pb-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-rose-400">Super Admin Panel</h3>
        <p className="text-[11px] text-slate-500 mt-0.5">Platform Governance</p>
      </div>
      <nav className="space-y-1">
        {links.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/admin'}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition",
                  isActive
                    ? "bg-rose-500/10 text-rose-400 border border-rose-500/20 font-semibold"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
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
