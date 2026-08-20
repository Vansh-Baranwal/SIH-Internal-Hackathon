import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MissionProvider } from './context/MissionContext';
import { Layout } from './components/layout/Layout';
import { Landing } from './pages/Landing';
import { Imagery } from './pages/Imagery';
import { Terrain } from './pages/Terrain';
import { HazardMap } from './pages/HazardMap';
import { LandingSites } from './pages/LandingSites';
import { Trajectory } from './pages/Trajectory';
import { Simulation } from './pages/Simulation';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MissionProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Landing />} />
            <Route path="imagery" element={<Imagery />} />
            <Route path="terrain" element={<Terrain />} />
            <Route path="hazard-map" element={<HazardMap />} />
            <Route path="landing-sites" element={<LandingSites />} />
            <Route path="trajectory" element={<Trajectory />} />
            <Route path="simulation" element={<Simulation />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </MissionProvider>
  </React.StrictMode>,
);
