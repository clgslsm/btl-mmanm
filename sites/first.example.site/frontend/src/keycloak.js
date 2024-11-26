import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: "https://sso.example.org/",
  realm: "demo-sso-realm",
  clientId: "react-app",
});

export default keycloak;
