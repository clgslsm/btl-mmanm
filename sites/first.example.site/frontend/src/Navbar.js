import React from "react";
import { useKeycloak } from "@react-keycloak/web";
import { Link } from "react-router-dom";
import "./styles/Navbar.css";

function Navbar() {
  const { keycloak } = useKeycloak(); // Access the keycloak instance

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          MyApp
        </Link>
        <ul className="navbar-links">
          <li>
            <Link to="/" className="navbar-link">
              Home
            </Link>
          </li>
          <li>
            <Link to="/profile" className="navbar-link">
              Profile
            </Link>
          </li>
          <li>
            <button
              className="navbar-button"
              onClick={() => {
                if (keycloak.authenticated) {
                    keycloak.logout({ redirectUri: window.location.origin }); // Logout if the user is authenticated
                } else {
                  keycloak.login(); // Login if the user is not authenticated
                }
              }}
            >
              {keycloak.authenticated ? "Logout" : "Login"}
            </button>
          </li>
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;
