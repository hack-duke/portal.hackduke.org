import React, { useState, useRef } from "react";
import "./AdminEmailPage.css";

function AdminEmailPage() {
  const [isComposeOpen, setIsComposeOpen] = useState(false);
  const [showCc, setShowCc] = useState(false);
  const [showBcc, setShowBcc] = useState(false);
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

  const handleSend = () => {
    const bodyContent = editorRef.current?.innerHTML || "";
    console.log("Sending email:", { ...emailData, body: bodyContent });
    // TODO: Implement actual send logic
    handleCloseCompose();
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
          <p>Select an email or compose a new message</p>
        </div>
      </div>

      {/* Compose Modal */}
      {isComposeOpen && (
        <div className="compose-modal">
          <div className="compose-header">
            <span className="compose-title">New Message</span>
            <button className="compose-close" onClick={handleCloseCompose}>
              &times;
            </button>
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
            <button className="send-btn" onClick={handleSend}>
              Send
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
