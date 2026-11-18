# Example module

A placeholder. A repository holds one module, under `modules/<name>/`, with a `module.json` and its
`*.schema.json` files. Rename this directory and `name` in `module.json`, then replace the schema.

Give each schema an `x-oold-uuid` of its own (a random UUID, for example from `uuidgen`): it is what keeps a schema's identity stable when it is renamed. The validator warns until you do. The example has none, because a UUID shipped in a template would be shared by every repository generated from it.

Every module needs at least one `*.instance.json` next to its schemas: `make test` validates the schemas against it and reads the module through it.
