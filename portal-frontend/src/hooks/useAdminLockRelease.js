import { useEffect, useRef } from "react";

/**
 * Hook to release admin locks when the browser tab/window is closed.
 * Uses navigator.sendBeacon() to ensure the request is sent even during page unload.
 * Only releases locks if the session is still valid (not invalidated by another tab).
 *
 * @param {string} sessionId - The current admin session ID
 * @param {boolean} isSessionInvalid - Whether the session has been invalidated (e.g., opened in another tab)
 */
export const useAdminLockRelease = (sessionId, isSessionInvalid) => {
  // Use refs to access latest values in the unload handler
  const sessionIdRef = useRef(sessionId);
  const isSessionInvalidRef = useRef(isSessionInvalid);

  // Keep refs in sync with props
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  useEffect(() => {
    isSessionInvalidRef.current = isSessionInvalid;
  }, [isSessionInvalid]);

  useEffect(() => {
    const handleUnload = () => {
      // Don't release locks if session was invalidated (opened in another tab)
      if (isSessionInvalidRef.current || !sessionIdRef.current) {
        return;
      }

      // Use sendBeacon to reliably send the request during page unload
      const url = `${process.env.REACT_APP_BACKEND_URL}/admin/release-locks-beacon`;
      const data = new URLSearchParams({ session_id: sessionIdRef.current });

      navigator.sendBeacon(url, data);
    };

    window.addEventListener("unload", handleUnload);

    return () => {
      window.removeEventListener("unload", handleUnload);
    };
  }, []);
};
