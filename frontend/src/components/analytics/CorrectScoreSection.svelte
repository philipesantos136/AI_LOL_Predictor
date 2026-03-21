<script lang="ts">
  import type { CorrectScoreSection } from '$lib/types/analytics';
  import ExplainBox from '../analytics/ExplainBox.svelte';
  import DataCommentBox from '../analytics/DataCommentBox.svelte';
  import BetEntry from '../analytics/BetEntry.svelte';

  interface Props {
    data: CorrectScoreSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();

  function sortScores(scores: Record<string, number>) {
    return Object.entries(scores).sort((a, b) => b[1] - a[1]);
  }
</script>

<div class="section-card">
  <h3 class="section-title">🏆 Correct Score (Placar Exato)</h3>

  <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
    <div class="team-panel">
      <div class="team-header text-blue-400">
        <span class="font-bold">{team1}</span>
        <span class="text-xs text-slate-500">({data.t1_total_series} Séries Históricas)</span>
      </div>
      <div class="scores-grid">
        {#each sortScores(data.t1_scores) as [score, count]}
          <div class="score-card text-center bg-[#0f172a] p-3 rounded-lg border border-blue-900/30">
            <div class="font-black text-xl text-blue-300">{score}</div>
            <div class="text-xs text-slate-400 font-semibold">{count} vez(es)</div>
            <div class="text-[10px] text-blue-500/70 mt-1">{((count / data.t1_total_series) * 100).toFixed(0)}%</div>
          </div>
        {/each}
        {#if Object.keys(data.t1_scores).length === 0}
          <div class="text-slate-500 text-sm italic py-4">Sem dados para placares fixos.</div>
        {/if}
      </div>
    </div>

    <div class="team-panel">
      <div class="team-header text-red-400">
        <span class="font-bold">{team2}</span>
        <span class="text-xs text-slate-500">({data.t2_total_series} Séries Históricas)</span>
      </div>
      <div class="scores-grid">
        {#each sortScores(data.t2_scores) as [score, count]}
          <div class="score-card text-center bg-[#0f172a] p-3 rounded-lg border border-red-900/30">
            <div class="font-black text-xl text-red-300">{score}</div>
            <div class="text-xs text-slate-400 font-semibold">{count} vez(es)</div>
            <div class="text-[10px] text-red-500/70 mt-1">{((count / data.t2_total_series) * 100).toFixed(0)}%</div>
          </div>
        {/each}
        {#if Object.keys(data.t2_scores).length === 0}
          <div class="text-slate-500 text-sm italic py-4">Sem dados para placares fixos.</div>
        {/if}
      </div>
    </div>
  </div>

  {#if data.bet_entries?.length > 0}
    <div class="bet-entries-grid">
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
    border-left: 3px solid #8b5cf6;
    width: 100%;
  }

  .section-title {
    color: #c4b5fd;
    font-size: 1rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
  }

  .team-panel {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .team-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #334155;
    padding-bottom: 0.5rem;
  }

  .scores-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 0.5rem;
  }

  .bet-entries-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
  }
</style>
