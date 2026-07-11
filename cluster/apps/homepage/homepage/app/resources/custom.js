// Workaround for an upstream bug: the search widget's selected provider is
// initialized from build-time fallback props (duckduckgo) and never updates
// to the configured custom provider unless localStorage says otherwise.
// Seed the choice so every browser gets the configured SearXNG search.
if (!localStorage.getItem("search-name")) {
  localStorage.setItem("search-name", "Custom")
}
