// Allure 3 report settings (npx allure@3.22.1 generate allure-results).
// The tree follows the labels set in tests/conftest.py (report_groups): Web or Mobile, then the platform or layer, then the area.
export default {
  name: "FAR Notes tests",
  output: "./allure-report",
  plugins: {
    awesome: {
      options: {
        groupBy: ["parentSuite", "suite", "subSuite"],
      },
    },
  },
};
