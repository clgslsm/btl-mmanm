import React from "react";
import { useKeycloak } from "@react-keycloak/web";
import { Link } from "react-router-dom";
import "./styles/Home.css";

function Home() {
  const { keycloak } = useKeycloak();

  return (
    <div className="home-container">
      <h1 className="home-title">Welcome to MyApp</h1>
      <p className="home-subtitle">
        {keycloak.authenticated
          ? `Hello, ${keycloak.tokenParsed?.name || "User"}!`
          : "Please login to access more features."}
      </p>
      <div className="home-buttons">
        <Link to="/public">
          <button className="home-button">Public Page</button>
        </Link>
        {keycloak.authenticated && (
          <Link to="/course">
            <button className="home-button">Course Information</button>
          </Link>
        )}
      </div>
    </div>
  );
}

export default Home;
