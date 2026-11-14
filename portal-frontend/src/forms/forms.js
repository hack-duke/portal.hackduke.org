import { CFG_APPLICATION_2027 } from "./2027-cfg-application";

export const FORMS = {
  [CFG_APPLICATION_2027.formKey]: CFG_APPLICATION_2027,
};

export const getFormByKey = (formKey) => {
  return FORMS[formKey] || null;
};

export const getAllForms = () => {
  return Object.values(FORMS);
};
