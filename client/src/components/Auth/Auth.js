import React, {useState} from "react";
import { Avatar, Button, Paper, Grid, Container } from "@material-ui/core";
import { useDispatch } from 'react-redux';
import { useHistory } from 'react-router-dom';

import useStyles from './styles';
import LockOutlinedIcon from "@material-ui/icons/LockOutlined";
import Input from "./Input";
import { signin } from '../../actions/auth';

const initialState = {
  login: '',
  password: ''
}

const Auth = () => {
  const classes = useStyles();
  const [formData, setFormData] = useState(initialState);

  const [showPassword, setShowPassword] = useState(false);
  const dispatch = useDispatch();
  const history = useHistory();

  const handleSubmit = (e) => {
    e.preventDefault();

    dispatch(signin(formData, history));
  }

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleShowPassword = () => {
    setShowPassword(!showPassword);
  }

  return (
    <Container className={classes.root} component="main" maxWidth="xs">
      <Paper className={classes.paper} elevation={3}>
        <Avatar className={classes.avatar}>
          <LockOutlinedIcon />
        </Avatar>
        <form className={classes.form} onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Input name="login" label="Логин" handleChange={handleChange} type="login" />
            <Input
              name="password"
              label="Пароль"
              handleChange={handleChange}
              type={showPassword ? "text" : "password"}
              handleShowPassword={handleShowPassword} />
          </Grid>
          <Button type="submit" fullWidth variant="contained" color="primary" className={classes.submit}>
            Вход
          </Button>
        </form>
      </Paper>
    </Container>
  )
}

export default Auth;