import React, { useMemo, useState } from "react";
import {
  formatTeamValue,
  teamForDirectoryEntry,
  teamLabel,
} from "../utils/teamUtils";

const memberIsLinked = (member) => {
  const status = String(member.matchStatus || "").toLowerCase();
  return Boolean(
    member.registrationId || ["matched", "linked"].includes(status),
  );
};

const linkageFor = (team) => {
  const linked = team.teammates.filter(memberIsLinked).length;
  const total = team.teammates.length;
  if (!linked)
    return { key: "unlinked", label: "No portal links", linked, total };
  if (linked < total)
    return { key: "partial", label: "Partially linked", linked, total };
  return { key: "complete", label: "Fully linked", linked, total };
};

const compareTeams = (left, right) => {
  const leftNumber = Number(left.number);
  const rightNumber = Number(right.number);
  if (Number.isFinite(leftNumber) && Number.isFinite(rightNumber)) {
    return leftNumber - rightNumber;
  }
  return teamLabel(left).localeCompare(teamLabel(right));
};

const uniqueValues = (teams, field) =>
  [...new Set(teams.map((team) => team[field]).filter(Boolean))].sort((a, b) =>
    String(a).localeCompare(String(b)),
  );

const DuQuantumTeamDirectory = ({
  teams = [],
  loading = false,
  error = "",
}) => {
  const [query, setQuery] = useState("");
  const [track, setTrack] = useState("all");
  const [challenge, setChallenge] = useState("all");
  const [source, setSource] = useState("all");
  const [linkage, setLinkage] = useState("all");
  const [expanded, setExpanded] = useState(null);

  const normalizedTeams = useMemo(
    () => teams.map((team) => ({ raw: team, ...teamForDirectoryEntry(team) })),
    [teams],
  );

  const stats = useMemo(() => {
    const members = normalizedTeams.reduce(
      (total, team) => total + team.teammates.length,
      0,
    );
    const linkedMembers = normalizedTeams.reduce(
      (total, team) => total + team.teammates.filter(memberIsLinked).length,
      0,
    );
    const unlinkedTeams = normalizedTeams.filter(
      (team) => linkageFor(team).key === "unlinked",
    ).length;
    return {
      teams: normalizedTeams.length,
      members,
      linkedMembers,
      unlinkedTeams,
    };
  }, [normalizedTeams]);

  const tracks = useMemo(
    () => uniqueValues(normalizedTeams, "track"),
    [normalizedTeams],
  );
  const challenges = useMemo(
    () => uniqueValues(normalizedTeams, "challenge"),
    [normalizedTeams],
  );
  const sources = useMemo(
    () => uniqueValues(normalizedTeams, "source"),
    [normalizedTeams],
  );

  const filteredTeams = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return normalizedTeams
      .filter((team) => {
        if (track !== "all" && team.track !== track) return false;
        if (challenge !== "all" && team.challenge !== challenge) return false;
        if (source !== "all" && team.source !== source) return false;
        if (linkage !== "all" && linkageFor(team).key !== linkage) return false;
        if (!normalizedQuery) return true;
        return JSON.stringify(team.raw).toLowerCase().includes(normalizedQuery);
      })
      .sort(compareTeams);
  }, [challenge, linkage, normalizedTeams, query, source, track]);

  const clearFilters = () => {
    setQuery("");
    setTrack("all");
    setChallenge("all");
    setSource("all");
    setLinkage("all");
  };

  return (
    <section
      className="dq-team-directory-panel"
      aria-labelledby="team-directory-heading"
    >
      <div className="dq-team-directory-heading">
        <div>
          <p className="dq-terminal-label">
            FINAL_TEAMS // {filteredTeams.length} OF {normalizedTeams.length}
          </p>
          <h2 id="team-directory-heading">Final team directory</h2>
          <p>
            Authoritative assignments from the final teams workbook, including
            teams whose members are not linked to portal registrations.
          </p>
        </div>
        <div className="dq-team-directory-summary" aria-label="Team totals">
          <span>
            <strong>{stats.teams}</strong> teams
          </span>
          <span>
            <strong>{stats.members}</strong> members
          </span>
          <span>
            <strong>{stats.linkedMembers}</strong> portal-linked
          </span>
          <span>
            <strong>{stats.unlinkedTeams}</strong>{" "}
            {stats.unlinkedTeams === 1 ? "team" : "teams"} with no links
          </span>
        </div>
      </div>

      <div className="dq-team-directory-controls">
        <label>
          <span>Search teams</span>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Team, member, email, challenge…"
          />
        </label>
        <label>
          <span>Final track</span>
          <select
            value={track}
            onChange={(event) => setTrack(event.target.value)}
          >
            <option value="all">All tracks</option>
            {tracks.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Assigned challenge</span>
          <select
            value={challenge}
            onChange={(event) => setChallenge(event.target.value)}
          >
            <option value="all">All challenges</option>
            {challenges.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Portal linkage</span>
          <select
            value={linkage}
            onChange={(event) => setLinkage(event.target.value)}
          >
            <option value="all">All linkage states</option>
            <option value="complete">Fully linked</option>
            <option value="partial">Partially linked</option>
            <option value="unlinked">No portal links</option>
          </select>
        </label>
        <label>
          <span>Formation source</span>
          <select
            value={source}
            onChange={(event) => setSource(event.target.value)}
          >
            <option value="all">All sources</option>
            {sources.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        {(query ||
          track !== "all" ||
          challenge !== "all" ||
          linkage !== "all" ||
          source !== "all") && (
          <button type="button" onClick={clearFilters}>
            Clear team filters
          </button>
        )}
      </div>

      {error && (
        <div className="dq-alert dq-alert-error" role="alert">
          {error}
        </div>
      )}

      {loading ? (
        <div className="dq-admin-loading" role="status">
          Loading final team directory…
        </div>
      ) : filteredTeams.length ? (
        <div className="dq-table-scroll" tabIndex="0">
          <table className="dq-team-directory-table">
            <caption className="dq-visually-hidden">
              DuQuantum 2026 final team directory
            </caption>
            <thead>
              <tr>
                <th scope="col">Final team</th>
                <th scope="col">Track</th>
                <th scope="col">Assigned challenge / sponsor</th>
                <th scope="col">Members</th>
                <th scope="col">Portal linkage</th>
                <th scope="col">
                  <span className="dq-visually-hidden">Details</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredTeams.map((team, index) => {
                const key = team.id || `${team.name}-${team.number}-${index}`;
                const isOpen = expanded === key;
                const teamLinkage = linkageFor(team);
                return (
                  <React.Fragment key={key}>
                    <tr className={isOpen ? "is-expanded" : ""}>
                      <td>
                        <strong>{teamLabel(team)}</strong>
                        <span>{formatTeamValue(team.source)}</span>
                      </td>
                      <td>{formatTeamValue(team.track)}</td>
                      <td>
                        <strong>{formatTeamValue(team.challenge)}</strong>
                        <span>{formatTeamValue(team.sponsor)}</span>
                      </td>
                      <td>{team.teammates.length}</td>
                      <td>
                        <span className={`dq-team-linkage ${teamLinkage.key}`}>
                          {teamLinkage.label}
                        </span>
                        <small>
                          {teamLinkage.linked} / {teamLinkage.total} members
                        </small>
                      </td>
                      <td>
                        <button
                          className="dq-detail-button"
                          type="button"
                          aria-expanded={isOpen}
                          aria-controls={`team-directory-details-${key}`}
                          onClick={() => setExpanded(isOpen ? null : key)}
                        >
                          {isOpen ? "Close" : "View roster"}
                          <span aria-hidden="true">{isOpen ? "−" : "+"}</span>
                        </button>
                      </td>
                    </tr>
                    {isOpen && (
                      <tr className="dq-detail-row">
                        <td colSpan="6" id={`team-directory-details-${key}`}>
                          <div className="dq-team-directory-details">
                            <section>
                              <h3>Final assignment</h3>
                              <dl>
                                <div>
                                  <dt>Team number</dt>
                                  <dd>{formatTeamValue(team.number)}</dd>
                                </div>
                                <div>
                                  <dt>Team name</dt>
                                  <dd>{formatTeamValue(team.name)}</dd>
                                </div>
                                <div>
                                  <dt>Track</dt>
                                  <dd>{formatTeamValue(team.track)}</dd>
                                </div>
                                <div>
                                  <dt>Assigned challenge</dt>
                                  <dd>{formatTeamValue(team.challenge)}</dd>
                                </div>
                                <div>
                                  <dt>Sponsor</dt>
                                  <dd>{formatTeamValue(team.sponsor)}</dd>
                                </div>
                                <div>
                                  <dt>Sponsor contact</dt>
                                  <dd>
                                    {team.sponsorContactEmail ? (
                                      <>
                                        {team.sponsorContactName && (
                                          <span>{team.sponsorContactName}</span>
                                        )}
                                        <a
                                          href={`mailto:${team.sponsorContactEmail}`}
                                        >
                                          {team.sponsorContactEmail}
                                        </a>
                                      </>
                                    ) : (
                                      formatTeamValue(team.sponsorContactName)
                                    )}
                                  </dd>
                                </div>
                              </dl>
                              <details className="dq-team-preferences">
                                <summary>Formation preferences</summary>
                                <dl>
                                  <div>
                                    <dt>Track preference</dt>
                                    <dd>
                                      {formatTeamValue(team.trackPreference)}
                                    </dd>
                                  </div>
                                  <div>
                                    <dt>Challenge preferences</dt>
                                    <dd>
                                      {formatTeamValue(
                                        team.challengePreferences,
                                      )}
                                    </dd>
                                  </div>
                                  <div>
                                    <dt>Requested additional teammates</dt>
                                    <dd>
                                      {formatTeamValue(
                                        team.requestedAdditionalTeammates,
                                      )}
                                    </dd>
                                  </div>
                                  <div>
                                    <dt>Additional teammate request details</dt>
                                    <dd>
                                      {formatTeamValue(
                                        team.additionalTeammatesDetail,
                                      )}
                                    </dd>
                                  </div>
                                </dl>
                              </details>
                            </section>
                            <section className="dq-team-directory-roster">
                              <h3>Final roster</h3>
                              {team.teammates.length ? (
                                <ol>
                                  {team.teammates.map((member, memberIndex) => (
                                    <li
                                      key={`${member.name}-${member.memberPosition || memberIndex}`}
                                    >
                                      <div>
                                        <strong>{member.name}</strong>
                                        {member.email && (
                                          <a href={`mailto:${member.email}`}>
                                            {member.email}
                                          </a>
                                        )}
                                        {member.discordUsername && (
                                          <span>
                                            Discord: {member.discordUsername}
                                          </span>
                                        )}
                                      </div>
                                      <div>
                                        <span
                                          className={`dq-team-linkage ${memberIsLinked(member) ? "complete" : "unlinked"}`}
                                        >
                                          {memberIsLinked(member)
                                            ? "Portal linked"
                                            : "Not linked"}
                                        </span>
                                        {member.matchMethod && (
                                          <small>
                                            {member.matchMethod}
                                            {member.matchDetail
                                              ? ` - ${member.matchDetail}`
                                              : ""}
                                          </small>
                                        )}
                                      </div>
                                    </li>
                                  ))}
                                </ol>
                              ) : (
                                <p>N/A</p>
                              )}
                            </section>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="dq-empty-results">
          <h3>No final teams match this view.</h3>
          <p>Clear the team filters to return to the complete directory.</p>
        </div>
      )}
    </section>
  );
};

export default DuQuantumTeamDirectory;
