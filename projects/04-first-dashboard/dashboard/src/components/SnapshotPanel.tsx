// The container. This is the whole point of the rung: one hook, useCommand, turns
// a pack command into {execute, data, loading, error}. The dashboard never imports
// the pack or talks to a model; it calls a command and renders the typed result.

import { useState } from "react";
import { useCommand } from "@huitzo/dashboard-sdk-react";

import { COUNTRY_SNAPSHOT, type CountrySnapshot, type Indicator } from "../types";
import { SnapshotView } from "./SnapshotView";

export function SnapshotPanel() {
  const [country, setCountry] = useState("USA");
  const [indicator, setIndicator] = useState<Indicator>("inflation");

  // useCommand handles the execute/loading/error/data state machine for us.
  const { execute, data, loading, error } = useCommand<CountrySnapshot>(COUNTRY_SNAPSHOT);

  return (
    <SnapshotView
      country={country}
      indicator={indicator}
      onCountry={setCountry}
      onIndicator={setIndicator}
      loading={loading}
      error={error}
      data={data}
      onRun={() => void execute({ country, indicator })}
    />
  );
}
