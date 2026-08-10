#!/usr/bin/env node
// Validate the schemas in schemas/ and their example instances, fully offline.
//
//   1. every *.schema.json compiles under JSON Schema 2020-12 (ajv), with
//      formats enforced (ajv-formats + ajv-formats-draft2019 for iri/idn-*);
//   2. its $ref composition resolves from disk (json-schema-ref-parser), so a
//      broken or missing local reference fails the build;
//   3. every *.instance.json validates against the schema of the same name;
//   4. schemas carrying an @context work as a JSON-LD context: a document is
//      expanded through it, exercising the term definitions. A loader maps the
//      local schema files and refuses network fetches, so runs are deterministic.
//
// Pass a directory to validate schemas elsewhere: `node scripts/validate.mjs dir`.
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import addFormats2019 from "ajv-formats-draft2019";
import $RefParser from "@apidevtools/json-schema-ref-parser";
import jsonld from "jsonld";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const dir = process.argv[2] ? resolve(process.cwd(), process.argv[2]) : join(root, "schemas");
const BASE = "https://schemas.example.org/";

const schemaFiles = readdirSync(dir).filter((f) => f.endsWith(".schema.json"));
const instanceFiles = readdirSync(dir).filter((f) => f.endsWith(".instance.json"));
if (schemaFiles.length === 0) {
  console.error(`No *.schema.json found in ${dir}`);
  process.exit(1);
}

const read = (file) => JSON.parse(readFileSync(join(dir, file), "utf8"));
const failures = [];
const fail = (what, error) => failures.push(`${what}: ${error.message ?? error}`);

const ajv = new Ajv2020({ strict: false, allErrors: true, loadSchema: async () => ({}) });
addFormats(ajv);
addFormats2019(ajv);

// 1 + 2: schemas compile and their references resolve.
const compiled = new Map();
for (const file of schemaFiles) {
  const schema = read(file);
  try {
    const resolved = await $RefParser.dereference(join(dir, file), { dereference: { circular: "ignore" } });
    compiled.set(file, ajv.compile(resolved));
  } catch (error) {
    fail(file, error);
  }
}

// 3: committed instances validate against their schema.
for (const file of instanceFiles) {
  const schemaFile = file.replace(/\.instance\.json$/, ".schema.json");
  const validate = compiled.get(schemaFile);
  if (!validate) {
    fail(file, `no schema ${schemaFile} to validate against`);
    continue;
  }
  if (!validate(read(file))) {
    fail(file, ajv.errorsText(validate.errors));
  }
}

// 4: schemas that carry an @context work as a JSON-LD context.
const documentLoader = async (url) => {
  const name = url.startsWith(BASE) ? url.slice(BASE.length) : null;
  if (name && schemaFiles.includes(name)) {
    return { document: read(name), documentUrl: url, contextUrl: null };
  }
  throw new Error(`refusing to fetch ${url} (offline validation)`);
};
for (const file of schemaFiles) {
  const schema = read(file);
  if (!schema["@context"]) continue;
  try {
    await jsonld.expand({ "@context": schema["@context"], "@id": `${BASE}subject` }, { documentLoader });
  } catch (error) {
    fail(`${file} (@context)`, error);
  }
}

if (failures.length > 0) {
  console.error(`\n${failures.length} problem(s):`);
  for (const problem of failures) console.error(`  - ${problem}`);
  process.exit(1);
}
console.log(
  `OK: ${schemaFiles.length} schema(s), ${instanceFiles.length} instance(s) validated in ${dir}`,
);
