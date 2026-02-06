import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";
import prettierConfigRecommended from "eslint-plugin-prettier/recommended";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
});

const eslintConfig = [
  ...compat.config({
    extends: ["plugin:@next/next/recommended", "next/typescript", "prettier"],
  }),
  prettierConfigRecommended,
  { ignores: [".next/*", "types/next-auth.d.ts"] },
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-implicit-any": "off",
      "@typescript-eslint/no-non-null-asserted-optional-chain": "off",
    },
  },
];

export default eslintConfig;
