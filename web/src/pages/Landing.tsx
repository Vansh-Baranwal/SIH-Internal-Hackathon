import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ChevronRight, Crosshair, Map, Activity, Mountain } from 'lucide-react';
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export function Landing() {
  const { hash } = useLocation();

  useEffect(() => {
    if (hash === '#about') {
      const element = document.getElementById('about');
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    } else if (hash === '#mission') {
      const element = document.getElementById('mission');
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
      }
    }
  }, [hash]);

  return (
    <div className="flex flex-col font-sans">
      {/* Hero */}
      <section className="relative min-h-[85vh] flex flex-col justify-center pt-32 pb-16 px-8 lg:px-24 overflow-hidden border-b border-white/5 bg-[#0a0a0a]">
        <div className="absolute inset-0 bg-gradient-to-r from-[#050505] via-[#050505]/90 to-transparent z-10" />
        
        {/* Moon Image */}
        <img 
          src="/src/assets/moon.webp" 
          className="absolute bottom-0 right-0 w-[1000px] lg:w-[1300px] 2xl:w-[1600px] max-w-none object-contain translate-x-[50%] translate-y-[50%] opacity-40 mix-blend-screen pointer-events-none z-0" 
          style={{ WebkitMaskImage: 'linear-gradient(to bottom, transparent 0%, black 15%)', maskImage: 'linear-gradient(to bottom, transparent 0%, black 15%)' }}
        />
        
        <motion.div 
          initial={{ opacity: 0, y: 30 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 1, ease: 'easeOut' }}
          className="relative z-20 max-w-4xl mt-16"
        >
          <h1 className="text-7xl lg:text-9xl font-black tracking-tight mb-8 leading-[1.1]">
            <span className="block text-white">Luna</span>
            <span className="block text-blue-500">Drishti</span>
          </h1>
          
          <p className="text-lg lg:text-xl text-zinc-400 leading-relaxed mb-12 max-w-2xl font-medium">
            A geospatial intelligence platform for converting Chandrayaan-2 lunar observations into high-fidelity terrain hazard maps, landing-site assessments, and interactive descent trajectory physics.
          </p>
          
          <div className="flex space-x-6">
            <Link to="/imagery" className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20 rounded-xl font-semibold px-8 py-4 tracking-wide transition-colors">
              <span>Launch Platform</span>
              <ChevronRight className="w-5 h-5" />
            </Link>
            <button onClick={() => {
              const el = document.getElementById('mission');
              if (el) el.scrollIntoView({ behavior: 'smooth' });
            }} className="flex items-center space-x-2 bg-white/5 hover:bg-white/10 text-white rounded-xl border border-white/10 font-semibold px-8 py-4 tracking-wide transition-colors">
              <span>Read Documentation</span>
            </button>
          </div>
        </motion.div>
      </section>

      {/* Mission Overview Section */}
      <section id="mission" className="relative py-32 px-8 lg:px-24 bg-[#0a0a0a] overflow-hidden">
        {/* Glow */}
        <div className="absolute top-0 right-1/4 w-[600px] h-[600px] bg-blue-600/5 rounded-full blur-[150px] pointer-events-none mix-blend-screen" />

        <motion.div 
          initial={{ opacity: 0, y: 50 }} 
          whileInView={{ opacity: 1, y: 0 }} 
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="relative max-w-[1400px] mx-auto p-10 lg:p-16 rounded-[2rem] bg-white/[0.015] backdrop-blur-2xl border border-white/10 shadow-2xl mb-16"
        >
          <div className="flex flex-col items-center mb-16 text-center">
            <p className="text-zinc-500 font-bold tracking-widest text-[10px] uppercase mb-4">The Challenge</p>
            <h2 className="text-5xl lg:text-[4rem] font-semibold text-white tracking-tighter mb-4 leading-tight">Mission Overview</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
            <div>
              <h3 className="text-lg font-medium text-white mb-6 tracking-tight">Problem Statement</h3>
              <p className="text-zinc-500 text-sm leading-relaxed tracking-tight mb-4">
                Safe autonomous lunar landings require detailed prior knowledge of the target terrain. Existing optical imagery often lacks the resolution required to identify sub-meter hazards (boulders, craters) and steep local slopes.
              </p>
              <p className="text-zinc-500 text-sm leading-relaxed tracking-tight">
                Without physical elevation data and mathematically rigorous hazard mapping, mission planners cannot accurately predict the Delta-V required to reach a safe touchdown zone.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-6 tracking-tight">Key Objectives</h3>
              <ul className="space-y-4 text-sm text-zinc-500 tracking-tight">
                <li className="flex items-start">
                  <span className="text-blue-500 font-medium mr-4">01</span> 
                  <span>Enhance optical imagery resolution using deep learning (CSASR).</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 font-medium mr-4">02</span> 
                  <span>Integrate physical DEMs to derive true elevation.</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 font-medium mr-4">03</span> 
                  <span>Map hazards including slopes, craters, and roughness.</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 font-medium mr-4">04</span> 
                  <span>Evaluate sites dynamically against strict lander physics.</span>
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 font-medium mr-4">05</span> 
                  <span>Validate descent reachability and Delta-V costs.</span>
                </li>
              </ul>
            </div>
          </div>
        </motion.div>

          {/* Glassmorphic Pipeline Section */}
          <div className="relative mt-32 w-full max-w-[1400px] mx-auto">
            {/* Decorative Ambient Glows */}
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-[120px] pointer-events-none mix-blend-screen" />
            <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[120px] pointer-events-none mix-blend-screen" />

            {/* Glass Card */}
            <motion.div 
              initial={{ opacity: 0, y: 50 }} 
              whileInView={{ opacity: 1, y: 0 }} 
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              className="relative grid grid-cols-1 lg:grid-cols-12 gap-16 lg:gap-24 items-center p-10 lg:p-16 rounded-[2rem] bg-white/[0.015] backdrop-blur-2xl border border-white/10 shadow-2xl"
            >
              
              {/* Left Column: Big Title */}
              <div className="lg:col-span-5 flex flex-col items-center lg:items-start text-center lg:text-left h-full justify-center">
                <p className="text-zinc-500 font-bold tracking-widest text-[10px] uppercase mb-6">Methodology</p>
                <h3 className="text-6xl lg:text-[5rem] font-semibold text-white tracking-tighter mb-8 leading-[1.05]">
                  Scientific<br/>Pipeline
                </h3>
                <p className="text-zinc-500 text-xs font-medium tracking-wide">Scope: 6 Phases | Execution: Automated</p>
              </div>
              
              {/* Right Column: List */}
              <div className="lg:col-span-7 flex flex-col w-full">
                <div className="border-t border-white/10"></div>
                {[
                  { step: "01", title: "Data Ingestion", desc: "Process raw TMC ortho-images and physical Digital Elevation Models" },
                  { step: "02", title: "Super Resolution", desc: "Execute CNN models to upscale optical resolution to 1m/px" },
                  { step: "03", title: "DEM Registration", desc: "Correlate optical imagery with physical topography" },
                  { step: "04", title: "Hazard Mapping", desc: "Compute physical slopes, detect craters, and map surface roughness" },
                  { step: "05", title: "Site Evaluation", desc: "Score terrain against specific lander geometry and safety constraints" },
                  { step: "06", title: "Flight Dynamics", desc: "Calculate descent trajectories and optimal propulsive routing" }
                ].map((module, i) => (
                  <motion.div 
                    initial={{ opacity: 0, x: 20 }} 
                    whileInView={{ opacity: 1, x: 0 }} 
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1, duration: 0.5 }}
                    key={module.step} 
                    className="flex py-7 border-b border-white/10 group hover:bg-white/[0.02] transition-colors pr-4"
                  >
                    <div className="w-16 flex-shrink-0 text-zinc-600 font-medium text-sm mt-0.5">{module.step}</div>
                    <div>
                      <h4 className="text-zinc-100 font-medium text-xl tracking-tight mb-1">{module.title}</h4>
                      <p className="text-zinc-500 text-sm tracking-tight">{module.desc}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
      </section>



      {/* About Glassmorphic Section */}
      <section id="about" className="relative py-32 px-8 lg:px-24 bg-[#0a0a0a] overflow-hidden">
        {/* Glow */}
        <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[150px] pointer-events-none mix-blend-screen" />

        <motion.div 
          initial={{ opacity: 0, y: 50 }} 
          whileInView={{ opacity: 1, y: 0 }} 
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="relative max-w-[1400px] mx-auto p-10 lg:p-16 rounded-[2rem] bg-white/[0.015] backdrop-blur-2xl border border-white/10 shadow-2xl"
        >
          <div className="flex flex-col items-center mb-16 text-center">
            <p className="text-zinc-500 font-bold tracking-widest text-[10px] uppercase mb-4">Project Overview</p>
            <h2 className="text-5xl lg:text-[4rem] font-semibold text-white tracking-tighter mb-4 leading-tight">About The Platform</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-16 mb-24">
            <div>
              <h3 className="text-lg font-medium text-white mb-4 tracking-tight">Scientific Motivation</h3>
              <p className="text-zinc-500 text-sm leading-relaxed tracking-tight">
                The Lunar Hazard Mapper is a demonstration platform designed to showcase an end-to-end autonomous hazard detection and landing site evaluation pipeline. Using Chandrayaan-2 TMC and TMCDTM datasets, the platform bridges the gap between raw orbital telemetry, deep-learning based optical super-resolution (CSASR), and physical engineering constraints for lunar descent vehicles.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-medium text-white mb-4 tracking-tight">Data Sources</h3>
              <p className="text-zinc-500 text-sm leading-relaxed tracking-tight">
                This project relies on verified <b>Chandrayaan-2 TMC</b> optical imagery and <b>TMCDTM</b> physical elevation models. No estimated elevations or fabricated parameters are used in the final trajectory decisions, ensuring engineering-grade validation for mission planning.
              </p>
            </div>
          </div>

          <div className="border-t border-white/5 pt-16">
            <div className="flex flex-col items-center mb-12 text-center">
              <h3 className="text-2xl font-medium text-white tracking-tight mb-2">Technology Stack</h3>
              <p className="text-zinc-500 text-xs font-medium tracking-wide uppercase">Core Architecture</p>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6 text-center">
              {[
                { type: "Frontend", name: "React & Vite" },
                { type: "3D Physics", name: "Three.js & R3F" },
                { type: "Styling", name: "Tailwind CSS" },
                { type: "Backend API", name: "FastAPI" },
                { type: "Geospatial", name: "Rasterio / GDAL" },
                { type: "Neural Nets", name: "PyTorch" }
              ].map((stack, i) => (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95 }} 
                  whileInView={{ opacity: 1, scale: 1 }} 
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1, duration: 0.5 }}
                  key={i} 
                  className="flex flex-col justify-center items-center h-full py-4"
                >
                  <span className="text-[10px] tracking-widest text-blue-500 uppercase font-bold mb-3">{stack.type}</span>
                  <span className="text-zinc-100 font-medium text-sm tracking-tight">{stack.name}</span>
                </motion.div>
              ))}
            </div>
          </div>
        </motion.div>
      </section>
    </div>
  );
}
