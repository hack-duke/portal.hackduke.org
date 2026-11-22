import React from "react";
import { Link } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { PortalLayout } from "../components/portal/PortalLayout";
import { EVENT_INFO } from "../portal/eventInfo";
import {
  FormIcon,
  CalendarIcon,
  MailIcon,
  CheckCircleIcon,
  FlagIcon,
} from "../components/portal/icons";
import "./InfoPage.css";

const TIMELINE_ICONS = {
  form: FormIcon,
  calendar: CalendarIcon,
  mail: MailIcon,
  check: CheckCircleIcon,
  flag: FlagIcon,
};

const InfoPage = () => {
  const { user } = useAuth0();
  const firstName = user?.given_name;

  return (
    <PortalLayout>
      <div className="info-page">
        <header className="info-header">
          <h1 className="info-title">
            Welcome{firstName ? `, ${firstName}` : ""}!
          </h1>
          <p className="info-subtitle">
            This is the HackDuke Portal, where you apply to and get ready for{" "}
            {EVENT_INFO.name}.
          </p>
        </header>

        <section className="info-card" aria-labelledby="info-event-heading">
          <div className="info-card-header">
            <div>
              <h2 id="info-event-heading" className="info-card-title">
                {EVENT_INFO.shortName}: {EVENT_INFO.dates}
              </h2>
              <p className="info-card-meta">{EVENT_INFO.location}</p>
            </div>
            <Link to="/application" className="info-cta">
              Go to application
            </Link>
          </div>

          <p className="info-card-note">{EVENT_INFO.timelineNote}</p>

          <ol className="timeline">
            {EVENT_INFO.timeline.map((item) => {
              const Icon = TIMELINE_ICONS[item.icon] || CalendarIcon;
              return (
                <li className="timeline-item" key={item.title}>
                  <span className="timeline-marker" aria-hidden="true">
                    <Icon />
                  </span>
                  <div className="timeline-body">
                    <span className="timeline-date">{item.date}</span>
                    <h3 className="timeline-title">{item.title}</h3>
                    <p className="timeline-description">{item.description}</p>
                  </div>
                </li>
              );
            })}
          </ol>
        </section>

        <p className="info-footer">
          Questions? Reach out to{" "}
          <a href={`mailto:${EVENT_INFO.contactEmail}`}>
            {EVENT_INFO.contactEmail}
          </a>
          .
        </p>
      </div>
    </PortalLayout>
  );
};

export default InfoPage;
