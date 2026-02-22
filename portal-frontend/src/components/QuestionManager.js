import React, { useState, useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import axios from "axios";
import Button from "./Button";
import Modal from "./Modal";
import QuestionEditorModal from "./QuestionEditorModal";
import { createGetAuthToken } from "../utils/authUtils";
import "./QuestionManager.css";

const QuestionManager = ({ formKey, sessionId, onError }) => {
  const { getAccessTokenSilently } = useAuth0();
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEditor, setShowEditor] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [questionToDelete, setQuestionToDelete] = useState(null);

  useEffect(() => {
    fetchQuestions();
  }, [formKey]);

  const fetchQuestions = async () => {
    try {
      setLoading(true);
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, onError);
      const token = await getAuthToken();
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/admin/forms/${formKey}/questions`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { session_id: sessionId },
        }
      );

      setQuestions(response.data);
    } catch (err) {
      onError?.("Failed to load questions");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    try {
      const getAuthToken = createGetAuthToken(getAccessTokenSilently, onError);
      const token = await getAuthToken();
      if (!token) return;

      await axios.delete(
        `${process.env.REACT_APP_BACKEND_URL}/admin/forms/${formKey}/questions/${questionId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { session_id: sessionId },
        }
      );

      setQuestionToDelete(null);
      await fetchQuestions();
    } catch (err) {
      onError?.("Failed to delete question");
    }
  };

  // Group questions by page
  const pageGroups = {};
  questions.forEach((q) => {
    const pageNum = q.page_number || 1;
    if (!pageGroups[pageNum]) {
      pageGroups[pageNum] = {
        pageNumber: pageNum,
        pageTitle: q.page_title || `Page ${pageNum}`,
        questions: [],
      };
    }
    pageGroups[pageNum].questions.push(q);
  });

  const pages = Object.values(pageGroups).sort(
    (a, b) => a.pageNumber - b.pageNumber
  );

  if (loading) {
    return <div className="loading">Loading questions...</div>;
  }

  return (
    <div className="question-manager">
      <div className="question-manager-header">
        <div className="question-count">
          {questions.length} {questions.length === 1 ? "question" : "questions"}
        </div>
        <Button onClick={() => setShowEditor(true)} variant="secondary">
          Add Question
        </Button>
      </div>

      {questions.length === 0 ? (
        <div className="empty-questions">
          <p>No questions yet. Add your first question to get started.</p>
        </div>
      ) : (
        <div className="pages-container">
          {pages.map((page) => (
            <div key={page.pageNumber} className="page-group">
              <h3 className="page-title">{page.pageTitle}</h3>
              <div className="questions-list">
                {page.questions
                  .sort((a, b) => a.order_in_page - b.order_in_page)
                  .map((question, index) => (
                    <div key={question.id} className="question-item">
                      <div className="question-info">
                        <div className="question-number">{index + 1}</div>
                        <div className="question-details">
                          <div className="question-label">
                            {question.label || question.question_key}
                          </div>
                          <div className="question-meta">
                            <span className="question-key">{question.question_key}</span>
                            <span className="question-type">{question.question_type}</span>
                            {question.required && (
                              <span className="question-required">required</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="question-actions">
                        <Button
                          variant="secondary"
                          onClick={() => {
                            setEditingQuestion(question);
                            setShowEditor(true);
                          }}
                        >
                          Edit
                        </Button>
                        <Button
                          variant="error"
                          onClick={() => setQuestionToDelete(question)}
                        >
                          Delete
                        </Button>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Question Editor Modal */}
      <QuestionEditorModal
        isOpen={showEditor}
        question={editingQuestion}
        formKey={formKey}
        sessionId={sessionId}
        onSave={async () => {
          setShowEditor(false);
          setEditingQuestion(null);
          await fetchQuestions();
        }}
        onClose={() => {
          setShowEditor(false);
          setEditingQuestion(null);
        }}
        onError={onError}
      />

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!questionToDelete}
        title="Delete Question?"
        onClose={() => setQuestionToDelete(null)}
      >
        <div className="delete-confirm">
          <p>
            Are you sure you want to delete{" "}
            <strong>{questionToDelete?.label || questionToDelete?.question_key}</strong>?
          </p>
          <p className="warning">This action cannot be undone.</p>
          <div className="modal-actions">
            <Button
              variant="error"
              onClick={() => handleDeleteQuestion(questionToDelete.id)}
            >
              Delete
            </Button>
            <Button
              variant="secondary"
              onClick={() => setQuestionToDelete(null)}
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default QuestionManager;
