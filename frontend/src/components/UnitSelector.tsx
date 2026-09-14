import React, { useEffect } from 'react';
import { setActiveUnit } from '../services/api';

interface UnitSelectorProps {
  units: { unit_id: number; unit_name: string; role: string }[];
  currentUnit: number | null;
  setCurrentUnit: (unit: number) => void;
}

export const UnitSelector: React.FC<UnitSelectorProps> = ({ units, currentUnit, setCurrentUnit }) => {
  useEffect(() => {
    if (units.length > 0 && !currentUnit) {
      setCurrentUnit(units[0].unit_id);
    }
  }, [units, currentUnit, setCurrentUnit]);

  useEffect(() => {
    setActiveUnit(currentUnit);
  }, [currentUnit]);

  if (units.length === 0) {
    return <div className="text-white text-sm">Sem unidades</div>;
  }

  return (
    <div className="flex items-center space-x-2">
      <label className="text-slate-300 text-sm">Unidade atual:</label>
      <select
        value={currentUnit || ''}
        onChange={(e) => setCurrentUnit(Number(e.target.value))}
        className="bg-slate-700 text-white rounded p-1 text-sm border-none focus:ring-0 cursor-pointer"
      >
        {units.map((u) => (
          <option key={u.unit_id} value={u.unit_id}>
            {u.unit_name}
          </option>
        ))}
      </select>
    </div>
  );
};
