import {BrowserRouter as Router, Route, Switch, Redirect, useParams} from 'react-router-dom';
import Navbar from './components/Navbar/Navbar';
import Auth from './components/Auth/Auth.js';
import Student from "./components/Student/Student";

function App() {

    return (
        <Router>
          <Navbar />
          <Switch>
            <Route exact path="/auth">
              <Auth />
            </Route>
            <Route exact path="/student/:id">
                <Student />
            </Route>
            <Route exact path="/admin">

            </Route>
            <Redirect to="/auth" />
          </Switch>
        </Router>
  );
}

export default App;