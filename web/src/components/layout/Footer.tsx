import { Link } from 'react-router-dom';

export function Footer() {
  return (
    <footer className="border-t border-white/5 bg-[#050505] text-zinc-500 py-6 px-8 mt-auto font-sans">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="col-span-2">
          <h2 className="text-zinc-300 font-bold tracking-wide mb-4">LunaDrishti</h2>
          <p className="text-sm font-medium leading-relaxed max-w-sm">
            High-fidelity geospatial intelligence platform for generating terrain-aware hazard maps, dual-lander feasibility assessments, and propulsive descent trajectory simulations.
          </p>
        </div>
        
        <div>
          <h3 className="text-white tracking-widest uppercase font-bold mb-4 text-[11px]">Navigation</h3>
          <ul className="space-y-2 text-sm font-medium">
            <li><Link to="/imagery" className="hover:text-blue-400 transition-colors">Imagery</Link></li>
            <li><Link to="/terrain" className="hover:text-blue-400 transition-colors">Terrain</Link></li>
            <li><Link to="/hazard-map" className="hover:text-blue-400 transition-colors">Hazards</Link></li>
            <li><Link to="/landing-sites" className="hover:text-blue-400 transition-colors">Landing Sites</Link></li>
            <li><Link to="/trajectory" className="hover:text-blue-400 transition-colors">Trajectory</Link></li>
            <li><Link to="/simulation" className="hover:text-blue-400 transition-colors">Simulation</Link></li>
          </ul>
        </div>

        <div>
          <h3 className="text-white tracking-widest uppercase font-bold mb-4 text-[11px]">Core Systems</h3>
          <ul className="space-y-2 text-sm font-medium">
            <li>Deep Learning (CSASR)</li>
            <li>Physical Topography</li>
            <li>Hazard Classification</li>
            <li>Site Feasibility</li>
            <li>Orbital Dynamics</li>
          </ul>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto mt-8 pt-6 border-t border-white/5 text-[11px] font-semibold tracking-widest uppercase flex flex-col sm:flex-row gap-4 justify-between">
        <p>&copy; 2026 LUNADRISHTI</p>
        <p>BUILT BY CTRL Z</p>
      </div>
    </footer>
  );
}
