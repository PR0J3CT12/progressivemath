import { AUTH } from "../constants";

import * as api from '../api/index';

export const signin = (formData, history) => async (dispatch) => {
	try {
		const { data } = await api.signIn(formData);

		dispatch({ type: AUTH, data });

		history.push(`/student/${data.user_id}`);
	} catch (err) {
		console.log(err);
	}
};
