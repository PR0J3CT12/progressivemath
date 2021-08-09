import { AUTH } from '../constants/index';

const authReducer = (state = { authData: null }, action) => {
	switch (action.type) {
		case AUTH:
			localStorage.setItem('profile', JSON.stringify({ ...action?.data }));

			setTimeout(() => {
				localStorage.clear()
			}, 60 * 60 * 1000);

			console.log('gay')
			return { ...state, authData: action?.data };
		default:
			return state;
	}
}

export default authReducer;