// import React from "react";

// // AboutMe - single-file React component (Tailwind CSS)
// // Drop this file into a React + Tailwind project.
// // - Requires: tailwindcss configured in your app

// export default function AboutMe() {
//   const skills = [
//     "React",
//     "TypeScript",
//     "Tailwind CSS",
//     "Node.js",
//     "GraphQL",
//     "Design Systems",
//   ];

//   const socials = [
//     { name: "GitHub", href: "https://github.com/yourhandle", svg: githubIcon },
//     {
//       name: "LinkedIn",
//       href: "https://www.linkedin.com/in/yourhandle",
//       svg: linkedinIcon,
//     },
//     { name: "Email", href: "mailto:you@example.com", svg: mailIcon },
//   ];

//   return (
//     <main className="min-h-screen bg-gray-50 text-gray-800 flex items-center justify-center p-6">
//       <div className="w-full max-w-4xl bg-white/80 backdrop-blur-md shadow-2xl rounded-2xl overflow-hidden border border-gray-100">
//         <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-8">
//           {/* Left column - photo & contact */}
//           <aside className="flex flex-col items-center md:items-start gap-6 md:gap-8 transition-opacity duration-700 ease-in-out opacity-100">
//             <div className="w-36 h-36 md:w-44 md:h-44 rounded-xl overflow-hidden shadow-lg ring-1 ring-gray-200">
//               {/* Replace the src with your photo. Uses an accessible alt text. */}
//               <img
//                 src="https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=800&auto=format&fit=crop&ixlib=rb-4.0.3&s=placeholder"
//                 alt="Your name — profile"
//                 className="w-full h-full object-cover"
//               />
//             </div>

//             <div className="text-center md:text-left">
//               <h1 className="text-2xl md:text-3xl font-extrabold">Your Name</h1>
//               <p className="mt-1 text-sm text-gray-500">
//                 Product Engineer · Designer · Open-source
//               </p>
//             </div>

//             <div className="flex gap-3">
//               {socials.map((s) => (
//                 <a
//                   key={s.name}
//                   href={s.href}
//                   target="_blank"
//                   rel="noreferrer"
//                   aria-label={s.name}
//                   className="p-2 rounded-lg hover:bg-gray-100 transition"
//                 >
//                   <span className="w-5 h-5 inline-block" aria-hidden>
//                     {s.svg}
//                   </span>
//                 </a>
//               ))}
//             </div>

//             <a
//               href="#contact"
//               className="mt-auto inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-500 text-white font-medium shadow-md hover:opacity-95"
//             >
//               Contact me
//             </a>
//           </aside>

//           {/* Right column - bio, skills, experience */}
//           <section className="md:col-span-2 transition-opacity duration-700 ease-in-out opacity-100">
//             <div className="flex flex-col gap-6">
//               <div>
//                 <h2 className="text-lg font-semibold">About me</h2>
//                 <p className="mt-3 text-gray-600 leading-relaxed">
//                   Hey — I’m <strong>Your Name</strong>. I build delightful
//                   products and design systems that help teams move faster. I
//                   focus on high-quality front-end architecture, great UX, and
//                   clean accessibility-first implementations.
//                 </p>

//                 <p className="mt-3 text-gray-600 leading-relaxed">
//                   I love collaborating across disciplines, shipping meaningful
//                   features, and mentoring engineers. Outside work I’m into
//                   photography, woodworking, and hiking.
//                 </p>
//               </div>

//               <div>
//                 <h3 className="text-sm font-medium text-gray-700">Skills</h3>
//                 <div className="mt-3 flex flex-wrap gap-2">
//                   {skills.map((skill) => (
//                     <span
//                       key={skill}
//                       className="text-xs px-3 py-1 rounded-full border border-gray-200 bg-gray-50 font-medium"
//                     >
//                       {skill}
//                     </span>
//                   ))}
//                 </div>
//               </div>

//               <div>
//                 <h3 className="text-sm font-medium text-gray-700">
//                   Selected experience
//                 </h3>
//                 <ul className="mt-4 space-y-3">
//                   <li className="p-4 rounded-lg border border-gray-100 bg-white shadow-sm">
//                     <div className="flex items-start justify-between">
//                       <div>
//                         <p className="text-sm font-semibold">
//                           Senior Frontend Engineer — Company A
//                         </p>
//                         <p className="text-xs text-gray-500">2022 — Present</p>
//                       </div>
//                       <p className="text-xs text-gray-400">Remote</p>
//                     </div>
//                     <p className="mt-2 text-sm text-gray-600">
//                       Led the front-end rewrite of the core product resulting in
//                       faster load times and more consistent UI components.
//                     </p>
//                   </li>

//                   <li className="p-4 rounded-lg border border-gray-100 bg-white shadow-sm">
//                     <div className="flex items-start justify-between">
//                       <div>
//                         <p className="text-sm font-semibold">
//                           Frontend Engineer — Startup B
//                         </p>
//                         <p className="text-xs text-gray-500">2019 — 2022</p>
//                       </div>
//                       <p className="text-xs text-gray-400">Hybrid</p>
//                     </div>
//                     <p className="mt-2 text-sm text-gray-600">
//                       Built the design system and contributed to the product's
//                       accessibility and performance improvements.
//                     </p>
//                   </li>
//                 </ul>
//               </div>

//               <div id="contact" className="pt-2">
//                 <h3 className="text-sm font-medium text-gray-700">
//                   Get in touch
//                 </h3>
//                 <p className="mt-2 text-sm text-gray-600">
//                   I’m open to freelance and full-time opportunities. Email me at{" "}
//                   <a
//                     className="text-indigo-600 underline"
//                     href="mailto:you@example.com"
//                   >
//                     you@example.com
//                   </a>
//                   .
//                 </p>
//               </div>
//             </div>
//           </section>
//         </div>

//         <footer className="border-t border-gray-100 text-xs text-gray-500 p-4 text-center">
//           Made with ❤️ — customize this page to tell your story.
//         </footer>
//       </div>
//     </main>
//   );
// }

// // ---------- Icons (inline SVGs) ----------
// function githubIcon() {
//   return (
//     <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
//       <path d="M12 .5a12 12 0 00-3.79 23.39c.6.11.82-.26.82-.58v-2.02c-3.34.73-4.04-1.61-4.04-1.61-.55-1.41-1.34-1.79-1.34-1.79-1.1-.75.08-.74.08-.74 1.21.09 1.85 1.24 1.85 1.24 1.08 1.85 2.83 1.32 3.52 1.01.11-.79.42-1.32.76-1.62-2.67-.3-5.47-1.33-5.47-5.92 0-1.31.47-2.38 1.24-3.22-.12-.3-.54-1.53.12-3.19 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 016 0c2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.24 2.9.12 3.19.77.84 1.23 1.91 1.23 3.22 0 4.6-2.8 5.61-5.48 5.91.43.37.81 1.1.81 2.22v3.29c0 .32.22.69.82.57A12 12 0 0012 .5z" />
//     </svg>
//   );
// }

// function linkedinIcon() {
//   return (
//     <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
//       <path d="M4.98 3.5C3.88 3.5 3 4.37 3 5.47s.88 1.97 1.98 1.97h.02C6.07 7.44 7 6.57 7 5.47S6.07 3.5 4.98 3.5zM3.5 8.98h3v12.02h-3V8.98zM9.5 8.98h2.88v1.64h.04c.4-.76 1.37-1.56 2.82-1.56 3.02 0 3.58 1.99 3.58 4.58v6.38h-3V16.3c0-1.31-.02-2.99-1.82-2.99-1.82 0-2.09 1.42-2.09 2.89v5.8h-3V8.98z" />
//     </svg>
//   );
// }

// function mailIcon() {
//   return (
//     <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
//       <path d="M20 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z" />
//     </svg>
//   );
// }

import React from "react";
import "./YourNewPage.css";

function YourNewPage() {
  return (
    <div className="new-page-container">
      <div className="new-page-content">
        <h1>Your New Page</h1>
        <p>Welcome to your new page! This is a basic React component.</p>       
        <div className="info-section">
          <h2>About This Page</h2>
          <p>
            This page was created with minimal imports and is ready to be
            customized.
          </p>
        </div>
      </div>
    </div>
  );
}

export default YourNewPage;
