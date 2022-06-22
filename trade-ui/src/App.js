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
      encToken: "",
      buyLegPrice: 0,
      finalPrice: -1
    };
  }

  componentDidMount() {

  }
  updateEnctoken() {
    const requestOptions = {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
      // body: JSON.stringify({ title: 'React POST Request Example' })
    };

    fetch(`http://localhost:5000/setenctoken?encToken=${encodeURIComponent(this.state.encToken)}`)
      .then(response => response.json())
      .then(data => this.setState({ postId: data.id }));
  }
  getFinalMargin() {
    const requestOptions = {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    };

    fetch(`http://localhost:5000/findmargin?buyLegPrice=${this.state.buyLegPrice}`)
      .then(response => response.json())
      .then(data => { 
        console.log(data); 
        this.setState({finalPrice:data.data.final.total})
      });
  }

  render() {
    return (
      <>
        <input value={this.state.encToken} onChange={evt => this.setState({ encToken: evt.target.value })} />
        <input type="button" onClick={() => this.updateEnctoken()} value="token"></input>
        <input value={this.state.buyLegPrice} onChange={evt => this.setState({ buyLegPrice: evt.target.value })} />
        <input type="button" onClick={() => this.getFinalMargin()} value="buy"></input>
        <div>{this.state.finalPrice}</div>
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
