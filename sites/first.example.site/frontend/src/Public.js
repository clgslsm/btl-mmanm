import React from "react";
import "./styles/Public.css";

function Public() {
  return (
    <div className="public-container">
      <h1 className="public-title">Public Page</h1>
      <p className="public-subtitle">
        This page is accessible to everyone, even if you are not logged in.
      </p>
    </div>
  );
}

export default Public;
