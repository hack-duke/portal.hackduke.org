import { CFG_APPLICATION_2026 } from "./2026-cfg-application";
import { JUDGE_APPLICATION_2026 } from "./2026-judge-application";

export const FORMS = {
  [CFG_APPLICATION_2026.formKey]: CFG_APPLICATION_2026,
  [JUDGE_APPLICATION_2026.formKey]: JUDGE_APPLICATION_2026,
};

export const getFormByKey = (formKey) => {
  return FORMS[formKey] || null;
};

export const getAllForms = () => {
  return Object.values(FORMS);
};
