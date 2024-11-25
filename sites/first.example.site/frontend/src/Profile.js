import React, { useState, useEffect } from "react";
import { useKeycloak } from "@react-keycloak/web";
import { jwtDecode } from "jwt-decode"; // Use named import
import './styles/Profile.css'; // Import custom CSS for styling

const Profile = () => {
  const { keycloak } = useKeycloak();
  const [userInfo, setUserInfo] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const [expiryTime, setExpiryTime] = useState(null);
  const [isTokenVisible, setIsTokenVisible] = useState(false); // State to track token visibility

  useEffect(() => {
    if (keycloak.authenticated) {
      const decodedToken = jwtDecode(keycloak.token); // Decode the token
      setUserInfo(decodedToken);

      // Set the expiry time from token's exp claim (in seconds)
      const expTime = new Date(decodedToken.exp * 1000);
      setExpiryTime(expTime.toLocaleString());
    }
  }, [keycloak]);

  const handleShowToken = () => {
    setIsTokenVisible(!isTokenVisible); // Toggle the token visibility
    if (!isTokenVisible) {
      setAccessToken(keycloak.token); // Show the raw access token
    } else {
      setAccessToken(null); // Hide the token if already visible
    }
  };

  const handleUpdateToken = () => {
    keycloak.updateToken(600).then((refreshed) => {
      if (refreshed) {
        setAccessToken(keycloak.token); // Update the access token after refresh
        const updatedDecoded = jwtDecode(keycloak.token); // Decode the refreshed token
        setExpiryTime(new Date(updatedDecoded.exp * 1000).toLocaleString()); // Update expiry time
      } else {
        alert('Token is still valid within 2 minutes');
      }
    }).catch((error) => {
        alert(error);
    });
  };

  return (
    <div className="container">
      <h2>User Information</h2>
      {userInfo ? (
        <div className="user-info">
          <p><strong>Name:</strong> {userInfo.name}</p>
          <p><strong>Email:</strong> {userInfo.email}</p>
          <p><strong>Roles:</strong> {userInfo.realm_access?.roles.join(", ")}</p>
          <p><strong>Groups:</strong> {userInfo.groups?.join(", ") || "None"}</p>
          <p><strong>Token Expires At:</strong> {expiryTime}</p>
        </div>
      ) : (
        <p>Unable to retrieve user information.</p>
      )}

      {/* Buttons */}
      <div className="buttons">
        <button onClick={handleShowToken} className="button">
          {isTokenVisible ? "Hide Access Token" : "Show Access Token"}
        </button>
        {isTokenVisible && accessToken && (
          <div className="token-container">
            <p>Access Token:</p>
            <div className="token-value">{accessToken}</div>
          </div>
        )}

        <button onClick={handleUpdateToken} className="button">Update Token</button>
      </div>
    </div>
  );
};

export default Profile;
