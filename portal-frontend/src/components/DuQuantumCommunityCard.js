import React from "react";

const DISCORD_INVITE_URL = "https://discord.gg/mqQNBDXkd";

const DiscordMark = () => (
  <svg
    className="dq-discord-mark"
    viewBox="0 0 127.14 96.36"
    role="img"
    aria-label="Discord"
  >
    <path
      fill="currentColor"
      d="M107.7 8.07A105.15 105.15 0 0 0 81.47 0a72.06 72.06 0 0 0-3.36 6.83 97.68 97.68 0 0 0-29.11 0A72.37 72.37 0 0 0 45.64 0 105.89 105.89 0 0 0 19.39 8.09C2.79 32.65-1.71 56.6.54 80.21a105.73 105.73 0 0 0 32.17 16.15 77.7 77.7 0 0 0 6.89-8.89 68.42 68.42 0 0 1-10.81-5.18c.91-.66 1.8-1.34 2.66-2a75.57 75.57 0 0 0 64.32 0c.87.71 1.76 1.39 2.67 2a68.68 68.68 0 0 1-10.84 5.19 77 77 0 0 0 6.89 8.89 105.25 105.25 0 0 0 32.45-16.14C129.58 52.84 122.43 29.11 107.7 8.07ZM42.45 65.69C36.18 65.69 31 59.93 31 52.86S36 40 42.45 40s11.57 5.81 11.46 12.86S48.84 65.69 42.45 65.69Zm42.24 0c-6.28 0-11.44-5.76-11.44-12.83S78.22 40 84.69 40s11.57 5.81 11.46 12.86S91.08 65.69 84.69 65.69Z"
    />
  </svg>
);

const DuQuantumCommunityCard = () => (
  <article className="dq-panel dq-community-card">
    <div className="dq-community-heading">
      <DiscordMark />
      <div>
        <p className="dq-terminal-label">COMMUNITY_CHANNEL // LIVE</p>
        <h2>Join the DuQuantum Discord</h2>
      </div>
    </div>
    <p>
      Meet other hackers, find teammates, and follow organizer announcements
      before and during the event.
    </p>
    <a
      className="dq-discord-link"
      href={DISCORD_INVITE_URL}
      target="_blank"
      rel="noopener noreferrer"
    >
      <DiscordMark />
      Join the Discord
      <span aria-hidden="true">↗</span>
    </a>
  </article>
);

export { DISCORD_INVITE_URL };
export default DuQuantumCommunityCard;
