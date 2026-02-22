import React, { useState, useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import axios from "axios";
import Modal from "./Modal";
import Button from "./Button";
import { createGetAuthToken } from "../utils/authUtils";
import "./QuestionEditorModal.css";

const QuestionEditorModal = ({
  isOpen,
  question,
  formKey,
  sessionId,
  onSave,
  onClose,
  onError,
}) => {
  const { getAccessTokenSilently } = useAuth0();
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    question_key: "",
    question_type: "text",
    label: "",
    placeholder: "",
    description: "",
    required: false,
    page_number: 1,
    page_title: "",
    order_in_page: 0,
    config: {},
  });

  useEffect(() => {
    if (question) {
      // Editing existing question
      setFormData({
        question_key: question.question_key,
        question_type: question.question_type || "text",
        label: question.label || "",
        placeholder: question.placeholder || "",
        description: question.description || "",
        required: question.required || false,
        page_number: question.page_number || 1,
        page_title: question.page_title || "",
        order_in_page: question.order_in_page || 0,
        config: question.config || {},
      });
    } else {
      // Creating new question
      setFormData({
        question_key: "",
        question_type: "text",
        label: "",
        placeholder: "",
        description: "",
        required: false,
        page_number: 1,
        page_title: "",
        order_in_page: 0,
        config: {},
      });
    }
  }, [question, isOpen]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === "checkbox" ? checked : value,
    });
  };

  const handleConfigChange = (key, value) => {
    setFormData({
      ...formData,
      config: {
        ...formData.config,
        [key]: value,
      },
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.question_key || !formData.label) {
      onError?.("Question key and label are required.");
      return;
    }

    try {
      setSaving(true);
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, onError);
      const token = await getAuthToken();
      if (!token) {
        setSaving(false);
        return;
      }

      const preparedData = {
        ...formData,
        page_number: parseInt(formData.page_number),
        order_in_page: parseInt(formData.order_in_page),
      };

      if (question) {
        // Update existing question
        await axios.put(
          `${process.env.REACT_APP_BACKEND_URL}/admin/forms/${formKey}/questions/${question.id}`,
          preparedData,
          {
            headers: { Authorization: `Bearer ${token}` },
            params: { session_id: sessionId },
          }
        );
      } else {
        // Create new question
        await axios.post(
          `${process.env.REACT_APP_BACKEND_URL}/admin/forms/${formKey}/questions`,
          preparedData,
          {
            headers: { Authorization: `Bearer ${token}` },
            params: { session_id: sessionId },
          }
        );
      }

      setSaving(false);
      onSave?.();
    } catch (err) {
      setSaving(false);
      onError?.(
        err.response?.data?.detail ||
          `Failed to ${question ? "update" : "create"} question.`
      );
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      title={question ? "Edit Question" : "Add Question"}
      onClose={onClose}
    >
      <form onSubmit={handleSubmit} className="question-form">
        {/* Question Key */}
        <div className="form-group">
          <label htmlFor="question_key">Question Key *</label>
          <input
            id="question_key"
            name="question_key"
            type="text"
            placeholder="e.g., first_name"
            value={formData.question_key}
            onChange={handleInputChange}
            disabled={!!question}
            title={
              question ? "Cannot change question key after creation" : undefined
            }
            required
          />
          <small>Unique identifier within the form</small>
        </div>

        {/* Question Type */}
        <div className="form-group">
          <label htmlFor="question_type">Question Type *</label>
          <select
            id="question_type"
            name="question_type"
            value={formData.question_type}
            onChange={handleInputChange}
            required
          >
            <option value="text">Text (Short)</option>
            <option value="boolean">Checkbox</option>
            <option value="file">File Upload</option>
            <option value="integer">Integer</option>
            <option value="float">Float/Decimal</option>
          </select>
        </div>

        {/* Label */}
        <div className="form-group">
          <label htmlFor="label">Label *</label>
          <input
            id="label"
            name="label"
            type="text"
            placeholder="Display text for users"
            value={formData.label}
            onChange={handleInputChange}
            required
          />
        </div>

        {/* Placeholder */}
        <div className="form-group">
          <label htmlFor="placeholder">Placeholder</label>
          <input
            id="placeholder"
            name="placeholder"
            type="text"
            placeholder="e.g., John Doe"
            value={formData.placeholder}
            onChange={handleInputChange}
          />
        </div>

        {/* Description */}
        <div className="form-group">
          <label htmlFor="description">Description/Help Text</label>
          <textarea
            id="description"
            name="description"
            rows="2"
            placeholder="Additional instructions for users"
            value={formData.description}
            onChange={handleInputChange}
          />
        </div>

        {/* Required */}
        <div className="form-group checkbox">
          <input
            id="required"
            name="required"
            type="checkbox"
            checked={formData.required}
            onChange={handleInputChange}
          />
          <label htmlFor="required">Required Field</label>
        </div>

        {/* Page Settings */}
        <div className="form-divider">Page Settings</div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="page_number">Page Number</label>
            <input
              id="page_number"
              name="page_number"
              type="number"
              min="1"
              value={formData.page_number}
              onChange={handleInputChange}
            />
          </div>

          <div className="form-group">
            <label htmlFor="order_in_page">Order in Page</label>
            <input
              id="order_in_page"
              name="order_in_page"
              type="number"
              min="0"
              value={formData.order_in_page}
              onChange={handleInputChange}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="page_title">Page Title</label>
          <input
            id="page_title"
            name="page_title"
            type="text"
            placeholder="e.g., General Information"
            value={formData.page_title}
            onChange={handleInputChange}
          />
        </div>

        {/* Type-specific Config */}
        {formData.question_type === "text" && (
          <div>
            <div className="form-divider">Text Settings</div>
            <div className="form-group">
              <label htmlFor="rows">Rows (for multiline text)</label>
              <input
                id="rows"
                type="number"
                min="1"
                value={formData.config.rows || ""}
                onChange={(e) =>
                  handleConfigChange("rows", e.target.value ? parseInt(e.target.value) : undefined)
                }
                placeholder="Leave empty for single-line"
              />
              <small>Leave empty for single-line text field</small>
            </div>
          </div>
        )}

        {formData.question_type === "file" && (
          <div>
            <div className="form-divider">File Settings</div>
            <div className="form-group">
              <label htmlFor="accept">File Type (MIME type)</label>
              <input
                id="accept"
                type="text"
                value={formData.config.accept || ""}
                onChange={(e) => handleConfigChange("accept", e.target.value)}
                placeholder="e.g., application/pdf or image/*"
              />
              <small>Leave empty to allow any file type</small>
            </div>
          </div>
        )}

        {formData.question_type === "boolean" && (
          <div>
            <div className="form-divider">Checkbox Settings</div>
            <div className="form-group">
              <label htmlFor="checkboxText">Checkbox Text</label>
              <input
                id="checkboxText"
                type="text"
                value={formData.config.checkboxText || ""}
                onChange={(e) => handleConfigChange("checkboxText", e.target.value)}
                placeholder="Text displayed next to checkbox"
              />
            </div>
          </div>
        )}

        {/* Form Actions */}
        <div className="modal-actions">
          <Button type="submit" disabled={saving}>
            {saving ? "Saving..." : question ? "Update Question" : "Add Question"}
          </Button>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default QuestionEditorModal;
