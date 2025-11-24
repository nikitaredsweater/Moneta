// eslint.config.cjs
const js = require("@eslint/js");
const tseslint = require("typescript-eslint");

const tsFiles = ["**/*.ts"];

module.exports = [
  // Ignore (replaces .eslintignore)
  { ignores: ["dist/**", "node_modules/**", "eslint.config.cjs"] },

  // JS files
  {
    files: ["**/*.{js,cjs,mjs}"],
    ...js.configs.recommended,
  },

  // TS (untyped) rules, scoped to .ts files
  ...tseslint.configs.recommended.map((cfg) => ({
    ...cfg,
    files: tsFiles,
    languageOptions: {
      parser: tseslint.parser,
    },
  })),

  // TS *typed* rules, scoped to .ts files with project info
  ...tseslint.configs.recommendedTypeChecked.map((cfg) => ({
    ...cfg,
    files: tsFiles,
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        project: ["./tsconfig.json"],
        tsconfigRootDir: __dirname,
      },
    },
  })),

  // Your custom TS rules
  {
    files: tsFiles,
    plugins: { "@typescript-eslint": tseslint.plugin },
    rules: {
      "@typescript-eslint/consistent-type-imports": [
        "warn",
        { prefer: "type-imports" },
      ],
      "@typescript-eslint/no-misused-promises": [
        "error",
        { checksVoidReturn: false },
      ],
      "no-console": "off",
    },
  },
];
