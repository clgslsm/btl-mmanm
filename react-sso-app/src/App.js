import React from 'react';

function App({ keycloak }) {
  return (
    <div className="App">
      <h1>React App</h1>
      <h2>User Profile</h2>
      <p><strong>Username:</strong> {keycloak.tokenParsed.preferred_username}</p>
      <p><strong>Email:</strong> {keycloak.tokenParsed.email}</p>
    </div>
  );
}

export default App;
