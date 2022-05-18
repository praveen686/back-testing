import logo from './logo.svg';
import './App.css';
import React, { useState, useEffect } from 'react';


function App() {
  return (
    <div className="App">
      <StartAnalyzer></StartAnalyzer>
    </div>
  );
}


class StartAnalyzer extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      ectoken: ""
    };
  }

  componentDidMount() {

  }
  upateEctoken(evt) {
    const val = evt.target.value;
    this.setState({
      ectoken: val
    });
  }

  updateEnctoken() {
    fetch('https://reqres.in/api/posts', requestOptions)
      .then(response => response.json())
      .then(data => this.setState({ postId: data.id }));
  }

  postData() {
    const requestOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'React POST Request Example' })
    };
    fetch(`http://localhost:5000/settoken?ectoken=${this.state.ectoken}`, requestOptions)
      .then(response => response.json())
      .then(data => this.setState({ postId: data.id }));
  }


  render() {
    return (
      <>
        <input value={this.state.ectoken} onChange={evt => this.upateEctoken(evt)} />
        <input type="button" onClick={() => this.postData()}></input>
      </>

    );
  }
}


class MyComponent extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      error: null,
      isLoaded: false,
      items: []
    };
  }

  componentDidMount() {
    fetch("http://localhost:5000/testtest")
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            isLoaded: true,
            items: result
          });
        },
        // Note: it's important to handle errors here
        // instead of a catch() block so that we don't swallow
        // exceptions from actual bugs in components.
        (error) => {
          this.setState({
            isLoaded: true,
            error
          });
        }
      )
  }


  render() {
    const { error, isLoaded, items } = this.state;
    if (error) {
      return <div>Error: {error.message}</div>;
    } else if (!isLoaded) {
      return <div>Loading...</div>;
    } else {
      return (
        <ul>
          {items.map(item => (
            <li key={item.id}>
              werewr
            </li>
          ))}
        </ul>
      );
    }
  }
}

export default App;
