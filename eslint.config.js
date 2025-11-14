import config from "@antfu/eslint-config"
import simpleImportSort from "eslint-plugin-simple-import-sort"
import vuePug from "eslint-plugin-vue-pug"

export default config(
  {
    plugins: {
      "simple-import-sort": simpleImportSort,
    },
    formatters: {
      css: true,
    },
    stylistic: {
      quotes: "double",
    },
    rules: {
      // always add if { ... } braces
      "curly": ["error", "all"],
      // allow console.log
      "no-console": "warn",
      // allow arrays [, a]
      "no-sparse-arrays": "off",
      // allow string + string
      "prefer-template": "off",
      // sort imports
      "simple-import-sort/imports": "error",
      "simple-import-sort/exports": "error",
      "import/order": "off",
      "sort-imports": "off",
      // put if { at one line
      "style/brace-style": ["error", "1tbs"],
      // allow @ts-ignore
      "ts/ban-ts-comment": "off",
      // allow interace method as arrow fn
      "ts/method-signature-style": "off",
    },
  },
  {
    // vue-pug doesn't support eslint flat config
    // this is hand-crafted from eslint-plugin-vue-pug/lib/configs/base.js
    // see. https://github.com/rashfael/eslint-plugin-vue-pug/issues/28
    name: "vue-pug",
    files: ["**/*.vue"],
    languageOptions: {
      parserOptions: {
        templateTokenizer: { pug: "vue-eslint-parser-template-tokenizer-pug" },
      },
    },
    plugins: {
      "vue-pug": vuePug,
    },
    rules: {
      // base
      "vue/component-name-in-template-casing": "off",
      "vue/html-self-closing": "off",
      "vue/html-end-tags": "off",
      "vue/html-indent": "off",
      "vue/multiline-html-element-content-newline": "off",
      "vue/singleline-html-element-content-newline": "off",
      // vue3-essential
      "vue-pug/no-parsing-error": "error",
      // vue3-strongly-recommended
      "vue-pug/no-pug-control-flow": "warn",
    },
  },
  {
    files: ["**/*.vue"],
    rules: {
      // <component-name>
      "vue/component-name-in-template-casing": ["error", "kebab-case"],
      // allow v-for without :key
      "vue/require-v-for-key": "off",
    },
  },
)
