
import './App.css';
import React, { useState, useEffect } from 'react';
import { Styler } from './styles/Grid.styled'


function App() {
  return (
    <div className="App">
      <StartAnalyzer></StartAnalyzer>
    </div>
  );
}


type AnalyzerState = { encToken: string, buyLegPrice: number, finalPrice: number };

class StartAnalyzer extends React.Component<{}, AnalyzerState> {
  constructor(props: {}) {
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
      .then(data => console.log(data));
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
        this.setState({ finalPrice: data.data.final.total })
      });
  }

  render() {
    return (
      <Styler xs={{ gar: "20px", gtc: "max-content",jus:"center", rg: "5px" }}>
        <Styler xs={{ gtc: "500px 50px", cg: "5px" }}>
          <input value={this.state.encToken} onChange={evt => this.setState({ encToken: evt.target.value })} />
          <input type="button" onClick={() => this.updateEnctoken()} value="token"></input>
        </Styler>
        <Styler xs={{ gtc: "50px 50px", cg: "5px" }}>
          <input value={this.state.buyLegPrice} onChange={evt => this.setState({ buyLegPrice: parseInt(evt.target.value) })} />
          <input type="button" onClick={() => this.getFinalMargin()} value="buy"></input>
        </Styler>


        <div>{this.state.finalPrice}</div>
      </Styler>

    );
  }
}


class MyComponent extends React.Component<any, any> {
  constructor(props: any) {
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
          {items.map((item: any) => (
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
