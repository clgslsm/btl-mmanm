import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import Keycloak from 'keycloak-js';

const keycloak = new Keycloak({
  url: 'http://localhost:8080/',
  realm: 'demo-sso-realm',
  clientId: 'react-app',
});

keycloak.init({ onLoad: 'login-required' }).then((authenticated) => {
  if (!authenticated) {
    keycloak.login();
  } else {
    console.log("Authenticated");

    ReactDOM.render(
      <React.StrictMode>
        <App keycloak={keycloak} />
      </React.StrictMode>,
      document.getElementById('root')
    );
  }

}).catch(() => {
  console.log("Authentication Failed");
});
