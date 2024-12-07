import React, { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { ReactKeycloakProvider } from "@react-keycloak/web";
import keycloakClient from "./keycloak";
import Home from "./Home";
import Course from "./Course";
import Profile from "./Profile";
import Public from "./Public";
import Navbar from "./Navbar";
import { useKeycloak } from "@react-keycloak/web";

const PrivateRoute = ({ children }) => {
  const { keycloak, initialized } = useKeycloak();

  // Wait until Keycloak is initialized before performing any actions
  useEffect(() => {
    if (initialized && !keycloak.authenticated) {
      keycloak.login(); // Trigger login if not authenticated
    }
  }, [initialized, keycloak]);

  // If not authenticated, we don't render the children yet, as login will be triggered
  if (!initialized || !keycloak.authenticated) {
    return null; // Prevent rendering children until the login flow completes
  }

  return children;
};
function App() {
  return (
    <ReactKeycloakProvider authClient={keycloakClient}>
      <Router>
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/public" element={<Public />} />
          <Route
            path="/course"
            element={
              <PrivateRoute>
                <Course />
              </PrivateRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <Profile />
              </PrivateRoute>
            }
          />
        </Routes>
      </Router>
    </ReactKeycloakProvider>
  );
}

export default App;
