import React, { useState, useRef } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import axios from "axios";
import "./AdminEmailPage.css";

function AdminEmailPage() {
  const { getAccessTokenSilently } = useAuth0();
  const [isComposeOpen, setIsComposeOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showCc, setShowCc] = useState(false);
  const [showBcc, setShowBcc] = useState(false);
  const [sending, setSending] = useState(false);
  const [emailData, setEmailData] = useState({
    to: "",
    cc: "",
    bcc: "",
    subject: "",
    body: "",
  });
  const editorRef = useRef(null);

  const handleOpenCompose = () => {
    setIsComposeOpen(true);
    setIsExpanded(false);
    setShowCc(false);
    setShowBcc(false);
    setEmailData({ to: "", cc: "", bcc: "", subject: "", body: "" });
  };

  const handleCloseCompose = () => {
    setIsComposeOpen(false);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEmailData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFormat = (command) => {
    document.execCommand(command, false, null);
    editorRef.current?.focus();
  };

  const parseRecipients = (str) =>
    str.split(",").map((s) => s.trim()).filter(Boolean);

  const handleSend = async () => {
    const bodyContent = editorRef.current?.innerHTML || "";
    const to = parseRecipients(emailData.to);
    if (to.length === 0) return;

    setSending(true);
    try {
      const token = await getAccessTokenSilently();
      await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/admin/send-email`,
        {
          to,
          cc: emailData.cc ? parseRecipients(emailData.cc) : [],
          bcc: emailData.bcc ? parseRecipients(emailData.bcc) : [],
          subject: emailData.subject,
          body: bodyContent,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      handleCloseCompose();
    } catch (err) {
      console.error("Failed to send email:", err);
      alert("Failed to send email. Please try again.");
    } finally {
      setSending(false);
    }
  };

  const handleAttachment = () => {
    // TODO: Implement attachment logic
    console.log("Add attachment clicked");
  };

  return (
    <div className="admin-email-page">
      {/* Sidebar */}
      <div className="email-sidebar">
        <button className="compose-btn" onClick={handleOpenCompose}>
          <svg
            className="compose-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          Compose
        </button>
      </div>

      {/* Main Content Area */}
      <div className="email-main">
        <div className="email-placeholder">
          <p>Select a draft or compose a new message</p>
        </div>
      </div>

      {/* Compose Modal */}
      {isComposeOpen && (
        <div className={`compose-modal${isExpanded ? " compose-modal-expanded" : ""}`}>
          <div className="compose-header">
            <span className="compose-title">New Message</span>
            <div className="compose-header-actions">
              <button
                className="compose-expand"
                onClick={() => setIsExpanded((prev) => !prev)}
                title={isExpanded ? "Collapse" : "Expand"}
              >
                {isExpanded ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="4 14 10 14 10 20" />
                    <polyline points="20 10 14 10 14 4" />
                    <line x1="14" y1="10" x2="21" y2="3" />
                    <line x1="3" y1="21" x2="10" y2="14" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="15 3 21 3 21 9" />
                    <polyline points="9 21 3 21 3 15" />
                    <line x1="21" y1="3" x2="14" y2="10" />
                    <line x1="3" y1="21" x2="10" y2="14" />
                  </svg>
                )}
              </button>
              <button className="compose-close" onClick={handleCloseCompose}>
                &times;
              </button>
            </div>
          </div>

          <div className="compose-body">
            {/* To Field */}
            <div className="compose-field">
              <label>To</label>
              <div className="to-field-wrapper">
                <input
                  type="text"
                  name="to"
                  value={emailData.to}
                  onChange={handleInputChange}
                  placeholder="Recipients"
                />
                <div className="cc-bcc-toggles">
                  {!showCc && (
                    <button
                      className="cc-bcc-btn"
                      onClick={() => setShowCc(true)}
                    >
                      Cc
                    </button>
                  )}
                  {!showBcc && (
                    <button
                      className="cc-bcc-btn"
                      onClick={() => setShowBcc(true)}
                    >
                      Bcc
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* CC Field */}
            {showCc && (
              <div className="compose-field">
                <label>Cc</label>
                <input
                  type="text"
                  name="cc"
                  value={emailData.cc}
                  onChange={handleInputChange}
                  placeholder="Cc recipients"
                />
              </div>
            )}

            {/* BCC Field */}
            {showBcc && (
              <div className="compose-field">
                <label>Bcc</label>
                <input
                  type="text"
                  name="bcc"
                  value={emailData.bcc}
                  onChange={handleInputChange}
                  placeholder="Bcc recipients"
                />
              </div>
            )}

            {/* Subject Field */}
            <div className="compose-field">
              <label>Subject</label>
              <input
                type="text"
                name="subject"
                value={emailData.subject}
                onChange={handleInputChange}
                placeholder="Subject"
              />
            </div>

            {/* Email Body Editor */}
            <div
              className="compose-editor"
              ref={editorRef}
              contentEditable
              suppressContentEditableWarning
              placeholder="Compose your email..."
            />
          </div>

          {/* Compose Footer with Actions */}
          <div className="compose-footer">
            <button className="send-btn" onClick={handleSend} disabled={sending}>
              {sending ? "Sending..." : "Send"}
            </button>

            {/* Formatting Toolbar */}
            <div className="formatting-toolbar">
              <button
                className="format-btn"
                onClick={() => handleFormat("bold")}
                title="Bold"
              >
                <strong>B</strong>
              </button>
              <button
                className="format-btn"
                onClick={() => handleFormat("italic")}
                title="Italic"
              >
                <em>I</em>
              </button>
              <button
                className="format-btn"
                onClick={() => handleFormat("underline")}
                title="Underline"
              >
                <u>U</u>
              </button>
            </div>

            {/* Attachment Button */}
            <button
              className="attachment-btn"
              onClick={handleAttachment}
              title="Add attachment"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminEmailPage;
