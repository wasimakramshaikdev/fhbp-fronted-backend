import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, Calendar, Users, MapPin, Sparkles, ShieldCheck, CheckCircle2, Star, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardBody } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { formatCurrency } from '../utils/formatters';

export const HomePage = () => {
  const navigate = useNavigate();
  const [city, setCity] = React.useState('Hyderabad');
  const [locality, setLocality] = React.useState('Madhapur');
  const [date, setDate] = React.useState('2026-08-12');
  const [guests, setGuests] = React.useState('350');

  const handleSearch = (e) => {
    e.preventDefault();
    navigate(`/search?city=${encodeURIComponent(city)}&locality=${encodeURIComponent(locality)}&date=${date}&guests=${guests}`);
  };

  const sampleFeatured = [
    {
      id: 1,
      name: "Grand Orchid Banquets",
      locality: "Madhapur, Hyderabad",
      rating: 4.8,
      reviews: 142,
      capacity: "200 - 600",
      price: 45000,
      image: "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?auto=format&fit=crop&w=800&q=80",
      type: "AC Banquet Hall",
    },
    {
      id: 2,
      name: "Royal Palms Convention",
      locality: "Gachibowli, Hyderabad",
      rating: 4.6,
      reviews: 98,
      capacity: "300 - 1000",
      price: 65000,
      image: "https://images.unsplash.com/photo-1545232979-8bf68ee9b1af?auto=format&fit=crop&w=800&q=80",
      type: "Convention Center",
    },
    {
      id: 3,
      name: "Sapphire Gardens & Lawn",
      locality: "Kondapur, Hyderabad",
      rating: 4.7,
      reviews: 210,
      capacity: "150 - 500",
      price: 35000,
      image: "https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?auto=format&fit=crop&w=800&q=80",
      type: "Open Lawn & Banquet",
    }
  ];

  return (
    <div className="space-y-20 pb-20">
      {/* Hero Section */}
      <section className="relative pt-12 pb-20 bg-gradient-to-b from-indigo-900 via-slate-900 to-slate-950 text-white overflow-hidden">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#ffffff_1px,transparent_1px)] [background-size:16px_16px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto space-y-5">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Verified Function Halls with Instant Slot Availability</span>
            </div>
            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
              Book the Perfect Function Hall in <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-amber-300">Hyderabad</span>
            </h1>
            <p className="text-lg text-slate-300 max-w-2xl mx-auto font-normal">
              Compare banquet halls, convention centers, and wedding lawns. Check real-time date availability, get transparent quotes, and reserve with advance payment.
            </p>
          </div>

          {/* Wireframe Hero Search Bar */}
          <div className="mt-12 max-w-5xl mx-auto bg-white p-4 sm:p-5 rounded-3xl shadow-2xl border border-slate-100 text-slate-900">
            <form onSubmit={handleSearch} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5 flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-indigo-600" /> City / Locality
                </label>
                <select
                  value={locality}
                  onChange={(e) => setLocality(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-medium text-slate-900 focus:border-indigo-600 focus:outline-none"
                >
                  <option value="Madhapur">Madhapur, Hyderabad</option>
                  <option value="Gachibowli">Gachibowli, Hyderabad</option>
                  <option value="Kondapur">Kondapur, Hyderabad</option>
                  <option value="Banjara Hills">Banjara Hills, Hyderabad</option>
                  <option value="Jubilee Hills">Jubilee Hills, Hyderabad</option>
                  <option value="Kukatpally">Kukatpally, Hyderabad</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-indigo-600" /> Event Date
                </label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-sm font-medium text-slate-900 focus:border-indigo-600 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1.5 flex items-center gap-1.5">
                  <Users className="w-3.5 h-3.5 text-indigo-600" /> Expected Guests
                </label>
                <input
                  type="number"
                  placeholder="e.g. 350"
                  value={guests}
                  onChange={(e) => setGuests(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-sm font-medium text-slate-900 focus:border-indigo-600 focus:outline-none"
                />
              </div>

              <div>
                <Button type="submit" variant="primary" size="lg" className="w-full" icon={Search}>
                  Search Halls
                </Button>
              </div>
            </form>
          </div>
        </div>
      </section>

      {/* Featured Halls Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-end justify-between mb-8">
          <div>
            <Badge variant="primary" className="mb-2">Curated Venues</Badge>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              Featured Function Halls
            </h2>
            <p className="text-sm text-slate-500 mt-1">
              Top-rated banquet and wedding venues in Hyderabad
            </p>
          </div>
          <Link to="/search" className="text-sm font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1">
            <span>View All</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {sampleFeatured.map((hall) => (
            <Card key={hall.id} className="group hover:shadow-xl transition-all duration-300 border-slate-200/80">
              <div className="relative aspect-video overflow-hidden bg-slate-100">
                <img
                  src={hall.image}
                  alt={hall.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute top-3 right-3 bg-white/95 backdrop-blur-md px-2.5 py-1 rounded-full text-xs font-bold text-slate-900 flex items-center gap-1 shadow-sm">
                  <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                  <span>{hall.rating}</span>
                  <span className="text-slate-400 font-normal">({hall.reviews})</span>
                </div>
              </div>
              <CardBody className="space-y-4">
                <div>
                  <span className="text-xs font-medium text-indigo-600 uppercase tracking-wider">{hall.type}</span>
                  <h3 className="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition">
                    {hall.name}
                  </h3>
                  <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                    <MapPin className="w-3.5 h-3.5" />
                    {hall.locality}
                  </p>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-600 pt-3 border-t border-slate-100">
                  <span className="flex items-center gap-1">
                    <Users className="w-3.5 h-3.5 text-slate-400" />
                    Up to {hall.capacity} guests
                  </span>
                  <span className="font-bold text-slate-900 text-sm">
                    {formatCurrency(hall.price)} <span className="text-xs font-normal text-slate-500">onwards</span>
                  </span>
                </div>
                <Link to={`/search?locality=${hall.locality.split(',')[0]}`}>
                  <Button variant="outline" className="w-full mt-2">
                    Check Availability
                  </Button>
                </Link>
              </CardBody>
            </Card>
          ))}
        </div>
      </section>

      {/* How It Works Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 bg-slate-100/60 rounded-3xl py-14 px-8 border border-slate-200/60">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <Badge variant="default" className="mb-2">Simple 3-Step Booking</Badge>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900">How HallBook Works</h2>
          <p className="text-slate-600 text-sm mt-2">Transparent function hall reservation with locked calendar dates and zero double booking.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 space-y-3 shadow-xs">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white font-bold flex items-center justify-center text-lg">1</div>
            <h3 className="text-lg font-bold text-slate-900">Discover & Check Slots</h3>
            <p className="text-sm text-slate-600 leading-relaxed">Search by locality, event date, and guest count. Inspect verified photos, capacity, and real-time open slots.</p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 space-y-3 shadow-xs">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white font-bold flex items-center justify-center text-lg">2</div>
            <h3 className="text-lg font-bold text-slate-900">Transparent Pricing & Hold</h3>
            <p className="text-sm text-slate-600 leading-relaxed">Select morning, evening, or full-day slots. Add catering, decor, or DJ options with an itemized price breakdown.</p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 space-y-3 shadow-xs">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white font-bold flex items-center justify-center text-lg">3</div>
            <h3 className="text-lg font-bold text-slate-900">Pay Advance & Confirm</h3>
            <p className="text-sm text-slate-600 leading-relaxed">Pay a 20% advance via secure UPI / Card. The date is locked, owner confirms, and balance is paid before the event.</p>
          </div>
        </div>
      </section>
    </div>
  );
};
