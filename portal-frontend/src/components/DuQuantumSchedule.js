import React, { useMemo, useState } from "react";

const DAYS = {
  sat: { label: "Saturday", date: "October 24", first: "09:00", last: "21:00" },
  sun: { label: "Sunday", date: "October 25", first: "10:00", last: "17:00" },
};

const SCHEDULE = [
  {
    id: "sat-check-in",
    day: "sat",
    start: "09:00",
    end: "11:00",
    title: "Hacker Check-In",
    location: "Wilkinson 0th Floor Lobby",
    details:
      "Check in, receive event materials, and have your attendee pass ready to scan.",
    lane: 0,
  },
  {
    id: "sat-opening",
    day: "sat",
    start: "10:30",
    end: "11:30",
    title: "Opening Ceremony",
    location: "Wilkinson 021",
    details:
      "Opening keynote by Ken Brown, Director of the Duke Quantum Center.",
    lane: 1,
  },
  {
    id: "sat-lunch",
    day: "sat",
    start: "11:30",
    end: "12:30",
    title: "Hacker Lunch",
    location: "Wilkinson 0th Floor Lobby",
    details: "Lunch is available as the 24-hour build period begins.",
    lane: 0,
  },
  {
    id: "sat-hacking-starts",
    day: "sat",
    start: "11:30",
    end: "12:00",
    title: "Hacking Starts!",
    details: "The DuQuantum 2026 hacking period officially begins.",
    kind: "milestone",
    lane: 1,
  },
  {
    id: "sat-sponsor-fair",
    day: "sat",
    start: "13:00",
    end: "14:00",
    title: "Sponsor Fair",
    location: "Wilkinson 126",
    details:
      "Meet the organizations supporting DuQuantum and learn about their challenges.",
    lane: 0,
  },
  {
    id: "sat-intro-workshop",
    day: "sat",
    start: "14:00",
    end: "15:00",
    title: "Intro to Quantum Computing Workshop",
    location: "Wilkinson 130",
    details:
      "An introduction to quantum computing and Qiskit led by an IBM Quantum representative.",
    lane: 0,
  },
  {
    id: "sat-mlh-workshops",
    day: "sat",
    start: "15:00",
    end: "16:00",
    title: "MLH Workshops",
    location: "Wilkinson 130",
    details: "Workshops covering Google AI Studio and GitHub Copilot.",
    lane: 0,
  },
  {
    id: "sat-plenary",
    day: "sat",
    start: "16:00",
    end: "17:30",
    title: "DQC Faculty Plenary Lectures",
    location: "Wilkinson 130",
    details:
      "Joint lecture by Natalie Klco and Huanqian “Hazel” Loh. This session is open to non-hackers.",
    lane: 0,
  },
  {
    id: "sat-dinner",
    day: "sat",
    start: "18:30",
    end: "20:00",
    title: "Hacker Dinner",
    location: "Wilkinson 0th Floor Lobby",
    details: "Dinner for registered DuQuantum hackers.",
    lane: 0,
  },
  {
    id: "sat-night-workspace",
    day: "sat",
    start: "20:00",
    end: "21:00",
    title: "Night-time Work / Sleeping",
    location: "Wilkinson 021",
    details:
      "Overnight workspace is available. Bring your own sleeping supplies if you plan to stay.",
    lane: 0,
    openEnded: true,
  },
  {
    id: "sun-brunch",
    day: "sun",
    start: "10:00",
    end: "12:00",
    title: "Brunch",
    location: "Wilkinson 0th Floor Lobby",
    details: "Sunday brunch is available for hackers.",
    lane: 0,
  },
  {
    id: "sun-hacking-ends",
    day: "sun",
    start: "11:30",
    end: "12:00",
    title: "Hacking Ends!",
    details:
      "Project development ends. Submit your work and prepare for judging.",
    kind: "milestone",
    lane: 1,
  },
  {
    id: "sun-judging",
    day: "sun",
    start: "12:00",
    end: "13:30",
    title: "Judging",
    location: "Wilkinson 021 / 126 / 130 / 132 / 136",
    details:
      "Challenge judging takes place in assigned Wilkinson rooms. Google Quantum AI judging will be held virtually.",
    lane: 0,
  },
  {
    id: "sun-deliberations",
    day: "sun",
    start: "13:45",
    end: "15:15",
    title: "Deliberations",
    location: "Wilkinson 130",
    details:
      "Challenge representatives and DuQuantum judges determine challenge and overall awards.",
    lane: 0,
  },
  {
    id: "sun-closing",
    day: "sun",
    start: "15:30",
    end: "16:30",
    title: "Closing Ceremony / Awards",
    location: "Wilkinson 021",
    details: "Awards, closing keynote, and remarks by Robert Calderbank.",
    lane: 0,
  },
];

const minutes = (value) => {
  const [hours, mins] = value.split(":").map(Number);
  return hours * 60 + mins;
};

const formatTime = (value) => {
  const total = minutes(value);
  const hours = Math.floor(total / 60);
  const mins = total % 60;
  const suffix = hours >= 12 ? "PM" : "AM";
  const hour = ((hours + 11) % 12) + 1;
  return `${hour}:${String(mins).padStart(2, "0")} ${suffix}`;
};

const DuQuantumSchedule = () => {
  const [activeDay, setActiveDay] = useState("sat");
  const [selectedId, setSelectedId] = useState(null);
  const day = DAYS[activeDay];
  const firstMinute = minutes(day.first);
  const lastMinute = minutes(day.last);
  const rowCount = (lastMinute - firstMinute) / 15;

  const events = useMemo(
    () => SCHEDULE.filter((event) => event.day === activeDay),
    [activeDay],
  );
  const selectedEvent = events.find((event) => event.id === selectedId);
  const hours = [];
  for (let time = firstMinute; time < lastMinute; time += 60) hours.push(time);

  const selectDay = (dayId) => {
    setActiveDay(dayId);
    setSelectedId(null);
  };

  return (
    <section
      id="duquantum-schedule"
      className="dq-schedule-section"
      aria-labelledby="dq-schedule-heading"
    >
      <div className="dq-schedule-tabs">
        <div
          className="dq-schedule-label-tab"
          style={{
            backgroundImage: 'url("/duquantum-2026/schedule/tab-label.svg")',
          }}
        >
          <h2 id="dq-schedule-heading">Schedule</h2>
        </div>
        <div role="tablist" aria-label="Event schedule day">
          {Object.entries(DAYS).map(([id, value]) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={activeDay === id}
              aria-controls="dq-schedule-panel"
              className={`dq-schedule-day-tab ${activeDay === id ? "is-active" : ""}`}
              style={{
                backgroundImage: `url("/duquantum-2026/schedule/${activeDay === id ? "tab-filled" : "tab-outline"}.svg")`,
              }}
              onClick={() => selectDay(id)}
            >
              <span>{value.label}</span>
              <small>{value.date}</small>
            </button>
          ))}
        </div>
      </div>

      <div
        className="dq-schedule-frame"
        style={{
          backgroundImage: 'url("/duquantum-2026/schedule/frame.svg")',
        }}
      >
        <div className="dq-schedule-frame-heading">
          <div>
            <p className="dq-terminal-label">EVENT_TIMELINE // EASTERN TIME</p>
            <h3>
              {day.label}, {day.date}
            </h3>
          </div>
          <a
            href="https://duquantum.org/#schedule"
            target="_blank"
            rel="noopener noreferrer"
          >
            Open event site <span aria-hidden="true">↗</span>
          </a>
        </div>

        <div
          id="dq-schedule-panel"
          role="tabpanel"
          className="dq-schedule-scroll"
        >
          <div
            className="dq-schedule-grid"
            style={{ gridTemplateRows: `repeat(${rowCount}, 18px)` }}
          >
            {hours.map((time) => {
              const row = (time - firstMinute) / 15 + 1;
              return (
                <React.Fragment key={time}>
                  <div
                    className="dq-schedule-hour-line"
                    style={{ gridRow: `${row} / span 4`, gridColumn: "1 / -1" }}
                  />
                  <time
                    className="dq-schedule-hour"
                    style={{ gridRow: `${row} / span 4`, gridColumn: 1 }}
                  >
                    {formatTime(`${Math.floor(time / 60)}:00`)}
                  </time>
                </React.Fragment>
              );
            })}

            {events.map((event) => {
              const rowStart = (minutes(event.start) - firstMinute) / 15 + 1;
              const rowEnd = (minutes(event.end) - firstMinute) / 15 + 1;
              const selected = selectedId === event.id;
              return (
                <button
                  key={event.id}
                  type="button"
                  className={`dq-schedule-event ${event.kind === "milestone" ? "is-milestone" : ""} ${event.openEnded ? "is-open-ended" : ""} ${selected ? "is-selected" : ""}`}
                  style={{
                    gridRow: `${rowStart} / ${rowEnd}`,
                    gridColumn: `${event.lane + 2}`,
                  }}
                  aria-expanded={selected}
                  aria-controls="dq-schedule-details"
                  onClick={() => setSelectedId(selected ? null : event.id)}
                >
                  <strong>{event.title}</strong>
                  {event.location && <span>{event.location}</span>}
                  <small>{formatTime(event.start)}</small>
                </button>
              );
            })}
          </div>
        </div>

        {selectedEvent && (
          <aside
            id="dq-schedule-details"
            className="dq-schedule-details"
            aria-label={`${selectedEvent.title} details`}
          >
            <button
              type="button"
              aria-label="Close schedule details"
              onClick={() => setSelectedId(null)}
            >
              ×
            </button>
            <p className="dq-terminal-label">SCHEDULE_DETAIL // SELECTED</p>
            <h4>{selectedEvent.title}</h4>
            <p className="dq-schedule-when">
              {formatTime(selectedEvent.start)}–{formatTime(selectedEvent.end)}
              {selectedEvent.location ? ` · ${selectedEvent.location}` : ""}
            </p>
            <p>{selectedEvent.details}</p>
          </aside>
        )}

        <img
          className="dq-schedule-corner"
          src="/duquantum-2026/schedule/corner.svg"
          alt=""
          aria-hidden="true"
        />
        <div className="dq-schedule-lights" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>
    </section>
  );
};

export { DAYS, SCHEDULE };
export default DuQuantumSchedule;
