import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';

const root = document.getElementById('root');
if (!root) {
  throw new Error('No root element found with id "root"');
}

ReactDOM.render(<App />, root);

