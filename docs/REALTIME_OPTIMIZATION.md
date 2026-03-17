# ⏱️ Real-time Optimization Plan: AI LoL Predictor

This document outlines the strategy to transition from a high-frequency polling model to a reactive real-time architecture using WebSockets and optimized data fetching.

---

## 1. Current State Diagnosis
- **Frontend:** Currently polls `api/live/match/{id}` every **500ms** via `setInterval`.
  - **Issue:** Overloads the client/server; data from Riot only changes every ~10-20s.
- **Backend:** Uses a **1-second cache** for telemetry data.
  - **Issue:** No request collapsing; multiple simultaneous users can trigger multiple outgoing Riot API calls.
- **Latency:** Artificially delayed by **60 seconds** in `get_iso_date_multiple_of_10` to ensure frame stability.

---

## 2. Target Architecture: WebSocket Sync
The goal is to implement a **Publisher-Subscriber** model where the server manages the Riot API connection and pushes updates to all connected clients only when data changes.

### A. Backend Implementation (FastAPI)
1.  **WebSocket Manager:**
    - Create a `/ws/match/{match_id}` endpoint.
    - Maintain a registry of active match connections (e.g., `active_matches: Dict[str, Set[WebSocket]]`).
2.  **Request Collapsing & Background Worker:**
    - For each *unique* active match, run exactly **one** background polling task.
    - Task fetches data from Riot every 10 seconds.
    - If data is different from the previous frame, broadcast the JSON to all WebSockets in the set.
3.  **Data Latency Tuning:**
    - Reduce the 60s offset to **35-40s**. This gains ~20s of closeness to "real" real-time while maintaining stability for the Riot API.

### B. Frontend Implementation (Svelte 5)
1.  **WebSocket Client:**
    - Replace `setInterval` in `+page.svelte` with a WebSocket connection.
    - Use `$state` runes to update the UI reactively when a message arrives.
2.  **Smooth Animations (GSAP):**
    - Instead of "jumping" values (HP, Gold), use GSAP to **interpolate** changes over 5-10 seconds.
    - This creates the *perception* of continuous real-time motion even if data updates are periodic.

---

## 3. Step-by-Step Roadmap

### Phase 1: Infrastructure (Backend)
- [ ] Implement `ConnectionManager` class in a new module (e.g., `interface/socket_manager.py`).
- [ ] Add the WebSocket route to `api.py`.
- [ ] Create a logic to check if a background polling task for a specific `match_id` is already running.

### Phase 2: Reactive UI (Frontend)
- [ ] Create a `liveSocket.ts` utility to manage reconnect logic.
- [ ] Refactor `+page.svelte` to listen for `onmessage` instead of polling.
- [ ] Add GSAP `to()` animations for the Gold bar and HP bars to smooth out the transitions.

### Phase 3: Fine-tuning
- [ ] Test the 40s latency offset for different regions (CBLOL, LCK, etc.).
- [ ] Add a "Reconnecting..." indicator in the UI.

---

## 4. Expected Benefits
- **-90% Server Load:** Zero HTTP headers overhead for polling; no redundant Riot API calls.
- **Improved UX:** Smoother visual transitions and 20s less delay compared to the current implementation.
- **Scalability:** The system can support hundreds of users watching the same game with minimal impact on API rate limits.
