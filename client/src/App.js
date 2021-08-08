import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Navbar from './components/Navbar/Navbar';
import Auth from './components/Auth/Auth';
import Footer from './components/Footer/Footer';

function App() {
  return (
    <Router>
      <Navbar />
      <Switch>
        <Route exact path="/auth">
          <Auth />
        </Route>
        <Route exact path="/">
          <Footer />
        </Route>
      </Switch>
    </Router>
  );
}

export default App;