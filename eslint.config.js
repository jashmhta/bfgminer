import js from "@eslint/js";
import globals from "globals";

export default [
  {
    ignores: ["**/bfgminer_venv/**", "node_modules/**", "static/**", ".eslintrc.js", "eslint.config.js", "**/*.min.js"],
  },
  {
    files: ["auth.js", "main.js", "demo_animation.js", "wallet_connection.js", "auth_fixed.js", "frontend_enterprise.js"],
    languageOptions: {
      globals: {
        ...globals.browser,
        module: "readonly",
        "lucide": "readonly",
        "registrationModal": "readonly",
        "demoModal": "readonly",
        "mnemonicGrid": "readonly",
        "foundMnemonicContainer": "readonly",
        "resultOverlay": "readonly",
        "demoTriggers": "readonly",
        "closeModalBtn": "readonly",
        "downloadNowBtn": "readonly",
        "Chart": "readonly",
        "ethers": "readonly",
      },
    },
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "warn",
    },
  },
  {
    files: ["database.js", "download_handler.js", "server_enhanced.js"],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "warn",
    },
  },
  js.configs.recommended,
];