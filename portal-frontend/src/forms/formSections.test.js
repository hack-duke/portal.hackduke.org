import { getFormSections } from "./formSections";
import { CFG_APPLICATION_2027 } from "./2027-cfg-application";

test("reads sections, labels and question kinds from the 2027 form", () => {
  const sections = getFormSections(CFG_APPLICATION_2027);
  expect(sections.map((s) => s.title)).toEqual([
    "General Information",
    "Education",
    "About You",
    "Agreements",
  ]);

  const byName = Object.fromEntries(
    sections.flatMap((s) => s.questions).map((q) => [q.name, q]),
  );
  expect(byName.resume.kind).toBe("file");
  expect(byName.major).toMatchObject({ kind: "short", label: "Major(s)" });
  expect(byName.why_hackduke.kind).toBe("long");
  expect(byName.waiver_agr.kind).toBe("check");
});
