import { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

type MissionContextType = {
  result: any;
  setResult: (data: any) => void;
};

const MissionContext = createContext<MissionContextType | undefined>(undefined);

export function MissionProvider({ children }: { children: ReactNode }) {
  const [result, setResult] = useState<any>(null);

  return (
    <MissionContext.Provider value={{ result, setResult }}>
      {children}
    </MissionContext.Provider>
  );
}

export function useMission() {
  const context = useContext(MissionContext);
  if (context === undefined) {
    throw new Error('useMission must be used within a MissionProvider');
  }
  return context;
}
