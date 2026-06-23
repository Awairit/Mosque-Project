import nextVitals from "eslint-config-next/core-web-vitals";

const eslintConfig = [
  ...nextVitals,
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "next-env.d.ts",
      "next.config.mjs",
      "postcss.config.js",
    ],
  },
];

export default eslintConfig;
