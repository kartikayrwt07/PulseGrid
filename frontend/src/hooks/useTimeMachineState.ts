import { useEffect, useState } from "react";
import type { ScoringEngineMode } from "../components/faculty/TimeMachineBar";
import { useTimeMachine } from "./useTimeMachine";

export function useTimeMachineState() {
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>(undefined);
  const [playing, setPlaying] = useState(false);
  const [engine, setEngine] = useState<ScoringEngineMode>("pulsegrid");

  const query = useTimeMachine(selectedWeek);
  const availableWeeks = query.data?.available_weeks ?? [4, 5, 6, 7, 8, 9];
  const currentWeek = selectedWeek ?? query.data?.active_week ?? 9;

  useEffect(() => {
    if (!playing || availableWeeks.length === 0) return undefined;
    const id = window.setInterval(() => {
      setSelectedWeek((prev) => {
        const cur = prev ?? query.data?.active_week ?? availableWeeks[availableWeeks.length - 1];
        const idx = availableWeeks.indexOf(cur);
        const nextIdx = idx < 0 || idx + 1 >= availableWeeks.length ? 0 : idx + 1;
        return availableWeeks[nextIdx];
      });
    }, 1200);
    return () => window.clearInterval(id);
  }, [playing, availableWeeks, query.data?.active_week]);

  const selectWeek = (wk: number) => {
    setPlaying(false);
    setSelectedWeek(wk);
  };

  return {
    query,
    selectedWeek: currentWeek,
    selectWeek,
    playing,
    togglePlay: () => setPlaying((p) => !p),
    engine,
    setEngine,
  };
}
