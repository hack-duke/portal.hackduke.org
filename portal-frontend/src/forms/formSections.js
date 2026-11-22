import React from "react";
import {
  LongQuestion,
  CheckQuestion,
  FileUploadQuestion,
} from "../components/form/Form";

const kindOf = (element) => {
  if (element.type === LongQuestion) return "long";
  if (element.type === CheckQuestion) return "check";
  if (element.type === FileUploadQuestion) return "file";
  return "short";
};

/**
 * Reads a form definition's <Page>/<Question> tree and returns its sections:
 * [{ title, questions: [{ name, label, kind }] }], where kind is
 * "short" | "long" | "check" | "file". Lets other pages (like the status page)
 * show answers with the same wording and order as the form itself.
 */
export const getFormSections = (formDefinition) =>
  React.Children.toArray(formDefinition.renderForm()).map((page) => ({
    title: page.props.title,
    questions: React.Children.toArray(page.props.children)
      .filter((child) => child.props?.name)
      .map((child) => ({
        name: child.props.name,
        // CheckQuestion puts its label in children (it can contain links).
        label: child.props.label ?? child.props.children,
        kind: kindOf(child),
      })),
  }));
