import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
    url: "https://sso.example.org/",
    realm: "demo-sso-realm",
    clientId: "first.example.org",
});

export default keycloak;
