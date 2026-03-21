<script lang="ts">
  import type { PlayerKillStatsSection } from '$lib/types/analytics';
  import ExplainBox from '../analytics/ExplainBox.svelte';
  import DataCommentBox from '../analytics/DataCommentBox.svelte';
  import BetEntry from '../analytics/BetEntry.svelte';

  interface Props {
    data: PlayerKillStatsSection;
    team1: string;
    team2: string;
  }

  let { data, team1, team2 }: Props = $props();

  function sortPlayers(players: any[]) {
    return players ? [...players].sort((a, b) => b.avg_kills - a.avg_kills) : [];
  }
</script>

<div class="section-card">
  <h3 class="section-title">👤 Over/Under Kills por Jogador</h3>

  <div class="split-layout">
    <!-- Blue Side Players -->
    <div class="team-panel">
      <div class="team-header text-blue-400">
        <span class="font-black text-sm uppercase tracking-widest">{team1} Players</span>
      </div>
      <div class="flex flex-col gap-4 mt-4">
        {#each sortPlayers(data.t1_players) as player}
          <div class="player-card">
            <div class="player-info">
              <span class="player-name">{player.playername}</span>
              <span class="player-role">{player.position}</span>
            </div>
            <div class="player-stats">
              <span>{player.avg_kills.toFixed(1)} K</span> / 
              <span>{player.avg_deaths.toFixed(1)} D</span> / 
              <span>{player.avg_assists.toFixed(1)} A</span>
            </div>
            <!-- Bet Entries subset -->
            <div class="bet-list">
              {#each player.bet_entries.slice(0, 2) as entry}
                 <BetEntry entry={entry} />
              {/each}
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Red Side Players -->
    <div class="team-panel">
      <div class="team-header text-red-400">
        <span class="font-black text-sm uppercase tracking-widest">{team2} Players</span>
      </div>
      <div class="flex flex-col gap-4 mt-4">
        {#each sortPlayers(data.t2_players) as player}
          <div class="player-card">
            <div class="player-info text-right justify-end flex-row-reverse">
              <span class="player-name">{player.playername}</span>
              <span class="player-role">{player.position}</span>
            </div>
            <div class="player-stats text-right justify-end">
              <span>{player.avg_kills.toFixed(1)} K</span> / 
              <span>{player.avg_deaths.toFixed(1)} D</span> / 
              <span>{player.avg_assists.toFixed(1)} A</span>
            </div>
            <!-- Bet Entries subset -->
            <div class="bet-list">
              {#each player.bet_entries.slice(0, 2) as entry}
                 <BetEntry entry={entry} />
              {/each}
            </div>
          </div>
        {/each}
      </div>
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
    border-left: 3px solid #f43f5e;
    width: 100%;
  }

  .section-title {
    color: #fda4af;
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
  }

  .team-header {
    border-bottom: 1px solid #334155;
    padding-bottom: 0.5rem;
  }

  .player-card {
    background: rgba(15, 23, 42, 0.4);
    border: 1px solid #334155;
    border-radius: 0.5rem;
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .player-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .player-name {
    font-size: 0.875rem;
    font-weight: 800;
    color: #e2e8f0;
  }

  .player-role {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #94a3b8;
    background: #1e293b;
    padding: 0.1rem 0.3rem;
    border-radius: 0.25rem;
  }

  .player-stats {
    display: flex;
    gap: 0.35rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: #94a3b8;
  }

  .bet-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-top: 0.25rem;
  }
</style>
