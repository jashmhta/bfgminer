import js from "@eslint/js";
import globals from "globals";

export default [
  {
    ignores: ["venv/**", "static/**"],
  },
  {
    files: ["auth.js", "main.js", "demo_animation.js", "wallet_connection.js"],
    languageOptions: {
      globals: {
        ...globals.browser,
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