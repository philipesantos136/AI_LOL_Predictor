<script lang="ts">
  import type { TowersPerTeamSection } from '$lib/types/analytics';
  import ExplainBox from '../analytics/ExplainBox.svelte';
  import DataCommentBox from '../analytics/DataCommentBox.svelte';
  import BetEntry from '../analytics/BetEntry.svelte';

  interface Props {
    data: TowersPerTeamSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();
</script>

<div class="section-card">
  <h3 class="section-title">🏰 Towers Over/Under (Individual)</h3>

  <div class="split-layout">
    <div class="team-panel">
      <div class="team-header text-blue-400">
        <span class="font-bold">{team1}</span>
        <span class="text-xs text-slate-500">Média: {data.t1_stats?.avg.toFixed(2) ?? 'N/A'}</span>
      </div>
      {#if data.t1_bet_entries?.length > 0}
        <div class="bet-entries-grid mt-4">
          {#each data.t1_bet_entries as entry}
            <BetEntry entry={entry} />
          {/each}
        </div>
      {:else}
        <p class="text-slate-500 text-sm mt-4">Sem entradas calculadas para torres.</p>
      {/if}
    </div>

    <div class="team-panel">
      <div class="team-header text-red-400">
        <span class="font-bold">{team2}</span>
        <span class="text-xs text-slate-500">Média: {data.t2_stats?.avg.toFixed(2) ?? 'N/A'}</span>
      </div>
      {#if data.t2_bet_entries?.length > 0}
        <div class="bet-entries-grid mt-4">
          {#each data.t2_bet_entries as entry}
            <BetEntry entry={entry} />
          {/each}
        </div>
      {:else}
        <p class="text-slate-500 text-sm mt-4">Sem entradas calculadas para torres.</p>
      {/if}
    </div>
  </div>

  <ExplainBox text={data.explain_text} />
  <DataCommentBox comments={data.comments} />
</div>

<style>
  .section-card {
    background: #1e293b;
    border-radius: 0.75rem;
    padding: 1.25rem;
    border: 1px solid #334155;
    border-left: 3px solid #cbd5e1;
    width: 100%;
  }

  .section-title {
    color: #e2e8f0;
    font-size: 1rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
  }

  .split-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
  }

  @media (max-width: 768px) {
    .split-layout {
      grid-template-columns: 1fr;
    }
  }

  .team-panel {
    display: flex;
    flex-direction: column;
    background: #0f172a;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #1e293b;
  }

  .team-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #334155;
    padding-bottom: 0.5rem;
  }

  .bet-entries-grid {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
</style>
