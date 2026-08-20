import { Link, useLocation } from 'react-router-dom';
import { Database, Satellite, Search } from 'lucide-react';
import { useMission } from '../../context/MissionContext';

export function Navbar() {
  const location = useLocation();
  const { result } = useMission();

  const links = [
    { name: 'Imagery', path: '/imagery' },
    { name: 'Terrain', path: '/terrain' },
    { name: 'Hazards', path: '/hazard-map' },
    { name: 'Landing Sites', path: '/landing-sites' },
    { name: 'Trajectory', path: '/trajectory' },
    { name: 'Simulation', path: '/simulation' },
  ];

  const hasData = result !== null;

  return (
    <header className="fixed top-6 z-50 flex justify-center w-full px-6 pointer-events-none">
      <div className="bg-white rounded-2xl shadow-xl flex items-center justify-between px-3 py-2 w-auto gap-12 border border-zinc-200 pointer-events-auto">
        <div className="flex items-center space-x-6">
          {/* Logo Component (Smaller) */}
          <Link to="/" className="flex items-center justify-center bg-black w-8 h-8 rounded-lg shadow-inner border border-blue-400 relative group overflow-hidden">
             <div className="absolute top-0.5 left-0.5 w-1 h-1 border-t border-l border-blue-400"></div>
             <div className="absolute top-0.5 right-0.5 w-1 h-1 border-t border-r border-blue-400"></div>
             <div className="absolute bottom-0.5 left-0.5 w-1 h-1 border-b border-l border-blue-400"></div>
             <div className="absolute bottom-0.5 right-0.5 w-1 h-1 border-b border-r border-blue-400"></div>
             
             <Satellite className="w-4 h-4 text-white" />
          </Link>
          
          <nav className="hidden lg:flex space-x-5 items-center">
            {links.map((link) => (
              <Link
                key={link.name}
                to={link.path}
                className={`text-[13px] transition-colors ${
                  location.pathname === link.path 
                    ? 'text-black font-bold' 
                    : 'text-zinc-500 font-medium hover:text-zinc-800'
                }`}
              >
                {link.name}
              </Link>
            ))}
          </nav>
        </div>

        <div className="flex items-center space-x-5">
          <Search className="w-4 h-4 text-zinc-500 cursor-pointer hover:text-black transition-colors" />
          
          <div className="flex items-center space-x-2 border-l border-zinc-200 pl-5 text-[12px] font-semibold pr-2">
            <Database className={`w-3.5 h-3.5 ${hasData ? 'text-green-500' : 'text-amber-500'}`} />
            <span className={hasData ? 'text-green-600' : 'text-amber-600'}>
              {hasData ? 'Data Loaded' : 'Awaiting Data'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
