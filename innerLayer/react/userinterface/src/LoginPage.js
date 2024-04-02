import React, { useState, useEffect, useRef } from 'react';
import logo from './logo.svg';
import './App.css';

function LoginPage({webSocket, isConnected, isRegistered, username, setUsername,  password, setPassword,  email, setEmail, invalidPassword}) {
  const handleUsernameChange = (event) => {
    setUsername(event.target.value);
  };
 
  const handlePasswordChange = (event) => {
    setPassword(event.target.value);
  };

  const handleEmailChange = (event) => {
    setEmail(event.target.value);
  };

  const handleLogIn = (event) => {
    const loginData = {
      action: 'login',
      username: username,
      password: password,
    };
    webSocket.current.send(JSON.stringify(loginData));
  }

  const handleRegistration = () => {
    const credentials = { username: username, password: password, email: email };
    localStorage.setItem('credentials', JSON.stringify(credentials));
    const registrationData = {
      action: 'register',
      username: username,
      password: password,
      email:    email,
    };
    webSocket.current.send(JSON.stringify(registrationData));
  };

  return (
    <>
      {!isConnected ? (
        <h3>Failed To Connect to Server. Ensure 'server.js' is running. If it is running, ensure you have created the .env file</h3>
      ) : isRegistered ? (
        <>
          <input type="text" placeholder="Username" value={username} onChange={handleUsernameChange} />
          <input type="password" placeholder="Password" value={password} onChange={handlePasswordChange}
                 onKeyDown={(e) => { if (e.key === "Enter") {handleLogIn()}}}/>
          <button onClick={handleLogIn}>Log In</button>

          {invalidPassword ? <h3 style={{color: 'red'}}>Invalid Username or Password</h3> : ""}

          
        </>
      ) : (
        <>
          <input type="text" placeholder="Username" value={username} onChange={handleUsernameChange} />
          <input type="password" placeholder="Password" value={password} onChange={handlePasswordChange} 
                 onKeyDown={(e)=>{if (e.key === "Enter") {handleLogIn()}}}/>
          <input type="email" placeholder="Email" value={email} onChange={handleEmailChange} />
          <button onClick={handleRegistration}>Register</button>
        </>
      )}
    </>
  );
}

export default LoginPage;