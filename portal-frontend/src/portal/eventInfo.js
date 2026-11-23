// Everything shown on the portal's Information page lives here, so each year
// only this file needs updating.
//
// Dates are plain text and shown exactly as written; "TBD" is fine.
export const EVENT_INFO = {
  shortName: "HackDuke 2027",
  name: "HackDuke: Code for Good 2027",
  dates: "February 6–7, 2027",
  location: "Duke University, Durham, NC",
  eventSiteUrl: "https://2027.hackduke.org/",
  contactEmail: "hackers@hackduke.org",
  // Exact deadline times (Eastern), used by the countdown on the login page.
  priorityDeadline: "2027-01-04T23:59:59-05:00",
  finalDeadline: "2027-01-15T23:59:59-05:00",
  timelineNote:
    "Here's what to expect leading up to the event. Dates may change.",
  // icon: one of "form" | "calendar" | "mail" | "check" | "flag"
  timeline: [
    {
      date: "November 23, 2026",
      title: "Applications Open",
      description:
        "HackDuke applications are open! Head to the Application tab to apply.",
      icon: "form",
    },
    {
      date: "December 14, 2026",
      title: "Priority Deadline",
      description:
        "Apply by 11:59 PM ET for priority consideration. We encourage applying early!",
      icon: "calendar",
    },
    {
      date: "January 4, 2027",
      title: "Final Deadline",
      description: "Last chance! Applications close at 11:59 PM ET.",
      icon: "calendar",
    },
    {
      date: "TBD",
      title: "Decisions Released",
      description:
        "Decisions will be emailed to you, and your status will update on the Application tab.",
      icon: "mail",
    },
    {
      date: "TBD",
      title: "Confirm Your Spot",
      description:
        "If you're accepted, we'll email you instructions to confirm your attendance and secure your spot.",
      icon: "check",
    },
    {
      date: "February 6-7, 2027",
      title: "Event Day",
      description:
        "HackDuke begins! Check in with the QR code on your Application tab.",
      icon: "flag",
    },
  ],
};
