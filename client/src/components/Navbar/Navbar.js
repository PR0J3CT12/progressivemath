import React from 'react';
import useStyles from './styles';
import IconButton from "@material-ui/core/IconButton";
import { Toolbar, Typography, AppBar, InputBase, withStyles } from "@material-ui/core";
import MenuIcon from '@material-ui/icons/Menu';
import SearchIcon from '@material-ui/icons/Search';

const LimeGreenTypography = withStyles({
  root: {
    color: "limegreen"
  }
})(Typography);

const WhiteTextTypography = withStyles({
  root: {
    color: "whitesmoke"
  }
})(Typography);

const Navbar = () => {
  const classes = useStyles();

  return (
    <div>
      <AppBar className={classes.appBar}>
        <Toolbar className={classes.toolbar}>
          <div className={classes.leftSideNav}>
            <IconButton
              edge="start"
              className={classes.menuButton}
              color="inherit"
              aria-label="open drawer"
            >
              <MenuIcon/>
            </IconButton>
            <div className={classes.title}>
              <WhiteTextTypography className={classes.titleText} variant="h6">
                za
              </WhiteTextTypography>
              <LimeGreenTypography className={classes.titleText} variant="h6">
                loo
              </LimeGreenTypography>
              <WhiteTextTypography className={classes.titleText} variant="h6">
                pka Тринки
              </WhiteTextTypography>
            </div>
          </div>
          <div className={classes.search}>
            <div className={classes.searchIcon}>
              <SearchIcon />
            </div>
            <InputBase
              placeholder="Search…"
              classes={{
                root: classes.inputRoot,
                input: classes.inputInput,
              }}
              inputProps={{ 'aria-label': 'search' }}
            />
          </div>
        </Toolbar>
      </AppBar>
    </div>
  );
}

export default Navbar;