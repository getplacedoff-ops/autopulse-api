import { useState } from 'react';
import { Search, Star, ChevronRight, PenTool, ThumbsUp, ThumbsDown, Info } from 'lucide-react';
import { mockCars } from '../services/supabase';
import { Link } from 'react-router-dom';

interface UserReview {
  id: string;
  userName: string;
  rating: number;
  comment: string;
  helpfulCount: number;
  unhelpfulCount: number;
}

const mockUserReviews: UserReview[] = [
  {
    id: 'ur1',
    userName: 'Karan Malhotra',
    rating: 5,
    comment: 'The Curvv EV is a masterpiece. I have been driving it for 2 weeks now. Range is around 480km in the city.',
    helpfulCount: 12,
    unhelpfulCount: 2
  },
  {
    id: 'ur2',
    userName: 'Shreya Iyer',
    rating: 4,
    comment: 'BE 6 performance is breathtaking! However, the ride is a bit too firm on potholed roads in Bangalore.',
    helpfulCount: 8,
    unhelpfulCount: 1
  }
];

interface ReviewArticle {
  id: string;
  carName: string;
  title: string;
  rating: number;
  image: string;
  category: 'First Drive' | 'Long Term' | 'Road Test' | 'EV Review';
  author: string;
  date: string;
  readTime: string;
  verdict: string;
  pros: string[];
  cons: string[];
  breakdown: {
    performance: number;
    comfort: number;
    technology: number;
    value: number;
  };
}

const mockReviews: ReviewArticle[] = [
  {
    id: 'rev1',
    carName: 'Tata Curvv EV',
    title: 'Tata Curvv EV: Coupe-SUV Revolutionized',
    rating: 4.5,
    image: 'https://assets.autopulse.pages.dev/cars/27a6e1cf833a1763.webp',
    category: 'EV Review',
    author: 'Aarav Mehta',
    date: 'June 5, 2026',
    readTime: '6 min read',
    verdict: 'An outstanding coupe-SUV that combines premium styling with a stellar real-world range and highly competitive pricing.',
    pros: ['Gorgeous coupe styling', 'Spacious 55kWh battery variant', 'Fast DC charging support'],
    cons: ['Slightly stiff ride quality', 'Tight rear headroom due to slope'],
    breakdown: { performance: 4.5, comfort: 4.0, technology: 4.5, value: 4.8 }
  },
  {
    id: 'rev2',
    carName: 'Mahindra BE 6',
    title: 'Mahindra BE 6: Pure EV Thrills',
    rating: 4.7,
    image: 'https://assets.autopulse.pages.dev/cars/a07b464528324a70.webp',
    category: 'First Drive',
    author: 'Vikram Singh',
    date: 'June 3, 2026',
    readTime: '5 min read',
    verdict: 'The BE 6 brings a futuristic EV architecture with performance capabilities that rival cars twice its price segment.',
    pros: ['Instant torque and handling', 'Aesthetically stunning dashboard', 'Spacious interior cabin'],
    cons: ['Limited charging network support', 'Rear visibility is compromise'],
    breakdown: { performance: 4.9, comfort: 4.5, technology: 4.6, value: 4.7 }
  },
  {
    id: 'rev3',
    carName: 'Hyundai Creta Electric',
    title: 'Creta EV: The Practical Family Cruiser',
    rating: 4.4,
    image: 'https://assets.autopulse.pages.dev/cars/9a7c72a4afc35c0d.webp',
    category: 'Road Test',
    author: 'Neha Sharma',
    date: 'May 28, 2026',
    readTime: '8 min read',
    verdict: 'Creta EV takes the beloved Creta packaging and electrifies it perfectly, offering premium convenience and stress-free range.',
    pros: ['Excellent ride comfort', 'Rich feature set with V2L', 'Familiar Creta dimensions'],
    cons: ['Conservative exterior design', 'Slightly slow AC charging time'],
    breakdown: { performance: 4.2, comfort: 4.8, technology: 4.4, value: 4.3 }
  }
];

export default function ReviewsPage() {
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState('All');
  const [sortBy, setSortBy] = useState('Latest');
  
  // Review Comparison state
  const [comp1, setComp1] = useState('');
  const [comp2, setComp2] = useState('');

  const filtered = mockReviews.filter(rev => {
    if (activeTab !== 'All' && rev.category.toLowerCase() !== activeTab.toLowerCase().replace(' ', '')) return false;
    if (search && !rev.carName.toLowerCase().includes(search.toLowerCase()) && !rev.title.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const featured = mockReviews[0];

  // Map internal pipeline statuses to user-facing labels
  const publicStatusLabel = (raw: string): string => {
    const map: Record<string, string> = {
      'In Ingestion Pipeline': 'Coming Soon',
      'in ingestion pipeline': 'Coming Soon',
      'IN INGESTION PIPELINE': 'Coming Soon',
      'Embargoed until launch': 'Launching Soon',
    };
    return map[raw] || raw;
  };

  return (
    <main className="min-h-screen text-zinc-100 py-10 px-4 md:px-8 max-w-7xl mx-auto">
      
      {/* Header Section */}
      <div className="mb-8 border-b border-zinc-800 pb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight font-display bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-transparent">
            Expert Car Reviews
          </h1>
          <p className="text-sm text-zinc-500 mt-2">In-depth, unbiased evaluations from industry professionals. Find your next drive.</p>
        </div>
        <div className="relative w-full md:max-w-xs">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            placeholder="Search reviews, models, or brands..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-dark pl-11"
          />
        </div>
      </div>

      {/* Filter Tabs Row */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8 border-b border-zinc-850 pb-4">
        <div className="flex flex-wrap gap-2">
          {['All', 'First Drive', 'Long Term', 'Road Test', 'EV Reviews'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`filter-chip ${activeTab === tab ? 'active' : ''}`}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-zinc-500 font-bold uppercase tracking-wider">Sort By:</span>
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="input-dark text-xs py-2 px-4 w-40 cursor-pointer appearance-none"
            style={{ background: 'rgba(255, 255, 255, 0.03)' }}
          >
            <option value="Latest">Latest Reviews</option>
            <option value="Most Popular">Most Popular</option>
            <option value="Top Rated">Top Rated</option>
          </select>
        </div>
      </div>

      {/* Featured Review Hero Card */}
      {featured && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 p-6 rounded-3xl border border-zinc-800/60 bg-zinc-900/10 backdrop-blur-md mb-12">
          {/* Left Large Image */}
          <div className="lg:col-span-2 rounded-2xl bg-zinc-850 border border-zinc-800 min-h-64 relative overflow-hidden flex items-center justify-center text-zinc-700 font-bold text-sm uppercase tracking-widest">
            {featured.image ? (
              <img src={featured.image} alt={featured.carName} className="w-full h-full object-cover" />
            ) : (
              `[ Featured Car Image - ${featured.carName} ]`
            )}
            <div className="absolute top-4 left-4 bg-[#f43f5e] text-white text-[10px] font-black uppercase py-1 px-2.5 rounded-lg shadow-lg">
              Featured Review
            </div>
          </div>
          {/* Review Details & Scorecard */}
          <div className="space-y-5">
            <div>
              <span className="badge badge-hot py-0.5 px-2 text-[9px] mb-2">{featured.category}</span>
              <h2 className="text-2xl font-bold text-zinc-200 mt-1 font-display leading-tight">{featured.title}</h2>
              <div className="flex items-center gap-1.5 mt-2">
                <span className="text-sm font-extrabold text-zinc-300">{featured.rating}</span>
                <div className="flex text-amber-400">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star key={i} size={13} fill={i < Math.round(featured.rating) ? '#ffd60a' : 'transparent'} className={i < Math.round(featured.rating) ? 'text-[#ffd60a]' : 'text-zinc-700'} />
                  ))}
                </div>
                <span className="text-[10px] text-zinc-500 font-semibold">(4.5/5 Stars)</span>
              </div>
            </div>

            {/* Breakdown score bars */}
            <div className="space-y-2.5 bg-black/20 p-4 rounded-xl border border-zinc-850/60">
              <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Ratings Breakdown</h4>
              {[
                { label: 'Performance', val: featured.breakdown.performance },
                { label: 'Comfort', val: featured.breakdown.comfort },
                { label: 'Technology', val: featured.breakdown.technology },
                { label: 'Value', val: featured.breakdown.value }
              ].map(bar => (
                <div key={bar.label} className="text-xs">
                  <div className="flex justify-between text-[11px] font-semibold text-zinc-400 mb-1">
                    <span>{bar.label}</span>
                    <span>{bar.val.toFixed(1)}/5.0</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                    <div className="h-full bg-indigo-500" style={{ width: `${(bar.val / 5) * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Pros & Cons */}
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <p className="font-extrabold text-emerald-400 uppercase tracking-wider mb-2">Pros</p>
                <ul className="space-y-1.5 list-disc pl-4 text-zinc-400">
                  {featured.pros.slice(0, 2).map((p, i) => <li key={i}>{p}</li>)}
                </ul>
              </div>
              <div>
                <p className="font-extrabold text-rose-400 uppercase tracking-wider mb-2">Cons</p>
                <ul className="space-y-1.5 list-disc pl-4 text-zinc-400">
                  {featured.cons.slice(0, 2).map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              </div>
            </div>

            <div className="border-t border-zinc-850 pt-4 flex items-center justify-between">
              <div className="text-[10px]">
                <p className="font-bold text-zinc-300">{featured.author}</p>
                <p className="text-zinc-600">Senior Editor · {featured.date}</p>
              </div>
              <Link to="/news" className="btn-primary py-2 px-4 text-xs font-bold uppercase tracking-wider">
                Read Full Review
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Grid Content and Right Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Expert Reviews Grid */}
        <div className="lg:col-span-2 space-y-6">
          <h3 className="text-lg font-bold text-zinc-200 border-b border-zinc-850 pb-3">Expert Reviews Grid</h3>

          {/* Empty state */}
          {filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-zinc-500 border border-zinc-800 rounded-2xl bg-zinc-900/10">
              <Info size={32} className="mb-3 opacity-40" />
              <p className="text-sm font-semibold">No reviews match your filters</p>
              <p className="text-xs mt-1 opacity-60">Try a different category or clear the search.</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {filtered.map(rev => (
              <div key={rev.id} className="p-5 rounded-2xl border border-zinc-850 bg-zinc-900/10 hover:border-zinc-800 transition-all flex flex-col justify-between" style={{ position: 'relative', overflow: 'hidden' }}>
                <div className="absolute top-0 right-0 w-32 h-32 pointer-events-none overflow-hidden">
                  <div className="bg-amber-500/10 border border-amber-500/20 text-[#ffd60a] text-[8px] font-black uppercase py-1 w-48 text-center rotate-45 translate-x-12 translate-y-6">
                    Editor's Choice
                  </div>
                </div>
                <div>
                  <div className="h-40 rounded-xl bg-zinc-850 border border-zinc-800 overflow-hidden mb-4 flex items-center justify-center text-zinc-700 text-xs font-bold uppercase tracking-widest">
                    {rev.image ? (
                      <img src={rev.image} alt={rev.carName} className="w-full h-full object-cover" />
                    ) : (
                      `[ ${rev.carName} Image ]`
                    )}
                  </div>
                  <span className="badge badge-secondary py-0.5 px-2 text-[9px] mb-2">{rev.category}</span>
                  <h4 className="font-bold text-base text-zinc-200 leading-snug hover:text-[#f43f5e] transition-colors">
                    {rev.title}
                  </h4>
                  <div className="flex items-center gap-1.5 mt-2 mb-3">
                    <div className="flex text-amber-400">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star key={i} size={11} fill={i < Math.round(rev.rating) ? '#ffd60a' : 'transparent'} className={i < Math.round(rev.rating) ? 'text-[#ffd60a]' : 'text-zinc-700'} />
                      ))}
                    </div>
                    <span className="text-[10px] text-zinc-500">({rev.rating}/5)</span>
                  </div>
                  <p className="text-xs text-zinc-400 leading-relaxed mb-4 italic">
                    "{rev.verdict}"
                  </p>
                </div>
                <div className="border-t border-zinc-850 pt-4 flex items-center justify-between">
                  <div className="text-[10px] text-zinc-500">
                    <span className="font-bold text-zinc-400">{rev.author}</span> · {rev.readTime}
                  </div>
                  <Link to="/news" className="btn-secondary py-1.5 px-3 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                    Read Review <ChevronRight size={10} />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="lg:col-span-1 space-y-8">
          
          {/* Top Rated Cars */}
          <div className="p-6 rounded-3xl border border-zinc-800 bg-zinc-900/10">
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-300 border-b border-zinc-850 pb-3 mb-4">Top Rated Cars This Month</h3>
            <div className="space-y-3.5">
              {[
                { rank: 1, name: 'Mahindra BE 6', score: 4.8 },
                { rank: 2, name: 'Tata Curvv EV', score: 4.7 },
                { rank: 3, name: 'Tesla Model Y', score: 4.7 },
                { rank: 4, name: 'Hyundai Creta EV', score: 4.6 },
                { rank: 5, name: 'Tata Nexon', score: 4.5 }
              ].map(item => (
                <div key={item.rank} className="flex justify-between items-center text-sm">
                  <span className="text-zinc-400 font-semibold">{item.rank}. {item.name}</span>
                  <span className="text-xs font-bold text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">{item.score} ★</span>
                </div>
              ))}
            </div>
          </div>

          {/* Upcoming Reviews */}
          <div className="p-6 rounded-3xl border border-zinc-800 bg-zinc-900/10">
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-300 border-b border-zinc-850 pb-3 mb-4">Upcoming Reviews</h3>
            <div className="space-y-3.5">
              {[
                { name: 'Tata Sierra EV', status: 'Coming Soon' },
                { name: 'Maruti e Vitara', status: 'In Ingestion Pipeline' },
                { name: 'Hyundai Creta Facelift', status: 'Scheduled Q3' },
                { name: 'Mahindra XUV.e8', status: 'Embargoed until launch' }
              ].map(item => (
                <div key={item.name} className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-zinc-300">{item.name}</span>
                  <span className="text-[10px] text-amber-400 px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 uppercase font-black">{publicStatusLabel(item.status)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Compare Reviewed Cars Widget */}
          <div className="p-6 rounded-3xl border border-zinc-800 bg-zinc-900/10" style={{ overflow: 'hidden', maxWidth: '100%' }}>
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-300 border-b border-zinc-850 pb-3 mb-4">Compare Reviewed Cars</h3>
            <form onSubmit={e => {
              e.preventDefault();
              if (comp1 && comp2) {
                // Route to compare page
              }
            }} className="space-y-4">
              <div>
                <select
                  required
                  value={comp1}
                  onChange={e => setComp1(e.target.value)}
                  className="input-dark text-xs py-2.5"
                  style={{ background: 'rgba(255, 255, 255, 0.03)' }}
                >
                  <option value="" disabled>Select Car 1</option>
                  {mockCars.map(c => <option key={c.id} value={c.slug}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <select
                  required
                  value={comp2}
                  onChange={e => setComp2(e.target.value)}
                  className="input-dark text-xs py-2.5"
                  style={{ background: 'rgba(255, 255, 255, 0.03)' }}
                >
                  <option value="" disabled>Select Car 2</option>
                  {mockCars.map(c => <option key={c.id} value={c.slug}>{c.name}</option>)}
                </select>
              </div>
              <Link to={comp1 && comp2 ? `/compare?ids=${comp1},${comp2}` : `/compare`} className="btn-primary w-full text-center py-2.5 text-xs font-bold uppercase tracking-wider block">
                Compare Cars
              </Link>
            </form>
          </div>

          {/* User Reviews Widget */}
          <div className="p-6 rounded-3xl border border-zinc-800 bg-zinc-900/10 space-y-6">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-300 border-b border-zinc-850 pb-3 mb-4">User Reviews</h3>
              <button className="btn-primary text-xs w-full py-2.5 bg-gradient-to-r from-indigo-500 to-indigo-600 border border-indigo-500/20 flex items-center justify-center gap-2">
                <PenTool size={14} /> Write a Review
              </button>
            </div>
            
            <div className="space-y-4">
              <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Recent User Reviews</h4>
              {mockUserReviews.map(rev => (
                <div key={rev.id} className="p-4 rounded-xl border border-zinc-850 bg-zinc-950/20 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-xs text-zinc-200">{rev.userName}</span>
                    <div className="flex text-amber-400">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star key={i} size={9} fill={i < rev.rating ? '#ffd60a' : 'transparent'} className={i < rev.rating ? 'text-[#ffd60a]' : 'text-zinc-700'} />
                      ))}
                    </div>
                  </div>
                  <p className="text-[11px] text-zinc-400 leading-normal">
                    "{rev.comment}"
                  </p>
                  <div className="flex items-center gap-3 text-[9px] text-zinc-500 pt-1">
                    <span>Helpful?</span>
                    <button className="flex items-center gap-1 hover:text-white transition-colors">
                      <ThumbsUp size={10} /> {rev.helpfulCount}
                    </button>
                    <button className="flex items-center gap-1 hover:text-white transition-colors">
                      <ThumbsDown size={10} /> {rev.unhelpfulCount}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </main>
  );
}
