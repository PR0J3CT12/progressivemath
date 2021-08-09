import { makeStyles } from '@material-ui/core/styles';

export default makeStyles((theme) => ({
	paper: {
		marginTop: theme.spacing(7),
		display: 'flex',
		flexDirection: 'column',
		alignItems: 'center',
		padding: theme.spacing(1.5),
	},
	root: {
		padding: theme.spacing(3),
		paddingTop: "12%"
	},
	avatar: {
		backgroundColor: "#E3CD81FF",
		marginBottom: "6px",
	},
	form: {
		width: '100%',
		marginTop: theme.spacing(1),
	},
	submit: {
		margin: theme.spacing(1, 0, 1),
		marginTop: "20px"
	},
}));