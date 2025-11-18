import { CFG_APPLICATION_2025 } from "./2025-cfg-application";

export const FORMS = {
  [CFG_APPLICATION_2025.formKey]: CFG_APPLICATION_2025,
};

export const getFormByKey = (formKey) => {
  return FORMS[formKey] || null;
};

export const getAllForms = () => {
  return Object.values(FORMS);
};
