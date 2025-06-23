// build_faceapi.mjs – bundle eval-free face-api for strict CSP sites
import { build }         from "esbuild";
import { readFileSync }  from "node:fs";
import { createRequire } from "node:module";
import path              from "node:path";

const require = createRequire(import.meta.url);
const entry   = require.resolve("@vladmandic/face-api/dist/face-api.esm.js");

// scrub new Function/eval helpers (tiny loader stubs only)
const code = readFileSync(entry, "utf8")
               .replace(/new Function\([\s\S]*?\)\)/g, "()=>{}");

await build({
  stdin: { contents: code, resolveDir: path.dirname(entry) },
  bundle: true,
  minify: true,
  format: "iife",
  globalName: "faceapi",
  target: "es2019",
  outfile: "static/face-api.bundle.js",
});

console.log("✓ static/face-api.bundle.js built – no eval required");
