/**
 * QuestMaster API client.
 *
 * Shared helper for calling /api/v1/ endpoints from browser JS.
 * Uses session cookies (credentials: 'same-origin') so that logged-in
 * users can call the API without managing JWT tokens.
 */
(function () {
  "use strict";

  var BASE = "/api/v1";

  function buildUrl(path, params) {
    var url = new URL(BASE + path, window.location.origin);
    if (params) {
      Object.keys(params).forEach(function (key) {
        var value = params[key];
        if (value !== undefined && value !== null) {
          url.searchParams.set(key, value);
        }
      });
    }
    return url.toString();
  }

  function get(path, params) {
    return fetch(buildUrl(path, params), {
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    }).then(function (response) {
      if (!response.ok) {
        var err = new Error("API error " + response.status);
        err.status = response.status;
        return response
          .json()
          .catch(function () {
            return null;
          })
          .then(function (data) {
            err.data = data;
            throw err;
          });
      }
      return response.json();
    });
  }

  window.QuestMasterAPI = { get: get };
})();
