<script lang="ts">
  import type { MapHandicapSection } from '$lib/types/analytics';
  import ExplainBox from '../analytics/ExplainBox.svelte';
  import DataCommentBox from '../analytics/DataCommentBox.svelte';
  import BetEntry from '../analytics/BetEntry.svelte';

  interface Props {
    data: MapHandicapSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();

  function avgDiff(diffs: number[]) {
    if (!diffs || diffs.length === 0) return 0;
    return (diffs.reduce((a, b) => a + b, 0) / diffs.length).toFixed(2);
  }
</script>

<div class="section-card">
  <h3 class="section-title">🗺️ Map Handicap (Séries)</h3>

  <div class="metrics">
    <div class="metric-block">
      <div class="metric-header text-blue-400">
        <span class="font-bold">{team1}</span>
        <span class="text-xs text-slate-500">Média: {avgDiff(data.t1_map_diffs)} Mapas/Série</span>
      </div>
      <div class="text-sm font-semibold text-slate-300 mt-2">Diferença de Mapas em Vitórias (+)/Derrotas (-) nas Séries:</div>
      <div class="flex flex-wrap gap-2 mt-2">
         {#each data.t1_map_diffs as d}
           <span class="px-2 py-1 rounded bg-[#0f172a] text-xs font-black border border-slate-700/50 {d > 0 ? 'text-green-400' : 'text-red-400'}">
             {d > 0 ? '+' : ''}{d}
           </span>
         {/each}
      </div>
    </div>

    <div class="metric-block">
      <div class="metric-header text-red-400">
        <span class="font-bold">{team2}</span>
        <span class="text-xs text-slate-500">Média: {avgDiff(data.t2_map_diffs)} Mapas/Série</span>
      </div>
      <div class="text-sm font-semibold text-slate-300 mt-2">Diferença de Mapas em Vitórias (+)/Derrotas (-) nas Séries:</div>
      <div class="flex flex-wrap gap-2 mt-2">
         {#each data.t2_map_diffs as d}
           <span class="px-2 py-1 rounded bg-[#0f172a] text-xs font-black border border-slate-700/50 {d > 0 ? 'text-green-400' : 'text-red-400'}">
             {d > 0 ? '+' : ''}{d}
           </span>
         {/each}
      </div>
    </div>
  </div>

  {#if data.bet_entries?.length > 0}
    <div class="bet-entries-grid mt-6">
      {#each data.bet_entries as entry}
        <BetEntry entry={entry} />
      {/each}
    </div>
  {/if}

  <ExplainBox text={data.explain_text} />
  <DataCommentBox comments={data.comments} />
</div>

<style>
  .section-card {
    background: #1e293b;
    border-radius: 0.75rem;
    padding: 1.25rem;
    border: 1px solid #334155;
    border-left: 3px solid #14b8a6;
    width: 100%;
  }

  .section-title {
    color: #5eead4;
    font-size: 1rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
  }

  .metrics {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .metric-block {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .metric-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #334155;
    padding-bottom: 0.5rem;
  }

  .bet-entries-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
  }
</style>
