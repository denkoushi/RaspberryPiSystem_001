import React, { useEffect, useState } from "react";
import { LocationState } from "../../state";

export const DemoApp: React.FC = () => {
  const [state, setState] = useState<LocationState | null>(null);
  const [locations, setLocations] = useState([]);

  useEffect(() => {
    const run = async () => {
      const baseUrl = process.env.API_BASE ?? "http://localhost:8501";
      const token = process.env.API_TOKEN;
      const locationState = new LocationState(baseUrl, { baseUrl, token });
      await locationState.initialize(token);
      setState(locationState);
      setLocations([...locationState.getLocations()]);
    };
    run();
    return () => state?.dispose();
  }, []);

  useEffect(() => {
    if (!state) return;
    const interval = setInterval(() => {
      setLocations([...state.getLocations()]);
    }, 1000);
    return () => clearInterval(interval);
  }, [state]);

  return (
    <div>
      <h1>Window A Demo</h1>
      <ul>
        {locations.map((loc) => (
          <li key={loc.order_code}>
            {loc.order_code}: {loc.location_code}
          </li>
        ))}
      </ul>
    </div>
  );
};
